#include "PluginEditor.h"
#include "Settings.h"
#include "ui/KnobShadow.h"

using namespace juce;
namespace theme = po::theme;
#ifndef SUITE_REPOSITORY
 #define SUITE_REPOSITORY "https://github.com/MaymiPR/Orrery"
#endif
static const juce::String repository = SUITE_REPOSITORY;     // the Orrery Suite repository (CMakeLists.txt)

namespace
{
constexpr float columnX[] { 89.0f, 176.0f, 559.0f, 711.0f, 798.0f };
constexpr float panelTop = 31.75f, panelBottom = 263.75f;
constexpr float ledX[2][2] { { 25.0f, 61.0f }, { 821.0f, 857.0f } };   // input L R, output L R (the ladders' left edges)

// the plate's decoration (ours, where the original has its grille): an orrery seen at a slant, four orbits round the
// suite's mark, a planet on each, and a few faint stars; all in the plate's own violet-black, centred on the lettering
constexpr float orreryX = 367.75f, orreryY = 309.0f;
constexpr float orbitRx[] { 50.0f, 90.0f, 135.0f, 180.0f };
constexpr float orbitTilt = 0.2f;                                   // ry / rx
constexpr float planetAngle[] { 2.2f, 5.4f, 0.75f, 3.75f };         // radians, round each orbit from the right

// the Orrery Suite mark (as the top bar's logo, po::Logo) at any size: an orbit, its lower arc lit as a crescent, the
// sun and a planet nearer in; ro is the orbit's radius (7.2 on the top bar)
void drawMark (Graphics& g, Point<float> c, float ro, Colour orbit, Colour lit)
{
    const float k = ro / 7.2f;
    g.setColour (orbit);
    g.drawEllipse (Rectangle<float> (2 * ro, 2 * ro).withCentre (c), jmax (0.6f, k));
    Path crescent;
    for (int i = 0; i <= 24; ++i)
    {
        const float a = MathConstants<float>::pi * (0.7f + 0.6f * (float) i / 24.0f);
        const Point<float> p (c.x - (ro + 0.5f * k) * std::sin (a), c.y - (ro + 0.5f * k) * std::cos (a));
        if (i == 0) crescent.startNewSubPath (p); else crescent.lineTo (p);
    }
    for (int i = 24; i >= 0; --i)
    {
        const float a = MathConstants<float>::pi * (0.7f + 0.6f * (float) i / 24.0f);
        crescent.lineTo (c.x - (ro + 0.5f * k) * std::sin (a), c.y - 1.2f * k - (ro - 1.6f * k) * std::cos (a));
    }
    crescent.closeSubPath();
    g.setColour (lit);
    g.fillPath (crescent);
    g.fillEllipse (Rectangle<float> (5.2f * k, 5.2f * k).withCentre (c + Point<float> (0.0f, -0.6f * k)));
    g.fillEllipse (Rectangle<float> (2.4f * k, 2.4f * k).withCentre (c + Point<float> (3.4f * k, -3.6f * k)));
}

// the meters keep the original's LED scales as bars: a bar is lit in whole cells (one per LED, same pitch), so it
// moves at the same thresholds the LEDs did
int topLed (float db)                         // the highest LED over its threshold (strictly), -1 for none
{
    int top = -1;
    for (int k = 0; k < theme::numLeds; ++k) if (db > theme::ledThresholdDb (k)) top = k;
    return top;
}

// draws a meter bar filling from the far end: right to left (horizontal) or top down (vertical), mirrored about its
// centre so the well, the gradient and the peak marker all run the other way
void drawMeterBarReversed (Graphics& g, Rectangle<float> r, float fraction, bool vertical, float peak = -1.0f)
{
    Graphics::ScopedSaveState ss (g);
    const auto c = r.getCentre();
    g.addTransform (vertical ? AffineTransform::scale (1.0f, -1.0f, c.x, c.y) : AffineTransform::scale (-1.0f, 1.0f, c.x, c.y));
    theme::drawMeterBar (g, r, fraction, vertical, peak);
}

String grText (float gr)
{
    const float v = -gr;
    return String (std::abs (v) < 0.05f ? 0.0f : v, 1);
}

// the cells over which a knob's caption shows its value (hovered on the reference): the knob's column, 87 px wide
// centred on the knob; on the plate its full height, for the EQ knobs 20.5 px above the knob centre to 45 below
Rectangle<float> plateCell (float cx) { return { cx - 43.5f, 266.5f, 87.0f, 92.25f }; }
Rectangle<float> eqCell (float cy) { return { 133.375f - 43.5f, cy - 20.5f, 87.0f, 65.5f }; }

String dbText (float db)
{
    if (db < -96.0f) return "-inf";         // the reference shows -96.0 and, one step lower, -inf
    return String (db, 1);
}

float toDb (float lin) { return lin > 1.0e-6f ? Decibels::gainToDecibels (lin) : -200.0f; }
}

