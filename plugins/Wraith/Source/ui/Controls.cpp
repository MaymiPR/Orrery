#include "Controls.h"
#include "Theme.h"
#include "shared/ui/Theme.h"
#include "shared/ui/Widgets.h"

using namespace juce;
namespace theme = orrery::theme;

namespace wr::ui
{
using namespace wr::look;

//==============================================================================
Knob::Knob (Kind k) : kind (k)
{
    orrery::noFocus (*this);
    setSliderStyle (Slider::RotaryVerticalDrag);
    setTextBoxStyle (Slider::NoTextBox, false, 0, 0);
    setRotaryParameters (MathConstants<float>::pi * 1.25f, MathConstants<float>::pi * 2.75f, true);
    setMouseDragSensitivity (250);
    setVelocityBasedMode (false);
    setVelocityModeParameters (1.0, 1, 0.0, true, ModifierKeys::shiftModifier);
    setPaintingIsUnclipped (true);
}

bool Knob::hitTest (int x, int y)
{
    const auto c = getLocalBounds().toFloat().getCentre();
    return c.getDistanceFrom ({ (float) x, (float) y }) <= radius;
}

void Knob::setRiderArc (bool on, float gainDb)
{
    if (on == riderOn && std::abs (gainDb - riderDb) < 0.01f) return;
    riderOn = on;
    riderDb = gainDb;
    repaint();
}

void Knob::paint (Graphics& g)
{
    const auto c = getLocalBounds().toFloat().getCentre();
    const float R = radius;
    const auto& rp = getRotaryParameters();
    auto angleOf = [this, &rp] (double v)
    {
        return rp.startAngleRadians + (float) valueToProportionOfLength (v) * (rp.endAngleRadians - rp.startAngleRadians);
    };
    const float angle = angleOf (getValue());
    // a range across zero is bipolar: its arc starts at zero (the top)
    const float from = getMinimum() < 0.0 && getMaximum() > 0.0 ? angleOf (0.0) : rp.startAngleRadians;
    theme::drawKnob (g, Rectangle<float> (2.0f * R, 2.0f * R).withCentre (c), angle, rp.startAngleRadians, rp.endAngleRadians, from, sectionOn);

    // the input gain: while the rider is on, the arc of what it adds, in pearl over the value's ring
    if (kind == Kind::gain && riderOn && std::abs (riderDb) > 0.05f)
    {
        const float to = angleOf (jlimit (getMinimum(), getMaximum(), getValue() + (double) riderDb));
        const float arcW = jlimit (1.5f, 4.0f, R * 0.09f), arcR = R - arcW * 0.5f;     // theme::drawKnob's ring
        Path arc;
        arc.addCentredArc (c.x, c.y, arcR, arcR, 0.0f, jmin (angle, to), jmax (angle, to), true);
        g.setColour (theme::pearl.withAlpha (0.9f));
        g.strokePath (arc, PathStrokeType (arcW, PathStrokeType::curved, PathStrokeType::butt));
    }
}

void heavyText (Graphics& g, const String& s, float x, float baseline, Justification j, float weight)
{
    GlyphArrangement ga;
    ga.addLineOfText (g.getCurrentFont(), s, 0.0f, 0.0f);
    const float w = ga.getBoundingBox (0, -1, false).getRight();
    const float dx = j.testFlags (Justification::right) ? x - w : j.testFlags (Justification::horizontallyCentred) ? x - w * 0.5f : x;
    Path p;
    ga.createPath (p);
    p.applyTransform (AffineTransform::translation (dx, baseline));
    g.fillPath (p);
    g.strokePath (p, PathStrokeType (weight));
}

//==============================================================================
void paintPowerIcon (Graphics& g, Point<float> c, float r, Colour col)
{
    Path p;
    p.addCentredArc (c.x, c.y, r, r, 0.0f, 0.62f, MathConstants<float>::twoPi - 0.62f, true);
    p.startNewSubPath (c.x, c.y - r - 1.2f);
    p.lineTo (c.x, c.y - r * 0.2f);
    g.setColour (col);
    g.strokePath (p, PathStrokeType (1.4f, PathStrokeType::curved, PathStrokeType::rounded));
}

// the toggles in the suite's look, at the pills' measured sizes: a stadium well with a light outline; the parts that
// are on filled gold inside it (lighter under the mouse)
Rectangle<float> paintToggle (Graphics& g, Rectangle<float> r, bool left, bool right, float splitX, bool hover)
{
    const auto body = r.getHeight() > 24.0f ? r.reduced (0.5f) : r.reduced (0.5f, 1.0f);
    const float radius = body.getHeight() * 0.5f;
    g.setColour (theme::well);
    g.fillRoundedRectangle (body, radius);
    if (left || right)
    {
        Graphics::ScopedSaveState s (g);
        const auto in = body.reduced (1.5f);
        Path clip;
        clip.addRoundedRectangle (in, in.getHeight() * 0.5f);
        g.reduceClipRegion (clip);
        auto part = in;
        if (! left) part = part.withLeft (splitX + 0.5f);
        if (! right) part = part.withRight (splitX - 0.5f);
        g.setColour (hover ? theme::goldLight : theme::gold);
        g.fillRect (part);
    }
    g.setColour (left || right ? theme::goldDeep.interpolatedWith (theme::gold, 0.5f) : hover ? theme::letteringFaint : theme::lineLight);
    g.drawRoundedRectangle (body.reduced (0.5f), radius - 0.5f, 1.0f);
    return body;
}

PowerPill::PowerPill() { orrery::noFocus (*this); setRepaintsOnMouseActivity (true); }

void PowerPill::paint (Graphics& g)
{
    const bool over = isMouseOver();
    const auto body = paintToggle (g, getLocalBounds().toFloat(), active, active, 0.0f, over);
    const auto col = active ? theme::well : over ? theme::lettering : theme::letteringFaint;
    paintPowerIcon (g, body.getCentre().translated (0.0f, 0.4f), 5.0f, col);
}

//==============================================================================
RiderPill::RiderPill() { orrery::noFocus (*this); }

void RiderPill::mouseUp (const MouseEvent& e)
{
    if (! getLocalBounds().contains (e.getPosition())) return;
    if (partAt (e.x) == 0) { if (onRider) onRider(); }
    else if (onArrow) onArrow();
}

void RiderPill::paint (Graphics& g)
{
    const auto in = paintToggle (g, getLocalBounds().toFloat(), riderOn, panelOpen, splitX, false);
    if (! riderOn && ! panelOpen)
    {
        g.setColour (theme::lineLight);
        g.fillRect (splitX - 0.5f, in.getY() + 5.0f, 1.0f, in.getHeight() - 10.0f);
    }
    g.setFont (theme::font (11.5f));
    auto ink = [this] (bool on, int part) { return on ? theme::well : hover == part ? theme::lettering : theme::letteringDim; };
    g.setColour (ink (riderOn, 0));
    heavyText (g, "rider", (in.getX() + splitX) * 0.5f + 2.0f, 17.5f, Justification::horizontallyCentred);
    g.setColour (ink (panelOpen, 1));
    heavyText (g, ">", (splitX + in.getRight()) * 0.5f - 2.0f, 17.5f, Justification::horizontallyCentred);
}

//==============================================================================
RoomPlate::RoomPlate() { orrery::noFocus (*this); }

void RoomPlate::mouseUp (const MouseEvent& e)
{
    if (! getLocalBounds().contains (e.getPosition())) return;
    const int p = partAt (e.x);
    if (p != selected && onChange) onChange (p);
}

void RoomPlate::paint (Graphics& g)
{
    const auto in = paintToggle (g, getLocalBounds().toFloat(), selected == 0, selected == 1, splitX, false);
    g.setFont (theme::font (11.5f));
    const char* names[2] { "room", "plate" };
    for (int i = 0; i < 2; ++i)
    {
        const bool sel = i == selected;
        g.setColour (sel ? theme::well : hover == i ? theme::lettering : theme::letteringDim);
        const float cx = i == 0 ? (in.getX() + splitX) * 0.5f + 1.5f : (splitX + in.getRight()) * 0.5f - 1.0f;
        heavyText (g, names[i], cx, 12.8f, Justification::horizontallyCentred);
    }
}
}
