#include "PluginProcessor.h"
#include "PluginEditor.h"

using namespace juce;

namespace wr
{
float filterFromNorm (float n)
{
    const float x = jlimit (0.0f, 1.0f, n) * 40.0f;
    const int i = jmin (39, (int) x);
    return reverbFilterTaper[i] + (reverbFilterTaper[i + 1] - reverbFilterTaper[i]) * (x - (float) i);
}

float filterToNorm (float hz)
{
    int i = 0;
    while (i < 39 && reverbFilterTaper[i + 1] < hz) ++i;
    const float a = reverbFilterTaper[i], b = reverbFilterTaper[i + 1];
    return jlimit (0.0f, 1.0f, ((float) i + (b > a ? (hz - a) / (b - a) : 0.0f)) / 40.0f);
}

AudioProcessorValueTreeState::ParameterLayout createLayout()
{
    AudioProcessorValueTreeState::ParameterLayout layout;
    const auto text = AudioParameterFloatAttributes().withStringFromValueFunction (threeDecimals);
    auto linear = [&] (const char* pid, const char* name, float lo, float hi, float def)
    {
        layout.add (std::make_unique<AudioParameterFloat> (ParameterID { pid, 1 }, name, NormalisableRange<float> (lo, hi), def, text));
    };
    auto stepped = [&] (const char* pid, const char* name, float lo, float hi, float step, float def)
    {
        layout.add (std::make_unique<AudioParameterFloat> (ParameterID { pid, 1 }, name, NormalisableRange<float> (lo, hi, step), def, text));
    };
    auto mix = [&] (const char* pid, const char* name, float def)
    {
        NormalisableRange<float> r (0.0f, 1.0f, [] (float, float, float n) { return mixFromNorm (n); },
                                    [] (float, float, float v) { return mixToNorm (v); });
        layout.add (std::make_unique<AudioParameterFloat> (ParameterID { pid, 1 }, name, r, def, text));
    };
    linear (id::inputGain, "Input Gain", -12.0f, 12.0f, 0.0f);
    linear (id::riderSpeed, "Gain Rider Speed", 0.001f, 0.01f, 0.003f);
    linear (id::riderAmount, "Gain Rider Amount", 0.0f, 1.0f, 0.7f);
    linear (id::riderFloor, "Gain Rider Floor", -50.0f, -18.0f, -30.0f);
    stepped (id::riderOn, "Gain Rider State", 0.0f, 1.0f, 1.0f, 0.0f);
    stepped (id::compression, "Compression", -50.0f, 50.0f, 1.0f, 0.0f);
    stepped (id::focus, "Focus", -50.0f, 50.0f, 1.0f, 0.0f);
    stepped (id::characterOn, "Character State", 0.0f, 1.0f, 1.0f, 0.0f);
    linear (id::eqLow, "EQ Low Gain", -12.0f, 12.0f, 0.0f);
    linear (id::eqHigh, "EQ High Gain", -12.0f, 12.0f, 0.0f);
    stepped (id::eqOn, "EQ State", 0.0f, 1.0f, 1.0f, 0.0f);
    linear (id::doublerStereo, "Doubler Stereo", 0.0f, 1.0f, 0.5f);
    mix (id::doublerMix, "Doubler Mix", 0.1f);
    stepped (id::doublerOn, "Doubler State", 0.0f, 1.0f, 1.0f, 0.0f);
    {
        NormalisableRange<float> r (2000.0f, 20000.0f, [] (float, float, float n) { return filterFromNorm (n); },
                                    [] (float, float, float v) { return filterToNorm (v); });
        layout.add (std::make_unique<AudioParameterFloat> (ParameterID { id::reverbFilter, 1 }, "Reverb Filter", r, 20000.0f, text));
    }
    mix (id::reverbMix, "Reverb Mix", 0.1f);
    stepped (id::reverbOn, "Reverb State", 0.0f, 1.0f, 1.0f, 0.0f);
    linear (id::outputGain, "Output Gain", -12.0f, 12.0f, 0.0f);
    layout.add (std::make_unique<AudioParameterBool> (ParameterID { id::bypass, 1 }, "Bypass", false));
    layout.add (std::make_unique<AudioParameterChoice> (ParameterID { id::reverbType, 1 }, "Reverb Type", StringArray { "room", "plate" }, 0));
    return layout;
}
}