PositronEditor::PositronEditor (PositronProcessor& p) : AudioProcessorEditor (p), proc (p)
{
    po::noFocus (*this);
    po::noFocus (content);
    setOpaque (true);
    addAndMakeVisible (content);
    content.setBounds (0, 0, (int) std::ceil (designW), (int) std::ceil (designH));

    for (auto* c : std::initializer_list<Component*> { &logo, &presetBox, &prevButton, &nextButton, &saveButton, &sidechain, &scaleBox, &gear,
                                                       &visualizer, &amountText, &eqPower, &eqHigh, &eqMid, &eqLow, &amount, &amountPower, &limiterPower,
                                                       &inputKnob, &limiterKnob, &outputKnob, &ioLinkButton })
        content.addAndMakeVisible (*c);
    content.addMouseListener (&hoverTracker, true);

    logo.setBounds (6, 7, 17, 17);
    presetBox.setBounds (176, 3, 193, 25);
    prevButton.setBounds (375, 3, 24, 25);
    nextButton.setBounds (405, 3, 24, 25);
    saveButton.setBounds (439, 3, 24, 25);
    sidechain.setBounds (560, 3, 85, 25);
    scaleBox.setBounds (794, 3, 66, 25);
    gear.setBounds (866, 7, 16, 17);
    visualizer.setBounds (177, 33, 382, 230);
    amountText.setBounds (360, 100, 140, 64);
    amountText.setInterceptsMouseClicks (false, false);
    amountText.paintFn = [this] (Graphics& g) { g.addTransform (AffineTransform::translation (-360.0f, -100.0f)); paintAmountText (g); };

    auto knobAt = [] (Component& k, float cx, float cy, float r) { k.setBounds (Rectangle<float> (2 * r, 2 * r).withCentre ({ cx, cy }).getSmallestIntegerContainer()); };
    // fractional centres: the knobs are placed with a transform so they land on the measured centres
    auto place = [] (Component& k, float cx, float cy, float r)
    {
        const int s = (int) std::ceil (2.0f * r);
        k.setBounds (0, 0, s, s);
        k.setTransform (AffineTransform::scale (2.0f * r / (float) s).translated (cx - r, cy - r));
    };
    ignoreUnused (knobAt);
    place (eqHigh, 133.375f, 90.75f, 20.375f);
    place (eqMid, 133.375f, 155.75f, 20.375f);
    place (eqLow, 133.375f, 220.75f, 20.375f);
    place (amount, 292.875f, 148.25f, 50.875f);
    place (inputKnob, 45.755f, 313.11f, 25.06f);
    place (limiterKnob, 754.745f, 313.11f, 25.06f);
    place (outputKnob, 841.74f, 313.11f, 25.06f);
    for (auto* k : { &eqHigh, &eqMid, &eqLow, &inputKnob, &outputKnob })     // bipolar: the value's arc starts at 0 dB
        k->setArcOrigin (0.5f);
    ioLinkButton.setBounds (664, 3, 64, 25);      // centred between the side-chain switch (ends 645) and "UI Scale" (747.5)
    // A / B (ours, Orion's switch and behaviour): in the free space between the logo and "Preset" (no caption: no room)
    content.addAndMakeVisible (compare);
    compare.setBounds (52, 3, 74, 25);
    content.addChildComponent (toast);                // over everything else (shown by the switch's arrow)
    toast.setBounds (344, 292, 200, 61);
    eqPower.setBounds (97, 40, 72, 25);
    amountPower.setBounds (364, 167, 72, 25);
    limiterPower.setBounds (719, 40, 72, 25);

    auto& s = proc.apvts;
    auto attach = [&] (po::MetalKnob& sl, const char* pid)
    {
        attachments.push_back (std::make_unique<AudioProcessorValueTreeState::SliderAttachment> (s, pid, sl));
        if (auto* prm = dynamic_cast<RangedAudioParameter*> (s.getParameter (pid)))
        {
            sl.setDefaultValue (prm->convertFrom0to1 (prm->getDefaultValue()));
            sl.onGesture = [prm] (bool begin) { if (begin) prm->beginChangeGesture(); else prm->endChangeGesture(); };
        }
    };
    attach (eqHigh, po::id::eqHigh);
    attach (eqMid, po::id::eqMid);
    attach (eqLow, po::id::eqLow);
    attach (amount, po::id::character);
    attach (inputKnob, po::id::inputGain);
    attach (limiterKnob, po::id::limiterGain);
    attach (outputKnob, po::id::outputGain);

    for (auto* k : { &inputKnob, &outputKnob })
    {
        k->onDragStart = [this, k] { beginLink (*k); };
        k->onValueChange = [this, k] { if (linkSource == k) mirror (k == &inputKnob); };
        k->onDragEnd = [this, k] { endLink (*k); };
    }
    ioLinkButton.active = proc.ioLink.load();
    ioLinkButton.onClick = [this]
    {
        proc.ioLink = ! proc.ioLink.load();
        ioLinkButton.active = proc.ioLink.load();
        ioLinkButton.repaint();
        if (proc.ioLink.load())                    // linking snaps the output to the input's opposite
            if (auto* prm = proc.apvts.getParameter (po::id::outputGain))
            {
                prm->beginChangeGesture();
                mirror (true);
                prm->endChangeGesture();
            }
    };

    auto toggleParam = [&s] (const char* pid)
    {
        if (auto* prm = s.getParameter (pid))
        {
            prm->beginChangeGesture();
            prm->setValueNotifyingHost (prm->getValue() >= 0.5f ? 0.0f : 1.0f);
            prm->endChangeGesture();
        }
    };
    eqPower.onClick = [toggleParam] { toggleParam (po::id::eqBypass); };
    amountPower.onClick = [toggleParam] { toggleParam (po::id::characterBypass); };
    limiterPower.onClick = [toggleParam] { toggleParam (po::id::limiterBypass); };
    for (auto* pid : { po::id::eqBypass, po::id::characterBypass, po::id::limiterBypass, po::id::character, po::id::inputGain, po::id::outputGain })
        s.addParameterListener (pid, this);

    sidechain.external = proc.sidechainExternal.load();
    sidechain.onChange = [this] (bool ext) { proc.sidechainExternal = ext; };
    presetBox.onClick = [this] { if (dropList != nullptr) closePopups(); else showPresetList(); };
    scaleBox.onClick = [this] { if (dropList != nullptr) closePopups(); else showScaleList(); };
    prevButton.onClick = [this] { proc.presets.step (-1); presetBox.text = proc.presets.currentName(); presetBox.repaint(); };
    nextButton.onClick = [this] { proc.presets.step (1); presetBox.text = proc.presets.currentName(); presetBox.repaint(); };
    saveButton.onClick = [this] { showSavePreset(); };
    gear.onClick = [this] { showSettings(); };
    logo.onClick = [this] { showAboutMenu(); };
    presetBox.text = proc.presets.currentName();
    compare.slot = proc.compareSlot();
    compare.onSelect = [this] (int slot)
    {
        proc.selectCompareSlot (slot);
        compare.slot = proc.compareSlot();
        presetBox.text = proc.presets.currentName();
        compare.repaint(); presetBox.repaint();
        updateFromParams();
    };
    compare.onCopy = [this]
    {
        proc.copyCompareSlot();
        toast.show (proc.compareSlot() == 0 ? "A copied to B." : "B copied to A.");
    };

    po::Settings::get().addChangeListener (this);
    updateFromParams();
    constrainer.setFixedAspectRatio (designW / designH);
    constrainer.setSizeLimits ((int) (designW * scales[0]), (int) (designH * scales[0]),
                               (int) (designW * scales[std::size (scales) - 1]), (int) (designH * scales[std::size (scales) - 1]));
    setResizable (true, false);          // hosts may resize the window too; the corner below is our own
    setConstrainer (&constrainer);
    grip = std::make_unique<Grip> (this, &constrainer);
    po::noFocus (*grip);
    addAndMakeVisible (*grip);
    grip->setAlwaysOnTop (true);
    setUiScale (proc.uiScale.load());
    startTimerHz (30);
    readoutClock.startTimer (46);
}

PositronEditor::~PositronEditor()
{
    readoutClock.stopTimer();
    content.removeMouseListener (&hoverTracker);
    po::Settings::get().removeChangeListener (this);
    for (auto* pid : { po::id::eqBypass, po::id::characterBypass, po::id::limiterBypass, po::id::character, po::id::inputGain, po::id::outputGain })
        proc.apvts.removeParameterListener (pid, this);
}

void PositronEditor::setUiScale (float s)
{
    scale = s;
    proc.uiScale = s;
    scaleBox.text = String (roundToInt (s * 100.0f)) + "%";
    content.setTransform (AffineTransform::scale (s));
    setSize ((int) (designW * s), (int) (designH * s));      // truncated, as the reference (359 px at 100 %)
}

// a new size (the corner, the host, or setUiScale) sets the scale; sizes from setUiScale itself keep their exact scale
// (they are truncated to whole pixels)
void PositronEditor::resized()
{
    if (std::abs (getWidth() - (int) (designW * scale)) > 1)
    {
        scale = jlimit (scales[0], scales[std::size (scales) - 1], (float) getWidth() / designW);
        proc.uiScale = scale;
        scaleBox.text = String (roundToInt (scale * 100.0f)) + "%";
        scaleBox.repaint();
        content.setTransform (AffineTransform::scale (scale));
        getProperties().set ("liveResize", true);        // stretch the cached images until the size settles (timer)
        lastResizeMs = Time::getMillisecondCounter();
    }
    if (grip != nullptr)
    {
        const int g = roundToInt (18.0f * scale);
        grip->setBounds (getWidth() - g, getHeight() - g, g, g);
    }
}

