#include "PluginEditor.h"
#include "ui/Faceplate.h"
#include "shared/ui/SaveDialog.h"

using namespace juce;
namespace theme = orrery::theme;
namespace lk = wr::look;
#ifndef SUITE_REPOSITORY
 #define SUITE_REPOSITORY "https://github.com/MaymiPR/Orrery"
#endif
static const juce::String repository = SUITE_REPOSITORY;

namespace
{
// fractional bounds: the component is placed with a transform so it lands on the measured position
void place (Component& c, Rectangle<float> r)
{
    c.setBounds (0, 0, (int) std::ceil (r.getWidth()), (int) std::ceil (r.getHeight()));
    c.setTransform (AffineTransform::translation (r.getX(), r.getY()));
}
// a knob: an even square of whole pixels round its centre, unscaled, so its body image lands pixel for pixel at 100 %
void placeKnob (wr::ui::Knob& k, float cx, float cy, float r)
{
    const int s = 2 * (int) std::ceil (r);
    k.radius = r;
    k.setBounds (0, 0, s, s);
    k.setTransform (AffineTransform::translation (cx - (float) s * 0.5f, cy - (float) s * 0.5f));
}
float toDb (float lin) { return lin > 1.0e-6f ? Decibels::gainToDecibels (lin) : -200.0f; }
float smallX (int section) { return lk::centreX (section); }
}

