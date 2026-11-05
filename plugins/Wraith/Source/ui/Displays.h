#pragma once
#include <juce_gui_basics/juce_gui_basics.h>

// The lit displays above the knobs and the two level meters. Everything inside a display is drawn as smooth strokes
// of our own (rounded, with a soft glow), in light gold on the screen's well, at the places and sizes measured on the
// reference. A display whose section is off shows its screen
// unlit: the drawing and the gold edge fade out linearly over 120 ms (and in again when it is on).
//
// How the drawings move (RefCapture films of the reference with parameters automated from the audio thread, on
// silence, pink noise level steps and bursts, and a sung-like signal; the drawings themselves are the editor's):
//   - a setting changes its drawing at once, the next frame (Focus, EQ gains, Doubler Stereo); Compression, Reverb
//     Mix and Filter and Doubler Mix draw nothing; room / plate morphs the triangle, easing out
//     with a time constant of ~145 ms (9 px, done in ~450 ms);
//   - audio moves only the character display's compression bars: the bar drops 1.9 px per dB over -25.4 - 0.23 x
//     Compression dB (RMS of what the section hears, plus 0.06 dB per unit of Focus), at most 32 px, following ~45 ms
//     up and ~30 ms down after a two-speed level average (200 ms, or 15 ms when that is 6 dB away); the base under it keeps the bar's
//     last peak through silence until the bar peaks again after a fall. The focus shape, EQ curve, doubler ellipses
//     and reverb triangle do not react to audio, and nothing moves in silence.
namespace wr::ui
{
class SectionDisplay : public juce::Component, private juce::Timer
{
public:
    SectionDisplay();
    void paint (juce::Graphics&) override;
    void setLit (bool on, bool animate);
    float litAmount() const { return lit; }
    // the display's drawing, in the editor's design pixels (the component's origin is subtracted for you)
    std::function<void (juce::Graphics&)> drawArt;
    juce::Point<float> origin;          // the display's top-left in design pixels

private:
    void timerCallback() override;
    float lit = 1.0f, target = 1.0f;
    double fadeStart = 0.0;
    float fadeFrom = 1.0f;
};

// The input / output meter: two readouts (the highest peak since the editor opened or the last click, "-6.0",
// "-inf"), a gold-to-pearl bar per channel with a held-peak marker, and (input only) the gold target bracket that
// fills while the level sits in it; the rider's floor as a pearl line while its knob is dragged.
class LevelMeter : public juce::Component
{
public:
    explicit LevelMeter (bool input);
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
    void setLevels (const float barDb[2], const float holdDb[2], const float maxDb[2], float targetFill);
    float floorDb = -30.0f;
    bool showFloor = false;
    juce::Point<float> origin;
    std::function<void()> onResetHold;

private:
    bool isInput;
    float bar[2] { -200.0f, -200.0f }, hold[2] { -200.0f, -200.0f }, peakMax[2] { -200.0f, -200.0f };
    float fill = 0.0f;
};
}