// three grooves cut into the plate's corner, faint lettering (gold under the mouse), each with a dark cut beside it
// so they read as engraved
void PositronEditor::Grip::paint (Graphics& g)
{
    const float w = (float) getWidth(), u = w / 18.0f;
    const auto light = isMouseOverOrDragging() ? theme::gold : theme::letteringFaint;
    for (int i = 1; i <= 3; ++i)
    {
        const float d = (float) i * 4.6f * u;
        g.setColour (Colours::black.withAlpha (0.7f));
        g.drawLine (w - d - 0.9f * u, w - 2.4f * u, w - 2.4f * u, w - d - 0.9f * u, 1.3f * u);
        g.setColour (light);
        g.drawLine (w - d, w - 2.4f * u, w - 2.4f * u, w - d, 1.3f * u);
    }
}

void PositronEditor::Grip::mouseUp (const MouseEvent& e)
{
    ResizableCornerComponent::mouseUp (e);
    if (auto* ed = findParentComponentOfClass<PositronEditor>()) ed->endLiveResize();   // render sharp at once
}

void PositronEditor::endLiveResize()
{
    if (! getProperties().getWithDefault ("liveResize", false)) return;
    getProperties().set ("liveResize", false);
    content.repaint();
}

void PositronEditor::parameterChanged (const String& id, float)
{
    const bool gain = id == po::id::inputGain || id == po::id::outputGain, fromInput = id == po::id::inputGain;
    MessageManager::callAsync ([safe = Component::SafePointer<PositronEditor> (this), gain, fromInput]
    {
        if (safe == nullptr) return;
        if (! gain) safe->updateFromParams();
        else if (safe->linkSource == nullptr) safe->mirror (fromInput);    // automation, presets: keep the link
    });
}

void PositronEditor::updateFromParams()
{
    auto v = [this] (const char* pid) { return proc.apvts.getRawParameterValue (pid)->load(); };
    eqOn = v (po::id::eqBypass) < 0.5f;
    characterOn = v (po::id::characterBypass) < 0.5f;
    limiterOn = v (po::id::limiterBypass) < 0.5f;
    characterValue = v (po::id::character);
    eqPower.active = eqOn;
    amountPower.active = characterOn;
    limiterPower.active = limiterOn;
    eqPower.repaint(); amountPower.repaint(); limiterPower.repaint();
    content.repaint();
}

void PositronEditor::changeListenerCallback (ChangeBroadcaster*) { content.repaint(); }

void PositronEditor::updateReadout (const MouseEvent& e, bool released)
{
    const auto p = e.getEventRelativeTo (&content).position;
    const po::MetalKnob* t = nullptr;
    const po::MetalKnob* knobs[] { &inputKnob, &limiterKnob, &outputKnob, &eqHigh, &eqMid, &eqLow };
    if (! released)
        for (auto* k : knobs)
            if (k->isMouseButtonDown()) t = k;          // a drag keeps its readout wherever the mouse goes
    const bool inside = content.getLocalBounds().toFloat().contains (p) && dialog == nullptr && dropList == nullptr
                        && ! (e.eventComponent == &content && ! content.isMouseOver (true));
    if (t == nullptr && inside)
    {
        const std::pair<const po::MetalKnob*, Rectangle<float>> cells[] {
            { &inputKnob, plateCell (45.755f) }, { &limiterKnob, plateCell (754.745f) }, { &outputKnob, plateCell (841.74f) },
            { &eqHigh, eqCell (90.75f) }, { &eqMid, eqCell (155.75f) }, { &eqLow, eqCell (220.75f) } };
        for (auto& [k, r] : cells)
            if (r.contains (p)) t = k;
    }
    if (t != readoutKnob) { readoutKnob = t; content.repaint(); }
}

String PositronEditor::captionText (const po::MetalKnob& k, const char* name) const
{
    const bool linkedPartner = linkSource != nullptr && linkSource != &k && (&k == &inputKnob || &k == &outputKnob);
    if (&k == readoutKnob || linkedPartner) return String::formatted ("%.1f dB", k.getValue());
    return name;
}

void PositronEditor::beginLink (po::MetalKnob& src)
{
    if (! proc.ioLink.load() || linkSource != nullptr) return;
    if (auto* prm = proc.apvts.getParameter (&src == &inputKnob ? po::id::outputGain : po::id::inputGain))
    {
        linkSource = &src;
        prm->beginChangeGesture();
        mirror (&src == &inputKnob);
    }
}

void PositronEditor::mirror (bool fromInput)
{
    if (! proc.ioLink.load() || mirroring) return;
    const ScopedValueSetter<bool> guard (mirroring, true);
    const auto* srcId = fromInput ? po::id::inputGain : po::id::outputGain;
    const auto* dstId = fromInput ? po::id::outputGain : po::id::inputGain;
    if (auto* dst = dynamic_cast<RangedAudioParameter*> (proc.apvts.getParameter (dstId)))
    {
        const float target = dst->getNormalisableRange().snapToLegalValue (-proc.apvts.getRawParameterValue (srcId)->load());
        if (std::abs (proc.apvts.getRawParameterValue (dstId)->load() - target) > 1.0e-5f)
            dst->setValueNotifyingHost (dst->convertTo0to1 (target));
    }
    content.repaint();
}

void PositronEditor::endLink (po::MetalKnob& src)
{
    if (linkSource != &src) return;
    if (auto* prm = proc.apvts.getParameter (&src == &inputKnob ? po::id::outputGain : po::id::inputGain))
        prm->endChangeGesture();
    linkSource = nullptr;
    content.repaint();
}

void PositronEditor::updateMeter (Meter& m, po::LevelTap& tap)
{
    m.rawPeakDb = toDb (tap.takePeak());
    m.barDb = toDb (tap.bar.load());
    m.fastDb = toDb (tap.takeFast());
}

// The I/O readouts as the reference updates them (MEASUREMENTS.md 6), measured with RefCapture films read frame by
// frame (nulltest/read_readouts.py):
// - peak: every 46 ms it takes the latest block's sample peak and holds the highest (until clicked); peaks in the
//   blocks in between are not seen, so a short spike reads lower than the sample peak (music with +2.1 dBFS overs
//   reads +0.9)
// - RMS: live, every fifth time (231 ms): the plain RMS (one-pole on x^2, 89 ms) + 1.5 dB; in silence it falls the
//   same 11.27 dB per update (also when the host stops calling the plug-in), and below -96 dB it reads -inf
// - LUFS mode (the settings page): the same box shows the short-term loudness of both channels (BS.1770, 3 s), every
//   third RMS update (693 ms); when the host stops calling the plug-in its window empties over 3 s
void PositronEditor::sampleReadouts()
{
    if (frozen) return;
    Meter* meters[4] { &inMeter[0], &inMeter[1], &outMeter[0], &outMeter[1] };
    po::LevelTap* taps[4] { &proc.inL, &proc.inR, &proc.outL, &proc.outR };
    for (int i = 0; i < 4; ++i)
        meters[i]->peakHoldDb = jmax (meters[i]->peakHoldDb, toDb (taps[i]->blockPeak.load()));
    if (++readoutTicks < 5) return;
    readoutTicks = 0;
    const int blocks = proc.blocksProcessed.load();
    const bool running = blocks != readoutBlocks;
    readoutBlocks = blocks;
    constexpr float silenceStep = 0.0747f;          // 10^(-11.27 / 10): 231 ms of the 89 ms one-pole
    for (int i = 0; i < 4; ++i)
    {
        auto& m = *meters[i];
        m.rmsMeanSquare = running ? taps[i]->meanSquare.load() : m.rmsMeanSquare * silenceStep;
        m.rmsDb = m.rmsMeanSquare > 1.0e-20f ? 10.0f * std::log10 (m.rmsMeanSquare) + 1.5f : -200.0f;
    }
    if (++loudnessTicks < 3) return;
    loudnessTicks = 0;
    for (int i = 0; i < 4; ++i)
    {
        auto& m = *meters[i];
        if (running) m.lufsMeanSquare = m.lufsStopMeanSquare = taps[i]->loudness.load();
        else m.lufsMeanSquare = jmax (0.0f, m.lufsMeanSquare - m.lufsStopMeanSquare * (0.693f / 3.0f));
        m.lufsDb = m.lufsMeanSquare > 1.0e-20f ? 10.0f * std::log10 (m.lufsMeanSquare) - 0.691f : -200.0f;
    }
}