WraithEditor::WraithEditor (WraithProcessor& p) : AudioProcessorEditor (p), proc (p)
{
    orrery::noFocus (*this);
    orrery::noFocus (content);
    setOpaque (true);
    addAndMakeVisible (content);
    content.setBounds (0, 0, (int) std::ceil (designW), (int) std::ceil (designH));

    for (auto* c : std::initializer_list<Component*> { &logo, &presetBox, &prevButton, &nextButton, &saveButton, &scaleBox, &compare,
                                                       &sidechain, &ioLinkButton, &riderPill,
                                                       &roomPlate, &inMeter, &outMeter, &compression, &focus, &eqHigh, &eqLow, &stereo,
                                                       &doublerMix, &filter, &reverbMix, &inGain, &outGain })
        content.addAndMakeVisible (*c);
    for (auto& d : displays) content.addAndMakeVisible (d);
    for (auto& b : power) content.addAndMakeVisible (b);
    content.addChildComponent (riderPanel);
    for (auto* k : { &riderSpeed, &riderAmount, &riderFloor }) riderPanel.addAndMakeVisible (*k);
    content.addChildComponent (toast);                // over everything else (shown by Compare's arrow)
    content.addMouseListener (&hoverTracker, true);

    // top bar: the reference's controls as measured (preset box 270 wide, arrows 12 and 48 px after it, save 90 px
    // after it, UI scale box 966 ... 1032), with ours as on the suite's other plug-ins: Compare left of "Preset" (the
    // preset group moved 96 px right for it), the side-chain switch and I/O LINK between the save button and "UI Scale"
    logo.setBounds (6, 7, 17, 17);
    compare.setBounds (40, 3, 74, 25);
    presetBox.setBounds (176, 3, 270, 25);
    prevButton.setBounds (458, 3, 24, 25);
    nextButton.setBounds (494, 3, 24, 25);
    saveButton.setBounds (536, 3, 24, 25);
    sidechain.setBounds (672, 3, 85, 25);
    ioLinkButton.setBounds (786, 3, 64, 25);
    toast.setBounds (422, 340, 200, 61);            // centred low on the plate, as on Scorpius
    scaleBox.setBounds (966, 3, 66, 25);

    for (int i = 0; i < 4; ++i)
    {
        place (power[i], lk::powerPill[i].r());
        place (displays[i], lk::display[i].r());
        displays[i].origin = { lk::display[i].x, lk::display[i].y };
    }
    displays[0].drawArt = [this] (Graphics& g) { drawCharacter (g); };
    displays[1].drawArt = [this] (Graphics& g) { drawEq (g); };
    displays[2].drawArt = [this] (Graphics& g) { drawDoubler (g); };
    displays[3].drawArt = [this] (Graphics& g) { drawReverb (g); };
    place (riderPill, lk::riderPill.r());
    riderPill.splitX = lk::riderSplit - lk::riderPill.x;
    place (roomPlate, lk::roomPlatePill.r());
    roomPlate.splitX = lk::roomPlateSplit - lk::roomPlatePill.x;
    place (inMeter, lk::meter[0].r().reduced (3.0f));
    inMeter.origin = lk::meter[0].r().reduced (3.0f).getPosition();
    place (outMeter, lk::meter[1].r().reduced (3.0f));
    outMeter.origin = lk::meter[1].r().reduced (3.0f).getPosition();

    placeKnob (compression, lk::compressionKnob.x, lk::compressionKnob.y, lk::compressionKnob.r);
    placeKnob (focus, lk::focusKnob.x, lk::focusKnob.y, lk::focusKnob.r);
    const wr::ui::Knob* dummy = nullptr; ignoreUnused (dummy);
    std::pair<wr::ui::Knob*, int> small[] { { &eqHigh, lk::eq }, { &stereo, lk::doubler }, { &filter, lk::reverb } };
    for (auto& [k, s] : small) placeKnob (*k, smallX (s), lk::smallKnobTopY, lk::smallKnobR);
    std::pair<wr::ui::Knob*, int> lower[] { { &eqLow, lk::eq }, { &doublerMix, lk::doubler }, { &reverbMix, lk::reverb } };
    for (auto& [k, s] : lower) placeKnob (*k, smallX (s), lk::smallKnobBottomY, lk::smallKnobR);
    placeKnob (inGain, lk::gainKnob[0].x, lk::gainKnob[0].y, lk::gainKnob[0].r);
    placeKnob (outGain, lk::gainKnob[1].x, lk::gainKnob[1].y, lk::gainKnob[1].r);
    riderPanel.setBounds (0, 0, (int) std::ceil (designW), (int) std::ceil (designH));
    for (int i = 0; i < 3; ++i)
        placeKnob (*std::array<wr::ui::Knob*, 3> { &riderSpeed, &riderAmount, &riderFloor }[(size_t) i], lk::riderKnobX, lk::riderKnobY[i], lk::riderKnobR);

    auto& s = proc.apvts;
    auto attach = [&] (wr::ui::Knob& k, const char* pid)
    {
        attachments.push_back (std::make_unique<AudioProcessorValueTreeState::SliderAttachment> (s, pid, k));
        if (auto* prm = dynamic_cast<RangedAudioParameter*> (s.getParameter (pid)))
            k.setDefault (prm->convertFrom0to1 (prm->getDefaultValue()));
    };
    attach (compression, wr::id::compression);
    attach (focus, wr::id::focus);
    attach (eqHigh, wr::id::eqHigh);
    attach (eqLow, wr::id::eqLow);
    attach (stereo, wr::id::doublerStereo);
    attach (doublerMix, wr::id::doublerMix);
    attach (filter, wr::id::reverbFilter);
    attach (reverbMix, wr::id::reverbMix);
    attach (inGain, wr::id::inputGain);
    attach (outGain, wr::id::outputGain);
    attach (riderSpeed, wr::id::riderSpeed);
    attach (riderAmount, wr::id::riderAmount);
    attach (riderFloor, wr::id::riderFloor);
    for (auto* k : { &compression, &focus, &eqHigh, &eqLow, &stereo, &doublerMix, &filter, &reverbMix })
        k->onValueChange = [this] { for (auto& d : displays) d.repaint(); content.repaint(); };
    riderFloor.onDragStart = [this] { inMeter.showFloor = true; inMeter.repaint(); };
    riderFloor.onDragEnd = [this] { inMeter.showFloor = false; inMeter.repaint(); };
    riderFloor.onValueChange = [this] { inMeter.floorDb = (float) riderFloor.getValue(); inMeter.repaint(); riderPanel.repaint(); };
    for (auto* k : { &riderSpeed, &riderAmount }) k->onValueChange = [this] { riderPanel.repaint(); };

    const char* powerIds[4] { wr::id::characterOn, wr::id::eqOn, wr::id::doublerOn, wr::id::reverbOn };
    for (int i = 0; i < 4; ++i) power[i].onClick = [this, pid = powerIds[i]] { toggleParam (pid); };
    riderPill.onRider = [this] { toggleParam (wr::id::riderOn); };
    riderPill.onArrow = [this] { setRiderPanel (! riderOpen); };
    roomPlate.onChange = [this] (int i)
    {
        if (auto* prm = proc.apvts.getParameter (wr::id::reverbType))
        {
            prm->beginChangeGesture();
            prm->setValueNotifyingHost ((float) i);
            prm->endChangeGesture();
        }
        updateFromParams();
    };
    inMeter.onResetHold = [this] { holdDb[0] = holdDb[1] = -200.0f; };
    outMeter.onResetHold = [this] { holdDb[2] = holdDb[3] = -200.0f; };
    for (auto* pid : wr::allIds) s.addParameterListener (pid, this);

    for (auto* k : { &inGain, &outGain })
    {
        k->onDragStart = [this, k] { beginLink (*k); };
        k->onValueChange = [this, k] { if (linkSource == k) mirror (k == &inGain); };
        k->onDragEnd = [this, k] { endLink (*k); };
    }
    ioLinkButton.active = proc.ioLink.load();
    ioLinkButton.onClick = [this]
    {
        proc.ioLink = ! proc.ioLink.load();
        ioLinkButton.active = proc.ioLink.load();
        ioLinkButton.repaint();
        if (proc.ioLink.load())                    // linking snaps the output to the input's opposite
            if (auto* prm = proc.apvts.getParameter (wr::id::outputGain))
            {
                prm->beginChangeGesture();
                mirror (true);
                prm->endChangeGesture();
            }
    };
    sidechain.external = proc.sidechainExternal.load();
    sidechain.onChange = [this] (bool ext) { proc.sidechainExternal = ext; };
    compare.slot = proc.compareSlot();
    compare.onSelect = [this] (int slot)
    {
        proc.selectCompareSlot (slot);
        compare.slot = proc.compareSlot();
        compare.repaint();
        updateFromParams();
    };
    compare.onCopy = [this]
    {
        proc.copyCompareSlot();
        toast.show (proc.compareSlot() == 0 ? "A copied to B." : "B copied to A.");
    };
    presetBox.onClick = [this] { if (dropList != nullptr) closePopups(); else showPresetList(); };
    scaleBox.onClick = [this] { if (dropList != nullptr) closePopups(); else showScaleList(); };
    prevButton.onClick = [this] { proc.presets.step (-1); presetBox.text = proc.presets.currentName(); presetBox.repaint(); };
    nextButton.onClick = [this] { proc.presets.step (1); presetBox.text = proc.presets.currentName(); presetBox.repaint(); };
    saveButton.onClick = [this] { showSavePreset(); };
    logo.onClick = [this] { showAboutMenu(); };
    presetBox.text = proc.presets.currentName();

    updateFromParams();
    constrainer.setFixedAspectRatio (designW / designH);
    constrainer.setSizeLimits ((int) (designW * scales[0]), (int) (designH * scales[0]),
                               (int) (designW * scales[std::size (scales) - 1]), (int) (designH * scales[std::size (scales) - 1]));
    setResizable (true, false);          // hosts may resize the window too; the corner below is our own
    setConstrainer (&constrainer);
    grip = std::make_unique<Grip> (this, &constrainer);
    orrery::noFocus (*grip);
    addAndMakeVisible (*grip);
    grip->setAlwaysOnTop (true);
    setUiScale (proc.uiScale.load());
    animate = true;
    lastTick = Time::getMillisecondCounterHiRes() * 0.001;
    startTimerHz (60);
}

