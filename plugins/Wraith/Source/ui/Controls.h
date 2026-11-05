#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include <functional>

// Wraith's controls, drawn in the suite's own look (shared/ui/Theme.h) at their measured sizes. Mouse behaviour as
// filmed on the reference
// (RefCapture drag scripts at 100 %):
//   - knobs: vertical drag, 250 design px for the whole range (0.4 % per px: compression 0 -> +16 in 40 px, EQ High
//     +2.88 dB in 30 px, rider amount +0.16 in 40 px, floor +3.84 dB in 30 px), clamped at the ends;
//   - Shift: velocity mode with the cursor hidden (1 px moves change nothing, as JUCE's default threshold);
//   - double-click and Alt-click: the parameter's default (compression +16 -> 0; focus 8 -> 0, the host default,
//     not the preset's); Ctrl-click does nothing;
//   - while the mouse is over a knob or drags it, its label shows the value (Captions in the editor).
namespace wr::ui
{
// Every knob is theme::drawKnob at its measured centre and radius: the value's gold arc (from the centre on the
// bipolar ones: compression, focus, the EQ gains, the gains), a pearl pointer; the arc fades to faint while the
// knob's section is switched off.
class Knob : public juce::Slider
{
public:
    enum class Kind { groove, gain, rider };      // the reference's ridged knobs, its gain knobs, the rider panel's
    explicit Knob (Kind);
    void paint (juce::Graphics&) override;
    void setDefault (double v) { setDoubleClickReturnValue (true, v, juce::ModifierKeys::altModifier); }

    // the input gain knob shows what the rider adds, as a pearl arc on from the knob's own value (dB, while on)
    void setRiderArc (bool on, float gainDb);
    void setSectionOn (bool on) { if (on != sectionOn) { sectionOn = on; repaint(); } }
    bool hitTest (int x, int y) override;
    float radius = 20.0f;              // design px; the component is an even square round it (whole pixels at 100 %)

private:
    Kind kind;
    bool riderOn = false, sectionOn = true;
    float riderDb = 0.0f;
};

// The power button above a section's display: filled gold with a dark power symbol while the section runs, an
// outline with a faint symbol while it is off, lighter under the mouse (filmed: at once, no fade). Acts on release
// over it.
class PowerPill : public juce::Component
{
public:
    PowerPill();
    void paint (juce::Graphics&) override;
    void mouseUp (const juce::MouseEvent& e) override { if (getLocalBounds().contains (e.getPosition()) && onClick) onClick(); }
    bool active = true;
    std::function<void()> onClick;
};

// The input section's "rider | >" pill: "rider" toggles the rider (on: its half filled gold, dark text), ">" opens
// the rider panel (open: its half filled gold); under the mouse a half's text brightens.
class RiderPill : public juce::Component
{
public:
    RiderPill();
    void paint (juce::Graphics&) override;
    void mouseMove (const juce::MouseEvent& e) override { setHover (partAt (e.x)); }
    void mouseExit (const juce::MouseEvent&) override { setHover (-1); }
    void mouseUp (const juce::MouseEvent&) override;
    bool riderOn = false, panelOpen = false;
    std::function<void()> onRider, onArrow;
    float splitX = 58.5f;                    // local x of the line between the two parts
private:
    int partAt (int x) const { return (float) x < splitX ? 0 : 1; }
    void setHover (int p) { if (p != hover) { hover = p; repaint(); } }
    int hover = -1;
};

// The reverb's "room | plate" pill: the chosen half filled gold with dark text, the other an outline with dim text
// that brightens under the mouse.
class RoomPlate : public juce::Component
{
public:
    RoomPlate();
    void paint (juce::Graphics&) override;
    void mouseMove (const juce::MouseEvent& e) override { setHover (partAt (e.x)); }
    void mouseExit (const juce::MouseEvent&) override { setHover (-1); }
    void mouseUp (const juce::MouseEvent&) override;
    int selected = 0;                        // 0 room, 1 plate
    std::function<void (int)> onChange;
    float splitX = 42.5f;
private:
    int partAt (int x) const { return (float) x < splitX ? 0 : 1; }
    void setHover (int p) { if (p != hover) { hover = p; repaint(); } }
    int hover = -1;
};

// A toggle's body (a stadium in r): its well and outline, and the parts of it that are on filled gold (left of
// splitX when `left`, right of it when `right`; a plain toggle passes both or neither). Returns the stadium.
juce::Rectangle<float> paintToggle (juce::Graphics&, juce::Rectangle<float> r, bool left, bool right, float splitX, bool hover);
void paintPowerIcon (juce::Graphics&, juce::Point<float> c, float r, juce::Colour);

// one line of text as theme::textAt draws it, made a little heavier (the reference's lettering is a medium weight;
// the suite's bundled face is the regular one): the glyph outlines filled and stroked "weight" px wide
void heavyText (juce::Graphics&, const juce::String&, float x, float baseline, juce::Justification, float weight = 0.35f);
}