void PositronEditor::timerCallback()
{
    // a resize has settled (no new size for 150 ms): render the per-scale images sharp at the final size
    if (getProperties().getWithDefault ("liveResize", false) && Time::getMillisecondCounter() - lastResizeMs > 150) endLiveResize();
    if (frozen) return;
    updateMeter (inMeter[0], proc.inL);
    updateMeter (inMeter[1], proc.inR);
    updateMeter (outMeter[0], proc.outL);
    updateMeter (outMeter[1], proc.outR);
    for (int b = 0; b < 3; ++b) { bandGrDb[b] = proc.bandGr[b].exchange (0.0f); bandGrHold[b] = jmax (bandGrHold[b], bandGrDb[b]); }
    for (int c = 0; c < 2; ++c) { limGrDb[c] = proc.limGr[c].exchange (0.0f); limGrHold[c] = jmax (limGrHold[c], limGrDb[c]); }
    const int blocks = proc.blocksProcessed.load();
    const bool running = blocks != lastBlocks;
    lastBlocks = blocks;
    // the visualiser follows this frame's input sample peak (not the meters: they fall slowly); no blocks = silence
    const float inPeak = running ? jmax (inMeter[0].rawPeakDb, inMeter[1].rawPeakDb) : -200.0f;
    const float mix = characterOn ? jlimit (0.0f, 1.0f, characterValue / 0.5f) : 0.0f;
    visualizer.setTempo (proc.hostBpm.load());
    visualizer.setPlaying (running && proc.hostPlaying.load() != 0);
    visualizer.advance (inPeak, mix, po::Settings::get().animation(), po::Settings::get().particleStyle() == po::Settings::Particles::positron);
    content.repaint();
    amountText.repaint();
}

void PositronEditor::setTestLevels (float inDb, float outDb, bool audio)
{
    frozen = true;
    for (auto& m : inMeter) { m.barDb = inDb - 3.0f; m.fastDb = inDb; m.peakHoldDb = inDb; m.rmsDb = inDb - 1.5f; }
    for (auto& m : outMeter) { m.barDb = outDb - 3.0f; m.fastDb = outDb; m.peakHoldDb = outDb; m.rmsDb = outDb - 1.5f; }    if (audio) visualizer.advance (0.0f, characterOn ? jlimit (0.0f, 1.0f, characterValue / 0.5f) : 0.0f, true,
                                   po::Settings::get().particleStyle() == po::Settings::Particles::positron);
    content.repaint();
}

//==============================================================================
void PositronEditor::Content::paint (Graphics& g)
{
    g.fillAll (Colours::black);
    ed.paintTopBar (g);
    ed.paintPanel (g);
    ed.paintPlate (g);
}

void PositronEditor::Content::mouseDown (const MouseEvent& e)
{
    // clicking a readout resets the held readouts of that meter (the RMS readout is live)
    const auto p = e.position;
    if (p.y > 40.0f && p.y < 84.0f)
    {
        if (p.x < columnX[0]) for (auto& m : ed.inMeter) m.peakHoldDb = -200.0f;
        if (p.x > columnX[4]) for (auto& m : ed.outMeter) m.peakHoldDb = -200.0f;
        if (p.x > columnX[3] && p.x < columnX[4]) for (auto& v : ed.limGrHold) v = 0.0f;
        repaint();
    }
    // the band readouts (beside the GR meters)
    if (p.x > columnX[2] + 80.0f && p.x < columnX[3] && p.y > 110.0f && p.y < 262.0f)
    {
        for (auto& v : ed.bandGrHold) v = 0.0f;
        repaint();
    }
    if (ed.dropList != nullptr) ed.closePopups();
}

void PositronEditor::paintTopBar (Graphics& g)
{
    g.setColour (theme::topBar);
    g.fillRect (0.0f, 0.0f, designW, 30.5f);
    g.setColour (theme::text);
    g.setFont (theme::font (12.0f));
    theme::textAt (g, "Preset", 136.0f, 19.5f);
    theme::textAt (g, "Sidechain", 500.5f, 19.5f);
    theme::textAt (g, "UI Scale", 747.5f, 19.5f);
}

void PositronEditor::paintPanel (Graphics& g)
{
    // the panel: a card (the visualiser's black glass fills the middle column), its outline and the column dividers
    const Rectangle<float> panel (1.5f, panelTop, designW - 3.0f, panelBottom - panelTop);
    g.setColour (theme::card);
    g.fillRoundedRectangle (panel, 15.0f);
    g.setColour (theme::outline);
    g.drawRoundedRectangle (panel, 15.0f, 2.2f);
    g.setColour (theme::divider);
    for (float x : columnX) g.fillRect (x, 36.0f, 1.0f, 224.5f);

    paintIoMeter (g, 0.0f, inMeter, true);
    paintIoMeter (g, 796.0f, outMeter, false);

    // EQ labels: a knob's name, or its value while hovered
    g.setFont (theme::font (11.25f));
    const float baselines[3] { 125.5f, 190.5f, 255.5f };
    const char* names[3] { "high", "mid", "low" };
    const po::MetalKnob* eqKnobs[3] { &eqHigh, &eqMid, &eqLow };
    for (int i = 0; i < 3; ++i)
    {
        const auto t = captionText (*eqKnobs[i], names[i]);
        g.setColour (! eqOn ? theme::letteringFaint : t == names[i] ? theme::letteringDim : theme::gold);
        g.drawText (t, Rectangle<float> (83.0f, baselines[i] - 12.0f, 101.5f, 16.0f), Justification::centredTop, false);
    }

    paintGainReduction (g);
    paintLimiter (g);
}