WraithEditor::~WraithEditor()
{
    content.removeMouseListener (&hoverTracker);
    for (auto* pid : wr::allIds) proc.apvts.removeParameterListener (pid, this);
}

void WraithEditor::toggleParam (const char* pid)
{
    if (auto* prm = proc.apvts.getParameter (pid))
    {
        prm->beginChangeGesture();
        prm->setValueNotifyingHost (prm->getValue() >= 0.5f ? 0.0f : 1.0f);
        prm->endChangeGesture();
    }
    updateFromParams();         // at once (the listener's update comes a message later)
}

void WraithEditor::setRiderPanel (bool open)
{
    // (filmed: the panel is there in the first frame after the click, no animation; a click outside it closes it)
    riderOpen = open;
    closePopups();
    riderPanel.setVisible (open);
    if (open) riderPanel.toFront (false);
    // the input section stays above the panel's dimming
    for (auto* c : std::initializer_list<Component*> { &inMeter, &riderPill, &inGain })
        if (open) c->toFront (false);
    riderPill.panelOpen = open;
    riderPill.repaint();
    content.repaint();
}

void WraithEditor::setUiScale (float s)
{
    scale = s;
    proc.uiScale = s;
    scaleBox.text = String (roundToInt (s * 100.0f)) + "%";
    content.setTransform (AffineTransform::scale (s));
    setSize ((int) std::round (designW * s), (int) std::round (designH * s));
}

// a new size (the corner, the host, or setUiScale) sets the scale; sizes from setUiScale itself keep their exact scale
void WraithEditor::resized()
{
    if (std::abs (getWidth() - (int) std::round (designW * scale)) > 1)
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
        const int g = roundToInt (16.0f * scale);
        grip->setBounds (getWidth() - g, getHeight() - g, g, g);
    }
}

void WraithEditor::Grip::paint (Graphics& g)
{
    const float w = (float) getWidth(), u = w / 16.0f;
    const auto light = isMouseOverOrDragging() ? theme::letteringDim : theme::letteringFaint;
    for (int i = 1; i <= 3; ++i)
    {
        const float d = (float) i * 4.0f * u;
        g.setColour (theme::bg.withAlpha (0.5f));
        g.drawLine (w - d - 0.9f * u, w - 2.0f * u, w - 2.0f * u, w - d - 0.9f * u, 1.2f * u);
        g.setColour (light);
        g.drawLine (w - d, w - 2.0f * u, w - 2.0f * u, w - d, 1.2f * u);
    }
}

void WraithEditor::Grip::mouseUp (const MouseEvent& e)
{
    ResizableCornerComponent::mouseUp (e);
    if (auto* ed = findParentComponentOfClass<WraithEditor>()) ed->endLiveResize();
}

void WraithEditor::endLiveResize()
{
    if (! getProperties().getWithDefault ("liveResize", false)) return;
    getProperties().set ("liveResize", false);
    content.repaint();
    for (auto* k : { &compression, &focus, &eqHigh, &eqLow, &stereo, &doublerMix, &filter, &reverbMix, &inGain, &outGain }) k->repaint();
}

void WraithEditor::parameterChanged (const String& pid, float)
{
    // called from the thread that changed the parameter: update on the message thread (and read the values there,
    // after every listener ran: inside the callback the raw value can still be the old one)
    const bool gain = pid == wr::id::inputGain || pid == wr::id::outputGain, fromInput = pid == wr::id::inputGain;
    MessageManager::callAsync ([safe = Component::SafePointer<WraithEditor> (this), gain, fromInput]
    {
        if (safe == nullptr) return;
        if (gain && safe->linkSource == nullptr) safe->mirror (fromInput);      // automation, presets: keep the link
        safe->updateFromParams();
    });
}

void WraithEditor::beginLink (Slider& src)
{
    if (! proc.ioLink.load() || linkSource != nullptr) return;
    if (auto* prm = proc.apvts.getParameter (&src == &inGain ? wr::id::outputGain : wr::id::inputGain))
    {
        linkSource = &src;
        prm->beginChangeGesture();
        mirror (&src == &inGain);
    }
}

void WraithEditor::mirror (bool fromInput)
{
    if (! proc.ioLink.load() || mirroring) return;
    const ScopedValueSetter<bool> guard (mirroring, true);
    const auto* srcId = fromInput ? wr::id::inputGain : wr::id::outputGain;
    const auto* dstId = fromInput ? wr::id::outputGain : wr::id::inputGain;
    if (auto* dst = dynamic_cast<RangedAudioParameter*> (proc.apvts.getParameter (dstId)))
    {
        const float target = dst->getNormalisableRange().snapToLegalValue (-proc.apvts.getRawParameterValue (srcId)->load());
        if (std::abs (proc.apvts.getRawParameterValue (dstId)->load() - target) > 1.0e-5f)
            dst->setValueNotifyingHost (dst->convertTo0to1 (target));
    }
    content.repaint();
}

void WraithEditor::endLink (Slider& src)
{
    if (linkSource != &src) return;
    if (auto* prm = proc.apvts.getParameter (&src == &inGain ? wr::id::outputGain : wr::id::inputGain))
        prm->endChangeGesture();
    linkSource = nullptr;
    content.repaint();
}

void WraithEditor::updateFromParams()
{
    const char* powerIds[4] { wr::id::characterOn, wr::id::eqOn, wr::id::doublerOn, wr::id::reverbOn };
    for (int i = 0; i < 4; ++i)
    {
        power[i].active = param (powerIds[i]) >= 0.5f;
        power[i].repaint();
        for (auto* k : sectionKnobs (i)) k->setSectionOn (power[i].active);
        displays[i].setLit (power[i].active, animate);
        displays[i].repaint();
    }
    riderPill.riderOn = param (wr::id::riderOn) >= 0.5f;
    riderPill.repaint();
    roomPlate.selected = param (wr::id::reverbType) >= 0.5f ? 1 : 0;
    roomPlate.repaint();
    if (revMorph < 0.0f || ! animate) revMorph = (float) roomPlate.selected;     // (no morph while the editor opens)
    inMeter.floorDb = param (wr::id::riderFloor);
    presetBox.text = proc.presets.currentName();
    presetBox.repaint();
    content.repaint();
}