WraithProcessor::WraithProcessor()
    : AudioProcessor (BusesProperties()
                          .withInput ("Input", AudioChannelSet::stereo(), true)
                          .withOutput ("Output", AudioChannelSet::stereo(), true)
                          .withInput ("Sidechain", AudioChannelSet::stereo(), false)),
      apvts (*this, nullptr, "Wraith", wr::createLayout())
{
    bypassParam = apvts.getParameter (wr::id::bypass);
    for (int i = 0; i < wr::numParams; ++i) raw[i] = apvts.getRawParameterValue (wr::allIds[i]);
    for (auto& e : presets.list())               // the reference opens with its factory preset "lead"
        if (e.factory && e.name == "lead") presets.load (e);
    slots[0] = slots[1] = captureSlot();
}

bool WraithProcessor::isBusesLayoutSupported (const BusesLayout& l) const
{
    // as the reference (ParamDump): stereo in, stereo out only; the side-chain bus (ours) is stereo or off
    if (l.getMainInputChannelSet() != AudioChannelSet::stereo() || l.getMainOutputChannelSet() != AudioChannelSet::stereo())
        return false;
    if (l.inputBuses.size() > 1)
    {
        const auto side = l.inputBuses[1];
        if (! side.isDisabled() && side != AudioChannelSet::stereo()) return false;
    }
    return true;
}

void WraithProcessor::prepareToPlay (double sampleRate, int block)
{
    preparedRate = sampleRate;
    preparedBlock = block;
    engine.prepare (sampleRate, block, wr::dsp::tuning());
    setLatencySamples (engine.latency());
}

void WraithProcessor::measure (const AudioBuffer<float>& b, wr::LevelTap& l, wr::LevelTap& r)
{
    const int n = b.getNumSamples();
    l.push (b.getMagnitude (0, 0, n));
    r.push (b.getMagnitude (jmin (1, b.getNumChannels() - 1), 0, n));
}

void WraithProcessor::processBlock (AudioBuffer<float>& buffer, MidiBuffer&)
{
    ScopedNoDenormals noDenormals;
    if (auto* head = getPlayHead())
        if (const auto position = head->getPosition())
            if (const auto bpm = position->getBpm()) hostBpm = (float) *bpm;
    auto main = getBusBuffer (buffer, true, 0);
    const int n = main.getNumSamples();
    if (main.getNumChannels() < 2) return;

    auto v = [this] (wr::Index i) { return raw[i]->load(); };
    auto on = [&] (wr::Index i) { return v (i) >= 0.5f; };
    wr::dsp::Params p;
    p.inputGainDb = v (wr::iInputGain);
    p.riderOn = on (wr::iRiderOn); p.riderSpeed = v (wr::iRiderSpeed); p.riderAmount = v (wr::iRiderAmount); p.riderFloorDb = v (wr::iRiderFloor);
    p.characterOn = on (wr::iCharacterOn); p.compression = v (wr::iCompression); p.focus = v (wr::iFocus);
    p.eqOn = on (wr::iEqOn); p.eqLowDb = v (wr::iEqLow); p.eqHighDb = v (wr::iEqHigh);
    p.doublerOn = on (wr::iDoublerOn); p.doublerStereo = v (wr::iDoublerStereo); p.doublerMix = v (wr::iDoublerMix);
    p.reverbOn = on (wr::iReverbOn); p.reverbFilterHz = v (wr::iReverbFilter); p.reverbMix = v (wr::iReverbMix);
    p.reverbType = (int) v (wr::iReverbType);
    p.outputGainDb = ioLink.load() ? -p.inputGainDb : v (wr::iOutputGain);      // the I/O link: output = -input, always
    p.bypass = bypassParam->getValue() >= 0.5f;

    measure (main, inL, inR);
    // EXT: the character section listens to the side-chain bus, when the host has it connected
    const float* key[2] { nullptr, nullptr };
    if (sidechainExternal.load() && getBusCount (true) > 1 && getBus (true, 1)->isEnabled())
    {
        auto side = getBusBuffer (buffer, true, 1);
        if (side.getNumChannels() >= 2) { key[0] = side.getReadPointer (0); key[1] = side.getReadPointer (1); }
    }
    {
        // editor hook: the mean square of what the character section hears (the key when EXT, else the input; the
        // channels averaged), for the display's compression bars. Reads only.
        const float* d0 = key[0] != nullptr ? key[0] : main.getReadPointer (0);
        const float* d1 = key[1] != nullptr ? key[1] : main.getReadPointer (1);
        double sq = 0.0;
        for (int i = 0; i < n; ++i) sq += 0.5 * ((double) d0[i] * d0[i] + (double) d1[i] * d1[i]);
        detectorIn.push (sq, n);
    }
    engine.process (main.getWritePointer (0), main.getWritePointer (1), n, p, key[0], key[1]);
    measure (main, outL, outR);
    ++blocksProcessed;
}