void PositronEditor::paintIoMeter (Graphics& g, float x0, const Meter (&m)[2], bool target)
{
    const float centres[2] { x0 + 28.75f, x0 + 65.25f };
    g.setFont (theme::font (12.0f));
    for (int c = 0; c < 2; ++c)
    {
        g.setColour (m[c].peakHoldDb > 0.0f ? theme::clip : theme::lettering);
        g.drawText (dbText (m[c].peakHoldDb), Rectangle<float> (centres[c] - 20.0f, 44.5f, 40.0f, 16.0f), Justification::centredTop, false);
        g.setColour (theme::gold);
        const bool lufs = po::Settings::get().meterMode() == po::Settings::Meter::lufsPeak;
        g.drawText (dbText (lufs ? m[c].lufsDb : m[c].rmsDb), Rectangle<float> (centres[c] - 20.0f, 67.5f, 40.0f, 16.0f), Justification::centredTop, false);
    }

    const float (&lx)[2] = ledX[x0 > 0.0f ? 1 : 0];
    for (int c = 0; c < 2; ++c)
    {
        // a bar on the LED ladder's scale (40 cells on a 4 px pitch, cell k lit over LED k's threshold, the bottom LED's
        // row at y 248): solid up to the RMS, lighter from there up to the fast peak, and a pearl marker at the peak
        // readout's held value (until the readout is clicked); once that is over 0 dBFS (the readout turns red) the
        // marker is not drawn
        const int top = topLed (m[c].barDb), run = topLed (m[c].fastDb);       // strict thresholds
        const int dot = m[c].peakHoldDb > 0.0f ? theme::numLeds : topLed (m[c].peakHoldDb);
        auto cells = [] (int k) { return (float) (k + 1) / (float) theme::numLeds; };   // fraction lit up to cell k
        const Rectangle<float> inner (lx[c], 249.0f - 4.0f * (float) theme::numLeds, 8.0f, 4.0f * (float) theme::numLeds);
        theme::drawMeterBar (g, inner.expanded (1.0f), cells (jmax (top, run)), true,
                             dot > jmax (top, run) && dot < theme::numLeds ? cells (dot) : -1.0f);
        if (run > top)
        {
            g.setColour (theme::goldDeep.withAlpha (0.6f));
            g.fillRect (inner.withTop (249.0f - 4.0f * (float) (run + 1)).withBottom (249.0f - 4.0f * (float) (top + 1)));
        }
    }
    // the input target fills with the fast peak (the top of the lighter run, either channel): fully from -12 to -3 dBFS,
    // fading over 1.5 dB (one LED) at each end (measured frame by frame against the reference's own LEDs)
    const float fast = jmax (m[0].fastDb, m[1].fastDb);
    const float fill = jlimit (0.0f, 1.0f, (fast + 13.5f) / 1.5f) * jlimit (0.0f, 1.0f, (-1.5f - fast) / 1.5f);

    if (target)
    {
        // the target, in gold: two brackets and a line pair; filled while the level sits inside it
        // measured at 200 %: 1 px strokes, outer edges y 103.25 .. 122.75, corner radius 2.5; lit, each bracket is a solid
        // block rounded on its outer corners (y 103.25 .. 123.25) and the line pair becomes a solid block
        auto bracket = [&g] (float x, bool right, float filled)
        {
            if (filled > 0.0f)
            {
                Path f;
                f.addRoundedRectangle (x, 103.25f, 8.0f, 20.0f, 2.5f, 2.5f, ! right, right, ! right, right);
                g.setColour (theme::targetFill.withAlpha (filled));
                g.fillPath (f);
            }
            const float top = 103.75f, bottom = 122.75f, r = 2.5f;           // stroke centre lines (measured)
            const float ox = right ? x : x + 8.0f, ix = right ? x + 7.5f : x + 0.5f, d = right ? -r : r;
            Path p;
            p.startNewSubPath (ox, top);
            p.lineTo (ix + d, top);
            p.quadraticTo (ix, top, ix, top + r);
            p.lineTo (ix, bottom - r);
            p.quadraticTo (ix, bottom, ix + d, bottom);
            p.lineTo (ox, bottom);
            g.setColour (theme::target);
            g.strokePath (p, PathStrokeType (1.0f));
        };
        bracket (15.0f, false, fill);
        bracket (71.0f, true, fill);
        g.setColour (theme::targetLine);
        g.fillRect (35.0f, 103.25f, 24.0f, 1.0f);
        g.fillRect (35.0f, 122.25f, 24.0f, 1.0f);
        if (fill > 0.0f)
        {
            g.setColour (theme::targetFill.withAlpha (fill));
            g.fillRect (35.0f, 103.25f, 24.0f, 20.0f);
        }
    }
}

void PositronEditor::paintAmountText (Graphics& g)
{
    g.setColour (characterOn ? theme::letteringDim : theme::letteringFaint);
    g.setFont (theme::font (16.75f));
    theme::textAt (g, "amount", 364.0f, 120.5f);
    g.setColour (characterOn ? theme::gold : theme::letteringFaint);
    g.setFont (theme::font (41.5f));
    theme::textAt (g, String (roundToInt (characterValue * 200.0f)) + "%", 363.0f, 159.5f);
}

void PositronEditor::paintGainReduction (Graphics& g)
{
    const float meterY[3] { 86.0f, 151.0f, 216.0f };
    const float targetX[3] { 681.0f, 621.0f, 653.0f };
    const float baselines[3] { 125.5f, 190.5f, 255.5f };
    const char* names[3] { "high", "mid", "low" };
    g.setFont (theme::font (11.25f));
    for (int b = 0; b < 3; ++b)
    {
        g.setColour (characterOn ? theme::letteringDim : theme::dimLabel);
        theme::textAt (g, names[b], 571.0f, baselines[b]);
        g.setColour (characterOn ? theme::gold : theme::dimLabel);
        theme::textAt (g, grText (bandGrHold[b]), 701.5f, baselines[b], Justification::right);

        // 33 cells over 6 dB, lit from the right: floor (5.5 GR), none under 0.18 dB (MEASUREMENTS.md 6, tone staircases
        // per band); and a marker at the deepest reduction the readout holds (until it is clicked), on a 20 dB scale
        // (1.65 cells per dB). The cells keep the original's LED bars' 4 px pitch, the first ending at x 701
        const float gr = characterOn ? bandGrDb[b] : 0.0f;
        const int bars = jlimit (0, 33, (int) std::floor (gr * 5.5f));
        const int marker = characterOn ? jlimit (0, 33, (int) std::floor (bandGrHold[b] * 1.65f)) : 0;
        // the target fills with the band's gain reduction, fully over a range in dB and fading over ~0.22 dB at each end
        // (a law measured with tone staircases and a pink-noise ramp); not where the bracket is drawn
        struct Range { float lo, hi, edge; };
        constexpr Range ranges[3] { { 0.341f, 1.378f, 0.25f }, { 2.452f, 3.978f, 0.219f }, { 0.965f, 2.455f, 0.211f } };
        const auto& rg = ranges[b];
        const float fill = jlimit (0.0f, 1.0f, (gr - rg.lo) / rg.edge + 1.0f) * jlimit (0.0f, 1.0f, (rg.hi - gr) / rg.edge + 1.0f);
        // target: an upside-down U above the meter and a U below it, each filled while lit (the bars pass between)
        if (fill > 0.0f)
        {
            g.setColour (theme::targetFill.withAlpha (fill));
            g.fillRoundedRectangle (targetX[b], meterY[b] - 10.0f, 19.0f, 8.0f, 3.5f);
            g.fillRect (targetX[b], meterY[b] - 6.0f, 19.0f, 4.0f);
            g.fillRoundedRectangle (targetX[b], meterY[b] + 10.0f, 19.0f, 8.0f, 3.5f);
            g.fillRect (targetX[b], meterY[b] + 10.0f, 19.0f, 4.0f);
        }
        {
            g.setColour (characterOn ? theme::target : theme::dimLabel);
            Path p;
            // measured at 200 %: stroke centres x +0.25 / +18.25, y meterY - 9.25 / + 17.75, corner radius 3.5
            const float x = targetX[b] + 0.25f, w = 18.0f, yTop = meterY[b] - 9.25f, yBot = meterY[b] + 17.75f, r = 3.5f;
            p.startNewSubPath (x, meterY[b] - 2.0f);
            p.lineTo (x, yTop + r); p.quadraticTo (x, yTop, x + r, yTop);
            p.lineTo (x + w - r, yTop); p.quadraticTo (x + w, yTop, x + w, yTop + r);
            p.lineTo (x + w, meterY[b] - 2.0f);
            p.startNewSubPath (x, meterY[b] + 10.25f);
            p.lineTo (x, yBot - r); p.quadraticTo (x, yBot, x + r, yBot);
            p.lineTo (x + w - r, yBot); p.quadraticTo (x + w, yBot, x + w, yBot - r);
            p.lineTo (x + w, meterY[b] + 10.25f);
            g.strokePath (p, PathStrokeType (1.0f));
        }
        const Rectangle<float> inner (701.0f - 4.0f * 33.0f, meterY[b], 4.0f * 33.0f, 8.5f);
        drawMeterBarReversed (g, inner.expanded (1.0f), (float) bars / 33.0f, false, marker > bars ? (float) marker / 33.0f : -1.0f);
    }
}