void WraithEditor::updateHover()
{
    const wr::ui::Knob* t = nullptr;
    const wr::ui::Knob* all[] { &compression, &focus, &eqHigh, &eqLow, &stereo, &doublerMix, &filter, &reverbMix, &inGain, &outGain,
                                &riderSpeed, &riderAmount, &riderFloor };
    for (auto* k : all)
        if (k->isShowing() && (k->isMouseButtonDown() || k->isMouseOver())) t = k;
    if (dialog != nullptr || dropList != nullptr) t = nullptr;
    if (t != hovered) { hovered = t; content.repaint(); riderPanel.repaint(); }
}

// the captions as the reference writes them while a knob is hovered or dragged (filmed): compression / focus
// "default" at 0, else signed ("+8", "-16"); EQ and gains "1.5 dB"; stereo "100.0%"; the mixes "10%"; filter
// "9.8 kHz"; rider speed "3 ms", amount "70.0%", floor "-30.0 dB"
String WraithEditor::caption (const wr::ui::Knob& k) const
{
    const double v = k.getValue();
    if (&k != hovered)
    {
        if (&k == &compression) return "compression";
        if (&k == &focus) return "focus";
        if (&k == &eqHigh) return "high";
        if (&k == &eqLow) return "low";
        if (&k == &stereo) return "stereo";
        if (&k == &filter) return "filter";
        if (&k == &doublerMix || &k == &reverbMix) return "mix";
        if (&k == &riderSpeed) return "speed";
        if (&k == &riderAmount) return "amount";
        if (&k == &riderFloor) return "floor";
        return "gain";
    }
    if (&k == &compression || &k == &focus)
    {
        const int n = roundToInt (v);
        return n == 0 ? String ("default") : (n > 0 ? "+" : "") + String (n);
    }
    if (&k == &stereo || &k == &riderAmount) return String (v * 100.0, 1) + "%";
    if (&k == &doublerMix || &k == &reverbMix) return String (roundToInt (v * 100.0)) + "%";
    if (&k == &filter) return String (v / 1000.0, 1) + " kHz";
    if (&k == &riderSpeed) return String (roundToInt (v * 1000.0)) + " ms";
    return String (v, 1) + " dB";
}

//==============================================================================
void WraithEditor::setTestLevels (float inDb, float outDb, float inBarDb, float outBarDb)
{
    frozen = true;
    animate = false;
    updateFromParams();
    for (int c = 0; c < 2; ++c)
    {
        holdDb[c] = inDb;
        barDb[c] = inBarDb;
        holdDb[2 + c] = outDb;
        barDb[2 + c] = outBarDb;
    }
    stepMeters (0.0f);
}

void WraithEditor::timerCallback()
{
    if (getProperties().getWithDefault ("liveResize", false) && Time::getMillisecondCounter() - lastResizeMs > 150) endLiveResize();
    if (frozen) return;
    const double now = Time::getMillisecondCounterHiRes() * 0.001;
    const float dt = (float) jlimit (0.0, 0.2, now - lastTick);
    lastTick = now;
    // the processor taps the input before any gain: the input meter shows it after the input gain and the rider (as
    // the reference's manual says); the rider's gain is estimated here from the level and its controls (it aims the
    // level at the target's centre, -11.5 dB, by amount, above its floor, at a pace set by speed)
    const float gainDb = param (wr::id::inputGain);
    const float rawIn[2] { toDb (proc.inL.take()), toDb (proc.inR.take()) };
    const float pre = jmax (rawIn[0], rawIn[1]) + gainDb;
    const bool riderOn = param (wr::id::riderOn) >= 0.5f;
    float want = 0.0f;
    if (riderOn && pre > param (wr::id::riderFloor)) want = jlimit (-12.0f, 12.0f, param (wr::id::riderAmount) * (-11.5f - pre));
    else if (riderOn) want = riderDb;                       // below the floor it holds
    const float tau = 0.05f + 30.0f * param (wr::id::riderSpeed);
    riderDb += (want - riderDb) * (1.0f - std::exp (-dt / tau));
    if (! riderOn) riderDb = 0.0f;
    inGain.setRiderArc (riderOn, riderDb);

    const float fresh[4] { rawIn[0] + gainDb + riderDb, rawIn[1] + gainDb + riderDb, toDb (proc.outL.take()), toDb (proc.outR.take()) };
    for (int i = 0; i < 4; ++i)
    {
        // (the bar holds ~60 ms before it falls: the reference's starts falling 58 ms after a burst ends)
        if (fresh[i] >= barDb[i] - 0.5f) barHold[i] = 0.06f;
        else barHold[i] -= dt;
        barDb[i] = jmax (fresh[i], barHold[i] > 0.0f ? barDb[i] : barDb[i] - lk::meterReleaseDbPerSec * dt);
        holdDb[i] = jmax (holdDb[i], fresh[i]);
    }
    stepCompressionBars (dt);
    // room / plate morphs (drawReverb)
    const float morphTo = param (wr::id::reverbType) >= 0.5f ? 1.0f : 0.0f;
    if (! exactlyEqual (revMorph, morphTo))
    {
        revMorph += (morphTo - revMorph) * (1.0f - std::exp (-dt / 0.145f));
        if (std::abs (morphTo - revMorph) < 0.04f) revMorph = morphTo;          // (the last pixel)
        displays[3].repaint();
    }
    stepMeters (dt);
}