void WraithProcessor::getStateInformation (MemoryBlock& dest)
{
    auto state = apvts.copyState();
    state.setProperty ("uiScale", uiScale.load(), nullptr);
    state.setProperty ("preset", presets.currentName(), nullptr);
    state.setProperty ("compare", slot, nullptr);
    state.setProperty ("ioLink", ioLink.load() ? 1 : 0, nullptr);
    state.setProperty ("sidechain", sidechainExternal.load() ? 1 : 0, nullptr);
    // the inactive compare slot (the active one is the parameters themselves), if it was ever used
    state.removeChild (state.getChildWithName ("SLOT"), nullptr);
    if (slotUsed[1 - slot]) state.appendChild (slots[1 - slot].createCopy(), nullptr);
    if (auto xml = state.createXml()) copyXmlToBinary (*xml, dest);
}

void WraithProcessor::setStateInformation (const void* data, int size)
{
    if (auto xml = getXmlFromBinary (data, size))
        if (xml->hasTagName (apvts.state.getType()))
        {
            auto tree = ValueTree::fromXml (*xml);
            uiScale = (float) tree.getProperty ("uiScale", 1.0f);
            presets.setCurrentName (tree.getProperty ("preset", "lead").toString());
            slot = jlimit (0, 1, (int) tree.getProperty ("compare", 0));
            ioLink = (int) tree.getProperty ("ioLink", 0) != 0;
            sidechainExternal = (int) tree.getProperty ("sidechain", 0) != 0;
            auto other = tree.getChildWithName ("SLOT");
            tree.removeChild (other, nullptr);
            apvts.replaceState (tree);
            slots[slot] = captureSlot();
            slotUsed[slot] = true;
            slotUsed[1 - slot] = other.isValid();
            slots[1 - slot] = other.isValid() ? other.createCopy() : slots[slot].createCopy();
        }
}

ValueTree WraithProcessor::captureSlot() const
{
    ValueTree t ("SLOT");
    for (auto* pid : wr::presetIds)
        if (auto* p = apvts.getParameter (pid)) t.setProperty (pid, p->getValue(), nullptr);
    t.setProperty ("preset", presets.currentName(), nullptr);
    return t;
}

void WraithProcessor::applySlot (const ValueTree& t)
{
    for (auto* pid : wr::presetIds)
        if (auto* p = apvts.getParameter (pid))
            if (t.hasProperty (pid))
            {
                p->beginChangeGesture();
                p->setValueNotifyingHost ((float) t.getProperty (pid));
                p->endChangeGesture();
            }
    presets.setCurrentName (t.getProperty ("preset", presets.currentName()).toString());
}

void WraithProcessor::selectCompareSlot (int s)
{
    s = jlimit (0, 1, s);
    if (s == slot) return;
    slots[slot] = captureSlot();
    if (! slotUsed[s]) slots[s] = slots[slot].createCopy();
    slotUsed[s] = true;
    slot = s;
    applySlot (slots[slot]);
}

void WraithProcessor::copyCompareSlot()
{
    slots[slot] = captureSlot();
    slots[1 - slot] = slots[slot].createCopy();
    slotUsed[1 - slot] = true;
}

AudioProcessorEditor* WraithProcessor::createEditor() { return new WraithEditor (*this); }

AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new WraithProcessor(); }