void PositronEditor::paintLimiter (Graphics& g)
{
    const float centres[2] { 737.5f, 774.0f };
    g.setFont (theme::font (12.0f));
    for (int c = 0; c < 2; ++c)
    {
        g.setColour (limiterOn ? theme::gold : theme::dimLabel);
        g.drawText (grText (limGrHold[c]), Rectangle<float> (centres[c] - 20.0f, 67.5f, 40.0f, 16.0f), Justification::centredTop, false);
        // in the original's dash cells (MEASUREMENTS.md 6: 31 on a 4 px pitch from y 90): a marker at cell
        // ceil((reduction - 0.05) / 1.5) for the deepest reduction the readout holds (cell 0 at rest; cell 1 from 0.05
        // dB, cell 2 from 1.55), and a bar from the top, one cell shorter, for the reduction now; empty while bypassed
        const auto cell = [] (float gr) { return jlimit (0, 30, (int) std::ceil (jmax (0.0f, gr - 0.05f) / 1.5f)); };
        const int bar = limiterOn ? jmax (0, cell (limGrDb[c]) - 1) : 0;
        const int marker = cell (limGrHold[c]) + 1;
        const Rectangle<float> inner (centres[c] - 4.0f, 90.0f, 8.0f, 4.0f * 31.0f);
        drawMeterBarReversed (g, inner.expanded (1.0f), (float) bar / 31.0f, true, limiterOn ? (float) marker / 31.0f : -1.0f);
    }
}

void PositronEditor::paintPlate (Graphics& g)
{
    // the plate: a separate rounded panel (x 0.5 .. 887.5, y 266.5 .. 358.75, corner radius 11) on black, a theme card
    g.setColour (theme::bg);
    g.fillRect (0.0f, 265.0f, designW, designH - 265.0f);
    const Rectangle<float> plate (0.5f, 266.5f, designW - 1.0f, 92.25f);
    theme::drawCard (g, plate, 11.0f);

    // where the original has its grille, our own decoration (x 176 .. 559, y 268 .. 349)
    {
        // faint stars, seeded, kept off the orbits' middle
        Random rng (1957);
        for (int i = 0; i < 70; ++i)
        {
            const Point<float> p (178.0f + rng.nextFloat() * 380.0f, 270.0f + rng.nextFloat() * 78.0f);
            const float r = 0.35f + 0.5f * rng.nextFloat() * rng.nextFloat();
            const float a = 0.25f + 0.5f * rng.nextFloat();
            const float ex = (p.x - orreryX) / 30.0f, ey = (p.y - orreryY) / 14.0f;
            if (ex * ex + ey * ey < 1.0f) continue;
            g.setColour (theme::letteringFaint.withAlpha (a));
            g.fillEllipse (Rectangle<float> (2.0f * r, 2.0f * r).withCentre (p));
        }
        // the orbits, the outer ones fainter, and a planet on each (the far half of an orbit behind the near half)
        for (int i = 0; i < (int) std::size (orbitRx); ++i)
        {
            const float rx = orbitRx[i], ry = rx * orbitTilt;
            g.setColour (theme::lineLight.withAlpha (0.55f - 0.09f * (float) i));
            g.drawEllipse (Rectangle<float> (2.0f * rx, 2.0f * ry).withCentre ({ orreryX, orreryY }), 1.0f);
            const Point<float> p (orreryX + rx * std::cos (planetAngle[i]), orreryY + ry * std::sin (planetAngle[i]));
            const float pr = i == 2 ? 2.6f : 1.9f;
            g.setColour (theme::card);
            g.fillEllipse (Rectangle<float> (2.0f * pr + 2.0f, 2.0f * pr + 2.0f).withCentre (p));
            g.setColour (i == 2 ? theme::violetDeep : theme::lineLight);
            g.fillEllipse (Rectangle<float> (2.0f * pr, 2.0f * pr).withCentre (p));
        }
        // the suite's mark as the sun
        drawMark (g, { orreryX, orreryY }, 9.0f, theme::violetDeep, theme::violet.withAlpha (0.85f));
    }

    // shadows of the plate knobs: the light comes from the upper right, so they fall to the left and down
    // (a soft cast shadow plus a tight contact shadow, drawn from the tokens in KnobShadow.h)
    {
        // rendered once per physical scale and drawn under each knob
        const float dpx = theme::pixelScale (g, content);
        constexpr float R = 25.06f, reach = 89.0f, half = R + reach;
        if (knobShadow.isNull() || (std::abs (dpx - knobShadowScale) > 0.001f && ! theme::liveResizing (content)))
        {
            const int px = (int) std::ceil (2.0f * half * dpx);
            knobShadow = Image (Image::ARGB, px, px, true, SoftwareImageType());
            Image::BitmapData bd (knobShadow, Image::BitmapData::writeOnly);
            for (int y = 0; y < px; ++y)
                for (int x = 0; x < px; ++x)
                {
                    const float dx = ((float) x + 0.5f) / dpx - half, dy = ((float) y + 0.5f) / dpx - half;
                    const float d = std::sqrt (dx * dx + dy * dy) - R;
                    if (d < -1.0f || d >= reach) continue;
                    const float fade = jlimit (0.0f, 1.0f, (reach - d) / 15.0f);       // soft end, no ring
                    bd.setPixelColour (x, y, Colours::black.withAlpha (jlimit (0.0f, 1.0f, po::knobshadow::darkness (dx, dy, R) * fade)));
                }
            knobShadowScale = dpx;
        }
        for (float cx : { 45.755f, 754.745f, 841.74f })
            g.drawImage (knobShadow, Rectangle<float> (2.0f * half, 2.0f * half).withCentre ({ cx, 313.11f }));
    }

    // labels
    g.setColour (theme::plateText);
    g.setFont (theme::font (12.0f));
    const std::pair<String, float> labels[] { { captionText (inputKnob, "input"), 46.0f }, { "eq", 132.25f }, { "gain reduction", 636.75f },
                                              { captionText (limiterKnob, "limiter"), 755.0f }, { captionText (outputKnob, "output"), 841.75f } };
    for (auto& [t, x] : labels) theme::textAt (g, t, x, 280.0f, Justification::horizontallyCentred);

    // lettering: the name centred on the sixteen letter slots (24.2 px apart), one letter per slot
    const String word = "POSITRON";
    const int firstSlot = (16 - word.length()) / 2;
    g.setFont (theme::font (9.5f));
    g.setColour (theme::letteringDim);
    for (int i = 0; i < word.length(); ++i)
        theme::textAt (g, String::charToString (word[i]), 186.5f + 24.2f * (float) (firstSlot + i), 357.5f, Justification::horizontallyCentred);
}