// The compression bars (measured on the reference, pink noise at -18 dBFS RMS, Compression swept): the bar's drop in
// design px is 1.9 per dB above a threshold of -25.4 - 0.23 x Compression dB (RMS, Focus included), at most 32 (-50:
// none; -25: 2.5; 0: 15; +25: 25; +50: 31; at Compression 0: -20 dBFS 12, -12 dBFS 27, -6 dBFS 32). It follows
// with ~45 ms up and ~30 ms down (each syllable of a sung-like signal: 124 -> 142 in ~80 ms, back in ~100 ms). The base marks the bar's peak
// and holds it through silence; after the bar has fallen, the next peak it reaches becomes the base (bursts of pink
// noise: the base kept a 0.25 s burst's peak, 154, through 2.5 s of silence, then took the next, lower burst's peak,
// 152, when that burst peaked; a sung-like signal: each syllable's peak, held through the pauses). Not matched: the
// reference now and then drops its base back to rest after a burst ends (after a 1 s burst, not after 0.5 or 3 s).
void WraithEditor::stepCompressionBars (float dt)
{
    const bool on = param (wr::id::characterOn) >= 0.5f;
    // the level the law is measured against: the RMS of what the character section hears, from the processor's
    // mean-square tap (the input, or the side-chain key when EXT is in use, which the input gain does not touch).
    // The tap sits before the input gain, the rider and Focus's EQ: the input gain is added here exactly; the rider's
    // gain is not known outside the DSP and is left out; Focus's EQ comes before the reference's detector (its bar
    // dropped 6 px more from Focus 0 to +50 on steady pink), so 0.06 dB per unit of Focus stands in for it
    const bool external = proc.sidechainExternal.load() && proc.getBusCount (true) > 1 && proc.getBus (true, 1)->isEnabled();
    // (a frame without a block keeps the last value, as hosts with long buffers call less often than this clock; after
    // 0.1 s without one the host has stopped)
    const float ms = proc.detectorIn.take();
    // (two averages in the power domain, 15 and 200 ms: on steady pink the reference's bar stays within half a pixel,
    // which needs the long one, yet between a sung signal's syllables it falls 8 dB in ~70 ms, which needs the short
    // one; the long one is used while the short one stays within 6 dB of it)
    if (ms >= 0.0f)
    {
        lastMeanSquare += (ms - lastMeanSquare) * (1.0f - std::exp (-dt / 0.015f));
        slowMeanSquare += (ms - slowMeanSquare) * (1.0f - std::exp (-dt / 0.2f));
        noBlockSeconds = 0.0f;
    }
    else if ((noBlockSeconds += dt) > 0.1f) lastMeanSquare = slowMeanSquare = 0.0f;
    auto db = [] (float p) { return p > 1.0e-12f ? 10.0f * std::log10 (p) : -120.0f; };
    const float fastDb = db (lastMeanSquare), slowDb = db (slowMeanSquare);
    const float level = (std::abs (fastDb - slowDb) > 6.0f ? fastDb : slowDb)
                        + (external ? 0.0f : param (wr::id::inputGain)) + 0.06f * param (wr::id::focus);    const float threshold = -25.4f - 0.23f * param (wr::id::compression);
    const float fresh = on && level > -90.0f ? jmin (32.0f, 1.9f * jmax (0.0f, level - threshold)) : 0.0f;
    // (the reference's bars answer ~25 ms later than ours would: its films show them a frame behind at every onset)
    barDelay[barDelayPos] = { Time::getMillisecondCounterHiRes(), fresh };
    barDelayPos = (barDelayPos + 1) % (int) std::size (barDelay);
    float target = fresh;
    double newest = -1.0;
    for (auto& d : barDelay)
        if (Time::getMillisecondCounterHiRes() - d.first >= 25.0 && d.first > newest) { newest = d.first; target = d.second; }
    const float prevBar = barPx, prevBase = basePx;
    barPx += (target - barPx) * (1.0f - std::exp (-dt / (target > barPx ? 0.045f : 0.03f)));
    if (barPx < basePx - 2.0f && ! barFell) { barFell = true; peakSinceFall = 0.0f; }
    if (barFell) peakSinceFall = jmax (peakSinceFall, barPx);
    if (barPx > prevBar + 0.05f) barRising = true;
    else if (barRising && barPx < prevBar - 0.05f)                // the bar has just peaked
    {
        barRising = false;
        if (barFell && peakSinceFall > 0.5f) { basePx = peakSinceFall; barFell = false; }
    }
    basePx = jmax (basePx, barPx);
    if (std::abs (barPx - prevBar) > 0.05f || std::abs (basePx - prevBase) > 0.05f) displays[0].repaint();
}

void WraithEditor::stepMeters (float dt)
{
    // the target fills while the level sits in it: fully from -13.5 to -9.5 dB, fading in from -17.5 (the
    // reference on a 5 dB/s ramp; a steady -6 dBFS burst leaves it empty, so it is gone from -6.5 up), following a
    // little behind (60 ms)
    const float l = jmax (barDb[0], barDb[1]);
    const float want = jlimit (0.0f, 1.0f, (l + 17.5f) / 4.0f) * jlimit (0.0f, 1.0f, (-6.5f - l) / 3.0f);
    targetFill = dt <= 0.0f ? want : targetFill + (want - targetFill) * (1.0f - std::exp (-dt / 0.06f));
    inMeter.setLevels (barDb, holdDb, holdDb, targetFill);
    outMeter.setLevels (barDb + 2, holdDb + 2, holdDb + 2, 0.0f);
}

//==============================================================================
// display drawings (design pixels; the shapes' places and sizes measured on the reference's 100 % captures at several
// settings), drawn as smooth strokes of our own: rounded joins and caps, a soft glow under each line
static void glowStroke (Graphics& g, const Path& p, float width, float lit)
{
    g.setColour (lk::pixel.withAlpha (0.06f * lit));
    g.strokePath (p, PathStrokeType (width * 3.6f, PathStrokeType::curved, PathStrokeType::rounded));
    g.setColour (lk::pixel.withAlpha (0.14f * lit));
    g.strokePath (p, PathStrokeType (width * 2.0f, PathStrokeType::curved, PathStrokeType::rounded));
    g.setColour (lk::pixel.withAlpha (lit));
    g.strokePath (p, PathStrokeType (width, PathStrokeType::curved, PathStrokeType::rounded));
}

