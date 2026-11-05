#pragma once
#include <juce_gui_basics/juce_gui_basics.h>

// Orrery Suite's own look, the same on every editor: true black behind, deep violet-black cards and wells, lavender-white
// lettering, the sun's gold for values and meters, the crescent's pearl for pointers and selections, the mark in its
// violet
// (docs/branding/colours.json, docs/branding/orrery-icon.svg). The layouts keep each plug-in's measured positions and
// sizes; everything drawn on them comes from here.
namespace orrery::theme
{
// the palette
inline const juce::Colour bg { 0xff000000 },              // behind everything
                          card { 0xff0c0a12 },            // a panel, the plate
                          raised { 0xff15111f },          // a control's body
                          raisedTop { 0xff2a2240 },       // its lit top
                          well { 0xff050408 },            // a slot, a meter's trough, a value box
                          line { 0xff2a2338 },            // frames and borders
                          lineLight { 0xff4a4064 },       // a frame under the mouse, a box's outline
                          lettering { 0xffece8f6 },       // names and values
                          letteringDim { 0xffa79fc0 },    // labels
                          letteringFaint { 0xff625a7e },  // scales, ticks, a bypassed section
                          gold { 0xffe9c46a },            // the value: arcs, meters, readouts, power buttons
                          goldLight { 0xfff3d894 },
                          goldDeep { 0xff8a6a2c },        // a meter's low end
                          violet { 0xffb07cff },          // the mark, the plates' skies
                          violetLight { 0xffc49dff },
                          violetDeep { 0xff5b3a99 },
                          pearl { 0xfff1ecff },           // the hand: pointers, the selection, a meter's top
                          clipRed { 0xffff5a6a };         // clipping

// the names the editors use, in the palette's colours
inline const juce::Colour topBar { 0xff07060b };
inline const juce::Colour panel { bg };
inline const juce::Colour text { lettering };              // top bar labels, boxes
inline const juce::Colour boxFill { raised };
inline const juce::Colour boxLine { lineLight };            // preset / scale boxes, gear, mark
inline const juce::Colour mint { gold };                  // readouts, labels, power buttons, peak marker
inline const juce::Colour ledGreen { goldDeep };
inline const juce::Colour target { gold };                // target brackets
inline const juce::Colour targetLine { gold };
inline const juce::Colour targetFill { gold };            // a target the level sits in: solid
inline const juce::Colour divider { line };
inline const juce::Colour outline { lineLight };            // main panel outline
inline const juce::Colour plateText { letteringDim };       // labels on the plate, bypassed amount text
inline const juce::Colour dimLabel { letteringFaint };      // labels, readouts, brackets of a bypassed section
inline const juce::Colour clip { clipRed };                 // peak readout over 0 dBFS
inline const juce::Colour menuCaption { goldLight };      // FACTORY / USER captions in the preset list

// The bundled typeface (Instrument Sans, SIL OFL).
juce::Font font (float emPx);

// draws one line of text at a fractional position: x is the left edge (or the right edge / centre with
// Justification::right / horizontallyCentred), y the baseline (Graphics::drawSingleLineText rounds both to ints)
void textAt (juce::Graphics&, const juce::String&, float x, float baseline,
           juce::Justification j = juce::Justification::left);

// device pixels per design pixel when painting component c: the context's own factor (display scale), or the
// component's transforms up the hierarchy (UI Scale), whichever is larger (snapshots report only the latter)
inline float pixelScale (juce::Graphics& g, const juce::Component& c)
{
    return juce::jmax (g.getInternalContext().getPhysicalPixelScaleFactor(), juce::Component::getApproximateScaleFactorForComponent (&c));
}

// true while the editor is being resized (its "liveResize" property): the per-scale images (glass, plate, shadows)
// are then drawn stretched from the last size instead of rendered again, and re-rendered once it settles
inline bool liveResizing (const juce::Component& c)
{
    for (auto* p = &c; p != nullptr; p = p->getParentComponent())
        if (p->getProperties().getWithDefault ("liveResize", false)) return true;
    return false;
}

// Meters: the scale of the original's LED ladder (LED k, 0 at the bottom, 39 at the top, at -58.5 + 1.5 k dB, measured
// with a level ramp) is kept as the bar's scale.
inline constexpr int numLeds = 40;
inline float ledThresholdDb (int k) { return -58.5f + 1.5f * (float) k; }
inline float meterFraction (float db) { return juce::jlimit (0.0f, 1.0f, (db + 60.0f) / 60.0f); }   // -60 .. 0 dBFS

// a card: the panel colour, a 1 px border
inline void drawCard (juce::Graphics& g, juce::Rectangle<float> r, float radius = 8.0f)
{
    g.setColour (card);
    g.fillRoundedRectangle (r, radius);
    g.setColour (line);
    g.drawRoundedRectangle (r.reduced (0.5f), radius, 1.0f);
}

// a well: a slot, a trough, a value box
inline void drawWell (juce::Graphics& g, juce::Rectangle<float> r, float radius = 2.0f)
{
    g.setColour (well);
    g.fillRoundedRectangle (r, radius);
    g.setColour (line.withAlpha (0.9f));
    g.drawRoundedRectangle (r.reduced (0.5f), radius, 1.0f);
}

// the gold-to-pearl fill of a meter, along its length
inline juce::ColourGradient meterGradient (juce::Rectangle<float> r, bool vertical)
{
    juce::ColourGradient cg = vertical ? juce::ColourGradient (goldDeep, 0.0f, r.getBottom(), pearl, 0.0f, r.getY(), false)
                                       : juce::ColourGradient (goldDeep, r.getX(), 0.0f, pearl, r.getRight(), 0.0f, false);
    cg.addColour (0.55, gold);
    return cg;
}

// a meter bar: its well, filled to `fraction` (0 .. 1) from the bottom (vertical) or the left, and an optional peak
// marker (a pearl line at `peak`, 0 .. 1; negative: none)
inline void drawMeterBar (juce::Graphics& g, juce::Rectangle<float> r, float fraction, bool vertical, float peak = -1.0f)
{
    drawWell (g, r, juce::jmin (2.0f, juce::jmin (r.getWidth(), r.getHeight()) * 0.5f));
    const auto inner = r.reduced (1.0f);
    fraction = juce::jlimit (0.0f, 1.0f, fraction);
    if (fraction > 0.0f)
    {
        const auto lit = vertical ? inner.withTop (inner.getBottom() - inner.getHeight() * fraction) : inner.withWidth (inner.getWidth() * fraction);
        juce::Graphics::ScopedSaveState ss (g);
        g.reduceClipRegion (lit.getSmallestIntegerContainer());
        g.setGradientFill (meterGradient (inner, vertical));
        g.fillRoundedRectangle (inner, 1.0f);
    }
    if (peak >= 0.0f)
    {
        peak = juce::jlimit (0.0f, 1.0f, peak);
        g.setColour (pearl);
        if (vertical) g.fillRect (inner.getX(), inner.getBottom() - inner.getHeight() * peak - 0.5f, inner.getWidth(), 1.0f);
        else          g.fillRect (inner.getX() + inner.getWidth() * peak - 0.5f, inner.getY(), 1.0f, inner.getHeight());
    }
}

// a knob filling the square r: a faint track and the value's gold arc round a raised violet-black disc, its pointer in
// pearl. Angles in radians, clockwise from straight up; `from` is where the arc starts (the start angle, or the centre
// of a bipolar knob)
inline void drawKnob (juce::Graphics& g, juce::Rectangle<float> r, float angle, float start, float end, float from, bool enabled = true)
{
    const float R = r.getWidth() * 0.5f;
    const auto c = r.getCentre();
    const float arcW = juce::jlimit (1.5f, 4.0f, R * 0.09f);
    const float arcR = R - arcW * 0.5f;
    const float discR = R - arcW - juce::jmax (1.5f, R * 0.07f);
    juce::Path track;
    track.addCentredArc (c.x, c.y, arcR, arcR, 0.0f, start, end, true);
    g.setColour (line);
    g.strokePath (track, juce::PathStrokeType (arcW, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
    if (std::abs (angle - from) > 1.0e-3f)
    {
        juce::Path value;
        value.addCentredArc (c.x, c.y, arcR, arcR, 0.0f, juce::jmin (from, angle), juce::jmax (from, angle), true);
        g.setColour (enabled ? gold : letteringFaint);
        g.strokePath (value, juce::PathStrokeType (arcW, juce::PathStrokeType::curved, juce::PathStrokeType::rounded));
    }
    const auto disc = juce::Rectangle<float> (discR * 2.0f, discR * 2.0f).withCentre (c);
    g.setColour (juce::Colours::black.withAlpha (0.45f));
    g.fillEllipse (disc.translated (0.0f, juce::jmax (1.0f, discR * 0.06f)));
    juce::ColourGradient body (raisedTop, c.x, disc.getY(), raised, c.x, disc.getBottom(), false);
    g.setGradientFill (body);
    g.fillEllipse (disc);
    juce::ColourGradient sheen (juce::Colours::white.withAlpha (0.07f), c.x, disc.getY(), juce::Colours::transparentWhite, c.x, c.y, true);
    g.setGradientFill (sheen);
    g.fillEllipse (disc.reduced (discR * 0.08f));
    g.setColour (line.brighter (0.15f));
    g.drawEllipse (disc.reduced (0.5f), 1.0f);
    const juce::Point<float> d (std::sin (angle), -std::cos (angle));
    g.setColour (enabled ? pearl : letteringDim);
    g.drawLine (juce::Line<float> (c + d * (discR * 0.3f), c + d * (discR - juce::jmax (1.5f, discR * 0.12f))), juce::jlimit (1.5f, 3.0f, discR * 0.1f));
}

// a fader cap: a raised body, a border, grip lines and a pearl index across its middle
inline void drawCap (juce::Graphics& g, juce::Rectangle<float> r, int grips = 2)
{
    const float radius = juce::jmin (3.0f, r.getHeight() * 0.2f);
    g.setColour (juce::Colours::black.withAlpha (0.45f));
    g.fillRoundedRectangle (r.translated (0.0f, 1.5f), radius);
    g.setGradientFill (juce::ColourGradient (raisedTop, 0.0f, r.getY(), raised, 0.0f, r.getBottom(), false));
    g.fillRoundedRectangle (r, radius);
    g.setColour (line.brighter (0.2f));
    g.drawRoundedRectangle (r.reduced (0.5f), radius, 1.0f);
    const float cy = r.getCentreY();
    g.setColour (lineLight);
    for (int i = 1; i <= grips; ++i)
        for (float side : { -1.0f, 1.0f })
            g.fillRect (r.getX() + 3.0f, std::round (cy + side * (float) i * r.getHeight() * 0.18f) - 0.5f, r.getWidth() - 6.0f, 1.0f);
    g.setColour (pearl);
    g.fillRect (r.getX() + 2.5f, std::round (cy) - 1.0f, r.getWidth() - 5.0f, 2.0f);
}

// a value in a well, centred
inline void drawValueBox (juce::Graphics& g, juce::Rectangle<float> r, const juce::String& value, float size = 11.0f)
{
    drawWell (g, r);
    g.setColour (lettering);
    g.setFont (font (size));
    g.drawText (value, r, juce::Justification::centred);
}
}