//==============================================================================
void PositronEditor::closePopups()
{
    if (dropList != nullptr) content.removeChildComponent (dropList.get());
    dropList.reset();
    presetBox.open = scaleBox.open = false;
    presetBox.repaint(); scaleBox.repaint();
}

void PositronEditor::showPresetList()
{
    closePopups();
    const auto all = proc.presets.list();
    std::vector<po::DropList::Item> items { { "factory", true } };
    std::vector<int> map { -1 };
    for (int i = 0; i < (int) all.size(); ++i)
        if (all[(size_t) i].factory) { items.push_back ({ all[(size_t) i].name, false, all[(size_t) i].name == proc.presets.currentName() }); map.push_back (i); }
    items.push_back ({ "user", true }); map.push_back (-1);
    bool anyUser = false;
    for (int i = 0; i < (int) all.size(); ++i)
        if (! all[(size_t) i].factory) { items.push_back ({ all[(size_t) i].name }); map.push_back (i); anyUser = true; }
    if (! anyUser) { items.push_back ({ "-" }); map.push_back (-1); }
    dropList = std::make_unique<po::DropList>();
    dropList->setItems (items, 24.0f, true);
    dropList->onPick = [this, all, map] (int row)
    {
        const int idx = map[(size_t) row];
        if (idx >= 0) { proc.presets.load (all[(size_t) idx]); presetBox.text = proc.presets.currentName(); }
        closePopups();
    };
    dropList->setBounds (176, 27, 193, (int) (24.0f * (float) items.size()) - 2);
    presetBox.open = true;
    content.addAndMakeVisible (*dropList);
}

void PositronEditor::showScaleList()
{
    closePopups();
    std::vector<po::DropList::Item> items;
    for (float s : scales) items.push_back ({ String (roundToInt (s * 100.0f)) + "%", false, std::abs (s - scale) < 0.01f });
    dropList = std::make_unique<po::DropList>();
    dropList->setItems (items, 24.0f, false);
    dropList->onPick = [safe = Component::SafePointer<PositronEditor> (this)] (int row)
    {
        const float s = scales[row];
        safe->closePopups();
        MessageManager::callAsync ([safe, s] { if (safe != nullptr) safe->setUiScale (s); });
    };
    dropList->setBounds (794, 27, 66, (int) (24.0f * (float) items.size()) + 1);
    scaleBox.open = true;
    content.addAndMakeVisible (*dropList);
}

namespace
{
// settings page: oversampling ratio, I/O metering, particle animation (layout measured on the reference)
class SettingsDialog : public po::Dialog
{
public:
    // the reference's three rows plus ours: particle style (classic / positron)
    SettingsDialog() : Dialog ("settings", { 234.0f, 50.5f, 420.0f, 300.0f }, false) {}
    void paint (Graphics& g) override
    {
        Dialog::paint (g);
        auto& st = po::Settings::get();
        g.setColour (theme::line);
        g.fillRect (box.getX(), 145.0f, box.getWidth(), 1.0f);
        g.fillRect (box.getX(), 236.5f, box.getWidth(), 1.0f);
        g.fillRect (box.getX(), 292.0f, box.getWidth(), 1.0f);
        g.setColour (theme::text);
        g.setFont (theme::font (16.75f));
        theme::textAt (g, "oversampling ratio", 258.0f, 118.5f);
        theme::textAt (g, "I/O metering", 258.0f, 182.0f);
        theme::textAt (g, "particle animation", 258.0f, 274.0f);
        theme::textAt (g, "particle style", 258.0f, 325.5f);
        const int ratios[4] { 1, 2, 4, 8 };
        int sel = 0;
        for (int i = 0; i < 4; ++i) if (ratios[i] == st.oversampling()) sel = i;
        segments (g, { 454.0f, 101.5f, 167.5f, 23.0f }, { "1", "2", "4", "8" }, sel);
        segments (g, { 454.0f, 257.5f, 84.0f, 23.0f }, { "ON", "OFF" }, st.animation() ? 0 : 1);
        segments (g, { 454.0f, 309.0f, 190.0f, 23.0f }, { "CLASSIC", "POSITRON" }, st.particleStyle() == po::Settings::Particles::positron ? 1 : 0);
        radio (g, 178.0f, "RMS & Peak", st.meterMode() == po::Settings::Meter::rmsPeak);
        radio (g, 204.0f, "Short-term LUFS & Peak", st.meterMode() == po::Settings::Meter::lufsPeak);
    }
    void mouseDown (const MouseEvent& e) override
    {
        auto& st = po::Settings::get();
        const auto p = e.position;
        if (Rectangle<float> (454.0f, 101.5f, 167.5f, 23.0f).contains (p)) { const int r[4] { 1, 2, 4, 8 }; st.setOversampling (r[jlimit (0, 3, (int) ((p.x - 454.0f) / (167.5f / 4.0f)))]); repaint(); return; }
        if (Rectangle<float> (454.0f, 257.5f, 84.0f, 23.0f).contains (p)) { st.setAnimation (p.x < 496.0f); repaint(); return; }
        if (Rectangle<float> (454.0f, 309.0f, 190.0f, 23.0f).contains (p))
        {
            st.setParticleStyle (p.x < 549.0f ? po::Settings::Particles::classic : po::Settings::Particles::positron);
            repaint(); return;
        }
        if (Rectangle<float> (450.0f, 168.0f, 190.0f, 20.0f).contains (p)) { st.setMeterMode (po::Settings::Meter::rmsPeak); repaint(); return; }
        if (Rectangle<float> (450.0f, 194.0f, 190.0f, 20.0f).contains (p)) { st.setMeterMode (po::Settings::Meter::lufsPeak); repaint(); return; }
        Dialog::mouseDown (e);
    }
private:
    static void segments (Graphics& g, Rectangle<float> r, StringArray labels, int sel)
    {
        const float w = r.getWidth() / (float) labels.size();
        g.setColour (theme::boxFill);
        g.fillRoundedRectangle (r, 4.0f);
        for (int i = 0; i < labels.size(); ++i)
        {
            const auto cell = Rectangle<float> (r.getX() + w * (float) i, r.getY(), w, r.getHeight());
            if (i == sel)              // the selection filled gold, as the top bar's INT / EXT
            {
                Graphics::ScopedSaveState s (g);
                Path clip; clip.addRoundedRectangle (r, 4.0f);
                g.reduceClipRegion (clip);
                g.setColour (theme::gold);
                g.fillRect (cell);
            }
            if (i > 0) { g.setColour (theme::lineLight); g.fillRect (cell.getX() - 0.5f, r.getY(), 1.0f, r.getHeight()); }
            g.setColour (i == sel ? theme::well : theme::text);
            g.setFont (theme::font (12.0f));
            g.drawText (labels[i], cell, Justification::centred, false);
        }
        g.setColour (theme::lineLight);
        g.drawRoundedRectangle (r.reduced (0.5f), 4.0f, 1.0f);
    }
    static void radio (Graphics& g, float cy, const String& text, bool on)
    {
        g.setColour (theme::lineLight);
        g.drawEllipse (Rectangle<float> (13.0f, 13.0f).withCentre ({ 460.5f, cy }), 1.0f);
        g.setColour (theme::gold);
        if (on) g.fillEllipse (Rectangle<float> (7.0f, 7.0f).withCentre ({ 460.5f, cy }));
        g.setColour (theme::text);
        g.setFont (theme::font (12.0f));
        theme::textAt (g, text, 478.0f, cy + 4.3f);
    }
};

// save preset: a name field and save / cancel
class SaveDialog : public po::Dialog
{
public:
    SaveDialog (po::PresetManager& pm, std::function<void()> saved)
        : Dialog ("save preset", { 240.0f, 74.0f, 408.0f, 209.0f }, true), presets (pm), onSaved (std::move (saved))
    {
        addAndMakeVisible (name);
        name.setBounds (Rectangle<float> (266.0f, 168.0f, 356.0f, 22.0f).toNearestInt());
        name.setFont (theme::font (16.0f));
        name.setColour (TextEditor::backgroundColourId, Colours::transparentBlack);
        name.setColour (TextEditor::outlineColourId, Colours::transparentBlack);
        name.setColour (TextEditor::focusedOutlineColourId, Colours::transparentBlack);
        name.setColour (TextEditor::textColourId, theme::text);
        name.setColour (TextEditor::highlightColourId, theme::goldDeep);
        name.setColour (CaretComponent::caretColourId, theme::text);
        name.setText (pm.currentName(), false);
        name.onReturnKey = [this] { commit(); };
        name.onEscapeKey = [this] { if (onClose) onClose(); };
    }
    void focusName() { name.grabKeyboardFocus(); name.selectAll(); }
    void paint (Graphics& g) override
    {
        Dialog::paint (g);
        g.setColour (theme::text.withAlpha (0.9f));
        g.drawRect (Rectangle<float> (258.0f, 146.5f, 371.5f, 47.0f), 1.0f);
        g.setColour (theme::letteringDim);
        g.setFont (theme::font (12.5f));
        theme::textAt (g, "preset name", 267.5f, 164.5f);
        button (g, saveArea, "save");
        button (g, cancelArea, "cancel");
    }
    void mouseDown (const MouseEvent& e) override
    {
        if (saveArea.contains (e.position)) { commit(); return; }
        if (cancelArea.contains (e.position)) { if (onClose) onClose(); return; }
        Dialog::mouseDown (e);
    }
private:
    void commit()
    {
        if (presets.save (name.getText())) { if (onSaved) onSaved(); }
        if (onClose) onClose();
    }
    static void button (Graphics& g, Rectangle<float> r, const String& t)
    {
        g.setColour (Colours::black);
        g.fillRoundedRectangle (r, 4.0f);
        g.setColour (theme::text);
        g.drawRoundedRectangle (r.reduced (0.5f), 4.0f, 1.0f);
        g.setFont (theme::font (14.5f));
        g.drawText (t, r, Justification::centred, false);
    }
    const Rectangle<float> saveArea { 297.0f, 230.5f, 179.0f, 35.5f }, cancelArea { 501.0f, 230.5f, 89.5f, 35.5f };
    po::PresetManager& presets;
    std::function<void()> onSaved;
    TextEditor name;
};
}