void WraithEditor::drawCharacter (Graphics& g)
{
    const float lit = displays[0].litAmount();
    // compression (filmed on pink noise, level steps and a sung-like signal): per group a bar 12 px wide hanging from
    // y 120 (at rest only its top edge) whose foot follows the compression the section applies, and a base line 21 px
    // wide that marks the bar's last peak, 2.5 px under it
    for (float x0 : { 215.0f, 240.0f })
    {
        Path bar;
        if (barPx > 0.5f) bar.addRoundedRectangle (x0 + 7.0f, 122.0f, 8.0f, barPx, 2.0f);
        else { bar.startNewSubPath (x0 + 7.0f, 122.0f); bar.lineTo (x0 + 15.0f, 122.0f); }
        glowStroke (g, bar, 3.2f, lit);
        Path base;
        base.startNewSubPath (x0 + 2.0f, 128.5f + basePx);
        base.lineTo (x0 + 19.0f, 128.5f + basePx);
        glowStroke (g, base, 3.2f, lit);
    }
    // focus: a square about (383, 138): at -50 a small diamond, at 0 a diamond 20 px from its centre to a corner, from
    // there a rectangle turning upright and growing to 48 x 40 px between its corners at +50, dotted inside when nearly
    // there (filmed on a Focus ramp: the size changes continuously with each step)
    const float f = param (wr::id::focus);
    const Point<float> centre (383.0f, 138.0f);
    Path shape;
    float hx = 0.0f, hy = 0.0f, ca = 1.0f, sa = 0.0f;
    if (f <= 0.0f)
    {
        const float r = 4.0f * (1.0f + 4.0f * (f + 50.0f) / 50.0f);      // centre to a corner
        shape.startNewSubPath (centre.x, centre.y - r);
        shape.lineTo (centre.x + r, centre.y);
        shape.lineTo (centre.x, centre.y + r);
        shape.lineTo (centre.x - r, centre.y);
        shape.closeSubPath();
        shape = shape.createPathWithRoundedCorners (2.0f);
    }
    else
    {
        const float t = f / 50.0f, grow = std::pow (t, 1.5f);
        hx = 14.14f + 9.86f * grow;
        hy = 14.14f + 5.86f * grow;
        const float angle = MathConstants<float>::pi * 0.25f * (1.0f + t) - MathConstants<float>::halfPi;
        ca = std::cos (angle);
        sa = std::sin (angle);
        auto corner = [&] (float sx, float sy)
        {
            const float x = sx * hx, y = sy * hy;
            return centre + Point<float> (x * ca - y * sa, x * sa + y * ca);
        };
        shape.startNewSubPath (corner (-1, -1));
        shape.lineTo (corner (1, -1));
        shape.lineTo (corner (1, 1));
        shape.lineTo (corner (-1, 1));
        shape.closeSubPath();
        shape = shape.createPathWithRoundedCorners (3.0f);
    }
    glowStroke (g, shape, 3.2f, lit);
    if (f > 0.0f && f / 50.0f > 0.75f)                                   // the dots inside come in from about +38 to +50
    {
        g.setColour (lk::pixel.withAlpha (lit * jlimit (0.0f, 1.0f, (f / 50.0f - 0.75f) / 0.25f)));
        for (float y = -hy + 8.0f; y < hy - 4.0f; y += 8.0f)          // (on the shape's own grid, turning with it)
            for (float x = -hx + 8.0f; x < hx - 4.0f; x += 8.0f)
            {
                const auto p = centre + Point<float> (x * ca - y * sa, x * sa + y * ca);
                g.fillEllipse (p.x - 1.6f, p.y - 1.6f, 3.2f, 3.2f);
            }
    }
}

void WraithEditor::drawEq (Graphics& g)
{
    // the shelves: the low level from x 518, the high level to x 576, 20 px for 12 dB about y 138, joined to the middle
    // (x 542 ... 552) by smooth S-curves over x 530 ... 541 and 553 ... 564
    const float yl = 138.0f - param (wr::id::eqLow) * (20.0f / 12.0f), yh = 138.0f - param (wr::id::eqHigh) * (20.0f / 12.0f);
    Path p;
    p.startNewSubPath (520.0f, yl);
    p.lineTo (530.0f, yl);
    p.cubicTo (536.5f, yl, 535.5f, 138.0f, 542.0f, 138.0f);
    p.lineTo (553.0f, 138.0f);
    p.cubicTo (559.5f, 138.0f, 558.5f, yh, 565.0f, yh);
    p.lineTo (575.0f, yh);
    glowStroke (g, p, 3.4f, displays[1].litAmount());
}

void WraithEditor::drawDoubler (Graphics& g)
{
    // two voices, each an ellipse 30 x 44 px about x 676, y 138, apart by 2 x 14.7 px at full Stereo; Mix and audio do
    // not move them (filmed)
    const float d = 14.7f * param (wr::id::doublerStereo);
    Path p;
    for (float cx : { 676.0f - d, 676.0f + d })
        p.addEllipse (cx - 13.5f, 117.5f, 27.0f, 41.0f);
    glowStroke (g, p, 3.0f, displays[2].litAmount());
}

void WraithEditor::drawReverb (Graphics& g)
{
    // a right triangle: an upright from y 114, a foot at y 154 ... 157, and the slope to the foot's end: room from x 780
    // to 828, plate from x 771 to 837. Between the two it morphs (filmed on a click of room / plate: easing out with a
    // time constant of ~145 ms, done in ~450 ms)
    const float m = revMorph;
    const float x0 = 780.0f + (771.0f - 780.0f) * m + 2.0f, x1 = 828.0f + (837.0f - 828.0f) * m - 2.0f;
    Path tri;
    tri.startNewSubPath (x0, 116.0f);
    tri.lineTo (x0, 156.0f);
    tri.lineTo (x1, 156.0f);
    tri.closeSubPath();
    tri = tri.createPathWithRoundedCorners (2.5f);
    const float lit = displays[3].litAmount();
    g.setGradientFill (ColourGradient (lk::pixel.withAlpha (0.16f * lit), x0, 156.0f, lk::pixel.withAlpha (0.02f * lit), x1, 116.0f, false));
    g.fillPath (tri);
    glowStroke (g, tri, 3.4f, lit);
}
//==============================================================================
void WraithEditor::Content::paint (Graphics& g)
{
    g.fillAll (theme::bg);
    const float dpx = theme::pixelScale (g, *this);
    if (ed.faceplate.isNull() || (std::abs (dpx - ed.faceplateScale) > 0.001f && ! theme::liveResizing (*this)))
    {
        ed.faceplate = wr::ui::renderFaceplate (dpx);
        ed.faceplateScale = dpx;
    }
    g.drawImage (ed.faceplate, Rectangle<float> (0.0f, lk::topBarH, designW, designH - lk::topBarH));
    ed.paintTopBar (g);
    ed.paintCaptions (g);
}

void WraithEditor::Content::mouseDown (const MouseEvent&)
{
    if (ed.dropList != nullptr) ed.closePopups();
}

void WraithEditor::paintTopBar (Graphics& g)
{
    g.setColour (theme::topBar);
    g.fillRect (0.0f, 0.0f, designW, lk::topBarH);
    g.setColour (theme::text);
    g.setFont (theme::font (12.0f));
    theme::textAt (g, "Preset", 136.0f, 19.5f);
    theme::textAt (g, "Sidechain", 612.0f, 19.5f);
    theme::textAt (g, "UI Scale", 960.0f, 19.5f, Justification::right);
}

void WraithEditor::paintCaptions (Graphics& g)
{
    g.setFont (theme::font (11.5f));
    // the name dim (faint while the section is off), the value in gold while it shows
    auto label = [&] (const wr::ui::Knob& k, float x, float y)
    {
        g.setColour (&k == hovered ? lk::value : sectionOn (k) ? lk::label : lk::labelOff);
        wr::ui::heavyText (g, caption (k), x, y, Justification::horizontallyCentred, 0.3f);
    };
    label (compression, lk::compressionKnob.x, lk::knobLabelY);
    label (focus, lk::focusKnob.x, lk::knobLabelY);
    label (eqHigh, smallX (lk::eq), lk::upperLabelY);
    label (eqLow, smallX (lk::eq), lk::knobLabelY);
    label (stereo, smallX (lk::doubler), lk::upperLabelY);
    label (doublerMix, smallX (lk::doubler), lk::knobLabelY);
    label (filter, smallX (lk::reverb), lk::upperLabelY);
    label (reverbMix, smallX (lk::reverb), lk::knobLabelY);
    label (inGain, lk::gainKnob[0].x, lk::knobLabelY);
    label (outGain, lk::gainKnob[1].x, lk::knobLabelY);
}

//==============================================================================
bool WraithEditor::RiderPanel::hitTest (int x, int y)
{
    // the input section under it stays live (its meter, rider button and gain knob are above the panel)
    const Point<float> p ((float) x, (float) y);
    if (p.y < lk::topBarH) return false;
    return ! Rectangle<float> (lk::plateX0[lk::input], lk::plateTop, lk::plateX1[lk::input] - lk::plateX0[lk::input], lk::plateBottom - lk::plateTop).contains (p);
}

void WraithEditor::RiderPanel::mouseDown (const MouseEvent&) {}

// a click outside the rider panel closes it (filmed), whichever component it reaches
void WraithEditor::clickedAnywhere (const MouseEvent& e)
{
    const auto p = e.getEventRelativeTo (&content).position;
    if (! riderOpen) return;
    if (p.y >= lk::topBarH && ! lk::riderPanel.r().contains (p)) setRiderPanel (false);
}

void WraithEditor::RiderPanel::paint (Graphics& g)
{
    const auto inputPlate = Rectangle<float> (lk::plateX0[lk::input] - 1.0f, lk::plateTop - 1.0f,
                                              lk::plateX1[lk::input] - lk::plateX0[lk::input] + 2.0f, lk::plateBottom - lk::plateTop + 2.0f);
    {
        Graphics::ScopedSaveState s (g);
        g.excludeClipRegion (inputPlate.getSmallestIntegerContainer());
        g.setColour (theme::bg.withAlpha (lk::riderDim));
        g.fillRect (Rectangle<float> (0.0f, lk::topBarH, designW, designH - lk::topBarH));
        g.setColour (theme::card);
        g.fillRoundedRectangle (lk::riderPanel.r(), 12.0f);
    }
    g.setColour (theme::lineLight);
    g.drawRoundedRectangle (lk::riderPanel.r().reduced (0.5f), 12.0f, 1.0f);
    g.setFont (theme::font (11.5f));
    const wr::ui::Knob* knobs[3] { &ed.riderSpeed, &ed.riderAmount, &ed.riderFloor };
    for (int i = 0; i < 3; ++i)
    {
        g.setColour (knobs[i] == ed.hovered ? lk::value : lk::label);
        theme::textAt (g, ed.caption (*knobs[i]), lk::riderKnobX, lk::riderLabelY[i], Justification::horizontallyCentred);
    }
}

Component* WraithEditor::componentAtDesign (Point<float> p)
{
    return content.getComponentAt (p.roundToInt());
}