void PositronEditor::showSettings()
{
    closePopups();
    auto d = std::make_unique<SettingsDialog>();
    d->setBounds (0, 0, (int) std::ceil (designW), (int) std::ceil (designH));
    d->onClose = [safe = Component::SafePointer<PositronEditor> (this)]
    {
        MessageManager::callAsync ([safe] { if (safe != nullptr) { safe->content.removeChildComponent (safe->dialog.get()); safe->dialog.reset(); } });
    };
    content.addAndMakeVisible (*d);
    dialog = std::move (d);
}

void PositronEditor::showSavePreset()
{
    closePopups();
    auto d = std::make_unique<SaveDialog> (proc.presets, [this] { presetBox.text = proc.presets.currentName(); presetBox.repaint(); });
    d->setBounds (0, 0, (int) std::ceil (designW), (int) std::ceil (designH));
    d->onClose = [safe = Component::SafePointer<PositronEditor> (this)]
    {
        MessageManager::callAsync ([safe] { if (safe != nullptr) { safe->content.removeChildComponent (safe->dialog.get()); safe->dialog.reset(); } });
    };
    content.addAndMakeVisible (*d);
    auto* raw = d.get();
    dialog = std::move (d);
    raw->focusName();
}

void PositronEditor::showDialog (std::unique_ptr<po::Dialog> d)
{
    closePopups();
    if (dialog != nullptr) { content.removeChildComponent (dialog.get()); dialog.reset(); }
    d->setBounds (0, 0, (int) std::ceil (designW), (int) std::ceil (designH));
    d->onClose = [safe = Component::SafePointer<PositronEditor> (this)]
    {
        MessageManager::callAsync ([safe] { if (safe != nullptr) { safe->content.removeChildComponent (safe->dialog.get()); safe->dialog.reset(); } });
    };
    content.addAndMakeVisible (*d);
    dialog = std::move (d);
}

// the logo's menu (version, About, repository, issues, licence), drawn like the preset list
void PositronEditor::showAboutMenu()
{
    if (dropList != nullptr) { closePopups(); return; }
    const String version = JucePlugin_VersionString;
    dropList = std::make_unique<po::DropList>();
    dropList->setItems ({ { "Positron v" + version, true }, { "About Positron" }, { "Orrery Suite on GitHub" },
                          { "Report an Issue" }, { "License (AGPL-3.0)" } }, 24.0f, true);
    dropList->onPick = [safe = Component::SafePointer<PositronEditor> (this), version] (int row)
    {
        if (safe == nullptr) return;
        safe->closePopups();
        if (row == 1)
        {
            const auto wrapper = safe->proc.wrapperType;
            const String format = AudioProcessor::getWrapperTypeDescription (wrapper);
            safe->showDialog (std::make_unique<po::InfoDialog> ("about Positron", std::vector<std::pair<String, String>> {
                { "Version", version + (wrapper == AudioProcessor::wrapperType_Undefined ? String() : " (" + format + ")") },
                { {}, {} },
                { "What it is", "An open-source mix-bus processor modelled on and measured against Cradle's The God Particle" },
                { "Part of", "Orrery Suite: open-source recreations, null-tested against the originals" },
                { "License", "Open source under the GNU Affero General Public License v3" },
                { "Built with", "JUCE, the VST3 SDK and CLAP; Instrument Sans (SIL OFL). Their licenses come with it" },
                { "Source", repository.fromFirstOccurrenceOf ("https://", false, false) },
                { {}, {} },
                { "Note", "An independent project, not affiliated with or endorsed by Cradle. The God Particle is a trademark of its owner." } }));
        }
        else if (row == 2) URL (repository).launchInDefaultBrowser();
        else if (row == 3) URL (repository + "/issues/new/choose").launchInDefaultBrowser();
        else if (row == 4) URL (repository + "/blob/main/LICENSE").launchInDefaultBrowser();
    };
    dropList->setBounds (4, 27, 214, 24 * 5 - 2);
    content.addAndMakeVisible (*dropList);
}