//==============================================================================
void WraithEditor::closePopups()
{
    if (dropList != nullptr) content.removeChildComponent (dropList.get());
    dropList.reset();
    presetBox.open = scaleBox.open = false;
    presetBox.repaint(); scaleBox.repaint();
}

void WraithEditor::showPresetList()
{
    closePopups();
    const auto all = proc.presets.list();
    std::vector<orrery::DropList::Item> items { { "factory", true } };
    std::vector<int> map { -1 };
    for (int i = 0; i < (int) all.size(); ++i)
        if (all[(size_t) i].factory) { items.push_back ({ all[(size_t) i].name, false, all[(size_t) i].name == proc.presets.currentName() }); map.push_back (i); }
    items.push_back ({ "user", true }); map.push_back (-1);
    bool anyUser = false;
    for (int i = 0; i < (int) all.size(); ++i)
        if (! all[(size_t) i].factory) { items.push_back ({ all[(size_t) i].name }); map.push_back (i); anyUser = true; }
    if (! anyUser) { items.push_back ({ "-" }); map.push_back (-1); }
    dropList = std::make_unique<orrery::DropList>();
    dropList->setItems (items, 24.0f, true);
    dropList->onPick = [this, all, map] (int row)
    {
        const int idx = map[(size_t) row];
        if (idx >= 0) { proc.presets.load (all[(size_t) idx]); presetBox.text = proc.presets.currentName(); }
        closePopups();
        updateFromParams();
    };
    dropList->setBounds (80, 27, 270, jmin ((int) (24.0f * (float) items.size()) - 2, (int) designH - 30));
    presetBox.open = true;
    content.addAndMakeVisible (*dropList);
}

void WraithEditor::showScaleList()
{
    closePopups();
    std::vector<orrery::DropList::Item> items;
    for (float s : scales) items.push_back ({ String (roundToInt (s * 100.0f)) + "%", false, std::abs (s - scale) < 0.01f });
    dropList = std::make_unique<orrery::DropList>();
    dropList->setItems (items, 24.0f, false);
    dropList->onPick = [safe = Component::SafePointer<WraithEditor> (this)] (int row)
    {
        if (safe == nullptr) return;
        const float s = scales[row];
        safe->closePopups();
        MessageManager::callAsync ([safe, s] { if (safe != nullptr) safe->setUiScale (s); });
    };
    dropList->setBounds (966, 27, 66, (int) (24.0f * (float) items.size()) + 1);
    scaleBox.open = true;
    content.addAndMakeVisible (*dropList);
}

void WraithEditor::showDialog (std::unique_ptr<Component> d)
{
    closePopups();
    if (dialog != nullptr) { content.removeChildComponent (dialog.get()); dialog.reset(); }
    d->setBounds (0, 0, (int) std::ceil (designW), (int) std::ceil (designH));
    if (auto* dl = dynamic_cast<orrery::Dialog*> (d.get()))
        dl->onClose = [safe = Component::SafePointer<WraithEditor> (this)]
        {
            MessageManager::callAsync ([safe] { if (safe != nullptr) { safe->content.removeChildComponent (safe->dialog.get()); safe->dialog.reset(); } });
        };
    content.addAndMakeVisible (*d);
    dialog = std::move (d);
}

void WraithEditor::showSavePreset()
{
    auto d = std::make_unique<orrery::SaveDialog> (proc.presets.currentName(), [this] (const String& n) { return proc.presets.save (n); },
                                                   [this] { presetBox.text = proc.presets.currentName(); presetBox.repaint(); });
    d->moveBy ((designH - 359.5f) * 0.5f);         // centred in this taller window
    auto* raw = d.get();
    showDialog (std::move (d));
    raw->focusName();
}

// the logo's menu (as the suite's other plug-ins): version, About, repository, issues, licence
void WraithEditor::showAboutMenu()
{
    if (dropList != nullptr) { closePopups(); return; }
    const String version = JucePlugin_VersionString;
    dropList = std::make_unique<orrery::DropList>();
    dropList->setItems ({ { "Wraith v" + version, true }, { "About Wraith" }, { "Orrery Suite on GitHub" },
                          { "Report an Issue" }, { "License (AGPL-3.0)" } }, 24.0f, true);
    dropList->onPick = [safe = Component::SafePointer<WraithEditor> (this), version] (int row)
    {
        if (safe == nullptr) return;
        safe->closePopups();
        if (row == 1)
        {
            const auto wrapper = safe->proc.wrapperType;
            const String format = AudioProcessor::getWrapperTypeDescription (wrapper);
            auto about = std::make_unique<orrery::InfoDialog> ("about Wraith", std::vector<std::pair<String, String>> {
                { "Version", version + (wrapper == AudioProcessor::wrapperType_Undefined ? String() : " (" + format + ")") },
                { {}, {} },
                { "What it is", "An open-source vocal chain modelled on and measured against Cradle's The Spirit" },
                { "Part of", "Orrery Suite: open-source recreations, null-tested against the originals" },
                { "License", "Open source under the GNU Affero General Public License v3" },
                { "Built with", "JUCE, the VST3 SDK and CLAP; Instrument Sans (SIL OFL). Their licenses come with it" },
                { "Source", repository.fromFirstOccurrenceOf ("https://", false, false) },
                { {}, {} },
                { "Note", "An independent project, not affiliated with or endorsed by Cradle. The Spirit is a trademark of its owner." } });
            if (auto* dl = dynamic_cast<orrery::Dialog*> (about.get())) dl->box = dl->box.translated ((designW - 888.0f) * 0.5f, 0.0f);
            safe->showDialog (std::move (about));
        }
        else if (row == 2) URL (repository).launchInDefaultBrowser();
        else if (row == 3) URL (repository + "/issues/new/choose").launchInDefaultBrowser();
        else if (row == 4) URL (repository + "/blob/main/LICENSE").launchInDefaultBrowser();
    };
    dropList->setBounds (4, 27, 214, 24 * 5 - 2);
    content.addAndMakeVisible (*dropList);
}
