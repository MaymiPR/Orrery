#include "Controls.h"
#include "Params.h"

using namespace juce;
namespace theme = orrery::theme;

namespace sc
{
//==============================================================================
void SegmentStack::paint (Graphics& g)
{
    const float w = (float) getWidth();
    const int n = options.size();
    g.setFont (theme::font (12.0f));
    for (int i = 0; i < n; ++i)
    {
        // every row is a box of its own (so two frames meet between rows), rounded only at the stack's outer corners;
        // the selected one is filled gold, the others raised in a frame
        const Rectangle<float> row (0.0f, (rowHeight + gap) * (float) i, w, rowHeight);
        const bool first = i == 0, last = i == n - 1;
        Path p;
        p.addRoundedRectangle (row.getX(), row.getY(), row.getWidth(), row.getHeight(), 3.0f, 3.0f, first, first, last, last);
        const bool down = i == pressed && held;
        if (i == selected)
        {
            g.setColour (theme::gold);
            g.fillPath (p);
        }
        else
        {
            g.setColour (theme::raised);
            g.fillPath (p);
            if (i == hover || down)
            {
                g.setColour (theme::gold.withAlpha (0.2f));
                g.fillPath (p);
            }
            if (! down)                     // held down, a row shows no frame (as the reference)
            {
                Path o;
                const auto r = row.reduced (0.5f);
                o.addRoundedRectangle (r.getX(), r.getY(), r.getWidth(), r.getHeight(), 2.5f, 2.5f, first, first, last, last);
                g.setColour (i == hover ? theme::gold : theme::lineLight);
                g.strokePath (o, PathStrokeType (1.0f));
            }
        }
        g.setColour (i == selected ? theme::well : theme::lettering);
        g.drawText (options[i], row.translated (0.0f, -0.5f), Justification::centred, false);
    }
}

// a row is chosen on release over the row that was pressed (measured: a press dragged off chooses nothing)
void SegmentStack::mouseDown (const MouseEvent& e) { pressed = rowAt (e.y); held = true; repaint(); }

// the pressed look lasts only while the mouse stays on the row it pressed
void SegmentStack::mouseDrag (const MouseEvent& e)
{
    const bool on = getLocalBounds().contains (e.getPosition()) && rowAt (e.y) == pressed;
    if (on != held) { held = on; repaint(); }
}

void SegmentStack::mouseUp (const MouseEvent& e)
{
    const int i = rowAt (e.y);
    const bool over = getLocalBounds().contains (e.getPosition());
    const int was = pressed;
    pressed = -1;
    held = false;
    repaint();
    if (over && i == was && i != selected) { selected = i; if (onChange) onChange (i); }
}

//==============================================================================
void TextToggle::paint (Graphics& g)
{
    const auto b = getLocalBounds().toFloat().withHeight (23.5f);
    g.setFont (theme::font (12.0f));
    if (isMouseButtonDown() && isMouseOver())
    {
        // pressed, on or off: a dark gold box without a frame, the text dimmed (as the reference)
        g.setColour (theme::gold.withAlpha (0.2f));
        g.fillRoundedRectangle (b.reduced (0.5f), 3.0f);
        g.setColour (theme::goldLight.withAlpha (0.85f));
        g.drawText (text, b.translated (0.0f, -0.5f), Justification::centred, false);
        return;
    }
    if (active)
    {
        g.setColour (theme::gold);
        g.fillRoundedRectangle (b, 3.0f);
        g.setColour (theme::well);
    }
    else
    {
        g.setColour (theme::raised);
        g.fillRoundedRectangle (b.reduced (0.5f), 3.0f);
        if (isMouseOver())
        {
            g.setColour (theme::gold.withAlpha (0.2f));
            g.fillRoundedRectangle (b.reduced (0.5f), 3.0f);
        }
        g.setColour (isMouseOver() ? theme::gold : theme::lineLight);
        g.drawRoundedRectangle (b.reduced (0.5f), 3.0f, 1.0f);
        g.setColour (theme::lettering);
    }
    g.drawText (text, b.translated (0.0f, -0.5f), Justification::centred, false);
}

//==============================================================================
Fader::Fader()
{
    noFocus (*this);
    setSliderStyle (Slider::LinearVertical);
    setTextBoxStyle (Slider::NoTextBox, false, 0, 0);
    setRange (0.0, 1.0);
    setSliderSnapsToMousePosition (false);
    setVelocityBasedMode (false);
    // Shift: JUCE's velocity mode (cursor hidden, slow moves fine-tune), as the reference; Ctrl drags at the normal speed
    setVelocityModeParameters (1.0, 1, 0.0, true, ModifierKeys::shiftModifier);
    setMouseDragSensitivity (pixelsPerRange);
    setDoubleClickReturnValue (true, 0.0);
}

// Alt-click: back to 0 (measured), without a drag after it
void Fader::mouseDown (const MouseEvent& e)
{
    Slider::mouseDown (e);
    if (e.mods.isAltDown()) setValue (getDoubleClickReturnValue(), sendNotificationSync);
}

void Fader::mouseDrag (const MouseEvent& e)
{
    if (! e.mods.isAltDown()) Slider::mouseDrag (e);
}

void Fader::paint (Graphics& g)
{
    const float cx = (float) getWidth() * 0.5f;
    const float v = (float) valueToProportionOfLength (getValue());
    const float capY = bottomY + (topY - bottomY) * v;
    // the scale: a faint tick either side of the slot every tenth of the travel, longer at the ends and the middle
    g.setColour (theme::letteringFaint);
    for (int k = 0; k <= 10; ++k)
    {
        const float y = std::round (bottomY + (topY - bottomY) * (float) k / 10.0f) - 0.5f;
        const float len = (k % 5) == 0 ? 5.0f : 3.0f;
        g.fillRect (cx - 7.0f - len, y, len, 1.0f);
        g.fillRect (cx + 7.0f, y, len, 1.0f);
    }
    // the slot: a well over the cap's travel; gold from the cap down while the path is on
    const Rectangle<float> slot (cx - 2.5f, topY - 2.5f, 5.0f, bottomY - topY + 5.0f);
    theme::drawWell (g, slot, 2.5f);
    if (on && v > 0.0f)
    {
        g.setColour (theme::gold);
        g.fillRoundedRectangle (slot.reduced (1.5f).withTop (capY), 1.0f);
    }
    theme::drawCap (g, Rectangle<float> (cx - capW * 0.5f, capY - capH * 0.5f, capW, capH));
}

//==============================================================================
namespace
{
// the marks' centres per colour (measured at 200 %: design px from the column's corner at 96, 41), in the order of
// their identities: a mark moves to its own place when the colour changes (marks 2 and 3 are the large ones)
constexpr float markPos[3][5][2] {
    { { 6.5f, 73.75f }, { 20.5f, 54.75f }, { 42.5f, 39.75f }, { 42.5f, 64.75f }, { 57.5f, 48.75f } },
    { { 40.5f, 74.75f }, { 58.5f, 42.75f }, { 20.5f, 39.75f }, { 33.5f, 52.75f }, { 7.5f, 57.75f } },
    { { 35.5f, 38.75f }, { 21.5f, 52.75f }, { 10.5f, 61.75f }, { 53.5f, 51.75f }, { 35.5f, 75.75f } } };
constexpr float markSize[5] { 4.25f, 4.25f, 7.5f, 7.5f, 4.25f };       // arm length

double nowMs() { return Time::getMillisecondCounterHiRes(); }

float easeInOutCubic (float u)
{
    return u < 0.5f ? 4.0f * u * u * u : 1.0f - std::pow (-2.0f * u + 2.0f, 3.0f) * 0.5f;
}
}

Point<float> DriveSparks::markAt (int i, double now) const
{
    const Point<float> to (markPos[colour][i][0], markPos[colour][i][1]);
    const float u = (float) jlimit (0.0, 1.0, (now - moveStart) / moveMs);
    return from[i] + (to - from[i]) * easeInOutCubic (u);
}

void DriveSparks::setColour (int c, bool animate)
{
    c = jlimit (0, 2, c);
    if (c == colour) return;
    const double now = nowMs();
    for (int i = 0; i < 5; ++i)            // (a move under way sets out again from where its marks are)
        from[i] = animate ? markAt (i, now) : Point<float> (markPos[c][i][0], markPos[c][i][1]);
    colour = c;
    moveStart = animate ? now : -1.0e9;
    if (animate) startTimerHz (60);
    repaint();
}

void DriveSparks::setHiPass (bool on, bool animate)
{
    if (on == hiPass) return;
    hiPass = on;
    crossStart = animate ? nowMs() : -1.0e9;
    if (animate) startTimerHz (60);
    repaint();
}

void DriveSparks::timerCallback()
{
    const double now = nowMs();
    if (now - moveStart > moveMs && now - crossStart > crossMs) stopTimer();
    repaint();
}

void DriveSparks::paint (Graphics& g)
{
    const double now = nowMs();
    // the cross-fade: the shape on its way out first, the new one over it
    const float q = (float) jlimit (0.0, 1.0, (now - crossStart) / crossMs);
    for (int layer = 0; layer < 2; ++layer)
    {
        const bool star = layer == 0 ? ! hiPass : hiPass;
        const float alpha = layer == 0 ? 1.0f - q : q;
        if (alpha <= 0.0f) continue;
        g.setColour (theme::pearl.withMultipliedAlpha (alpha));
        for (int i = 0; i < 5; ++i)
        {
            const auto m = markAt (i, now);
            const float s = markSize[i];
            Path p;
            p.startNewSubPath (m.x - s, m.y); p.lineTo (m.x + s, m.y);
            p.startNewSubPath (m.x, m.y - s); p.lineTo (m.x, m.y + s);
            if (star)
            {
                const float d = s * 0.72f;
                p.startNewSubPath (m.x - d, m.y - d); p.lineTo (m.x + d, m.y + d);
                p.startNewSubPath (m.x - d, m.y + d); p.lineTo (m.x + d, m.y - d);
            }
            g.strokePath (p, PathStrokeType (s > 5.0f ? 1.0f : 0.55f));        // (measured: 2 px and 1 px at 200 %)
        }
    }
}

//==============================================================================
void Fades::show (Component& c, bool visible, bool animate)
{
    const float target = visible ? 1.0f : 0.0f;
    auto it = std::find_if (fades.begin(), fades.end(), [&c] (const Fade& f) { return f.c == &c; });
    if (it != fades.end() ? exactlyEqual (it->to, target) : c.isVisible() == visible) return;        // already there or on its way
    const float now = c.isVisible() ? c.getAlpha() : 0.0f;                               // (a fade under way turns back)
    if (it != fades.end()) fades.erase (it);
    if (! animate)
    {
        c.setAlpha (1.0f);
        c.setVisible (visible);
        return;
    }
    c.setAlpha (now);
    c.setVisible (true);
    fades.push_back ({ &c, now, target, nowMs() });
    startTimerHz (60);
}

void Fades::timerCallback()
{
    const double t = nowMs();
    for (auto it = fades.begin(); it != fades.end();)
    {
        if (it->c == nullptr) { it = fades.erase (it); continue; }
        const double span = fullMs * std::abs (it->to - it->from);
        const float u = span <= 0.0 ? 1.0f : (float) jlimit (0.0, 1.0, (t - it->start) / span);
        it->c->setAlpha (it->from + (it->to - it->from) * u);
        if (u >= 1.0f)
        {
            it->c->setVisible (it->to > 0.0f);
            it->c->setAlpha (1.0f);
            it = fades.erase (it);
        }
        else
            ++it;
    }
    if (fades.empty()) stopTimer();
}

//==============================================================================
void GrReadout::paint (Graphics& g)
{
    g.setColour (theme::gold);
    g.setFont (theme::font (19.5f));
    // the number is centred and a reduction's "-" hangs to its left (as the reference: "- 3.6" sits left of "0.0")
    const float cx = (float) getWidth() * 0.5f;
    const String number = text.startsWith ("-") ? text.substring (1).trimStart() : text;
    theme::textAt (g, number, cx, 22.0f, Justification::horizontallyCentred);
    if (number != text)
    {
        GlyphArrangement ga;
        ga.addLineOfText (g.getCurrentFont(), number, 0.0f, 0.0f);
        theme::textAt (g, "-", cx - ga.getBoundingBox (0, -1, false).getRight() * 0.5f - 5.0f, 22.0f, Justification::right);
    }
}


//==============================================================================
Blob::Blob (uint32 seed, Law l) : law (l)
{
    setInterceptsMouseClicks (false, false);
    // the outline's deformation: lobes 2 ... 12 in the reference's proportions (its outlines' angular spectrum), each
    // swelling in place at its own speed (the reference's shapes morph without turning), scaled to an rms of 1
    static constexpr float profile[lobes] { 0.80f, 0.53f, 0.66f, 0.22f, 0.40f, 0.20f, 0.25f, 0.15f, 0.10f, 0.12f, 0.08f };
    Random r ((int64) seed);
    float power = 0.0f;
    for (int k = 0; k < lobes; ++k)
    {
        amp[k] = profile[k] * (0.8f + 0.4f * r.nextFloat());
        phaseC[k] = MathConstants<float>::twoPi * r.nextFloat();
        phaseS[k] = MathConstants<float>::twoPi * r.nextFloat();
        rateC[k] = 0.6f + 1.6f * r.nextFloat();
        rateS[k] = 0.6f + 1.6f * r.nextFloat();
        power += amp[k] * amp[k] * 0.5f;
    }
    for (auto& a : amp) a /= std::sqrt (power);
}

float Blob::target (float peak) const
{
    if (peak < 0.00251f) return restRadius;                       // (below -52 dBFS)
    return jmin (maxRadius, law.k0 + law.k1 * (std::pow (peak, law.power) - 0.0832f));
}

void Blob::update (float peak, float dt)
{
    const float goal = target (peak);
    if (goal > radius) radius += (goal - radius) * (1.0f - std::exp (-dt / law.upSeconds));
    else radius -= jmin (law.fallPxPerSecond * dt, (radius - goal) * (1.0f - std::exp (-dt / law.downSeconds)));
    if (goal <= restRadius && radius - restRadius < 0.1f) radius = restRadius;
    // the shape moves by as much as the level changes (a steady tone leaves it still)
    const float db = 20.0f * std::log10 (jmax (peak, 1.0e-6f));
    if (db > -60.0f || lastDb > -60.0f) time += 0.05f * jmin (12.0f, std::abs (db - jmax (lastDb, -60.0f)));
    lastDb = db;
    repaint();
}

void Blob::freeze (float peak)
{
    radius = target (peak);
    time = 3.7f;
    repaint();
}

void Blob::paint (Graphics& g)
{
    const auto c = getLocalBounds().toFloat().getCentre();
    // (measured: about 1 px of deformation (rms) at any size once it grows)
    const float deform = 1.0f * jlimit (0.0f, 1.0f, (radius - restRadius) / 3.0f);
    Path p;
    constexpr int n = 120;
    for (int i = 0; i <= n; ++i)
    {
        const float a = MathConstants<float>::twoPi * (float) i / (float) n;
        float w = 0.0f;
        for (int k = 0; k < lobes; ++k)
            w += amp[k] * (std::cos (phaseC[k] + rateC[k] * time) * std::cos ((float) (k + 2) * a)
                           + std::sin (phaseS[k] + rateS[k] * time) * std::sin ((float) (k + 2) * a));
        const float rr = radius + deform * w;
        const Point<float> q (c.x + rr * std::sin (a), c.y - rr * std::cos (a));
        if (i == 0) p.startNewSubPath (q); else p.lineTo (q);
    }
    p.closeSubPath();
    g.setColour (theme::gold.withAlpha (0.1f));
    g.fillPath (p);
    g.setColour (theme::gold);
    g.strokePath (p, PathStrokeType (1.0f));
}

//==============================================================================
void EqCurve::paint (Graphics& g)
{
    // Measured on the reference at 200 % (each band alone at 3 and 6 dB): not a response curve but one shape per band,
    // evenly spaced, each filled at 18 % and outlined at 37 % (overlaps add up; ours in gold); heights linear in dB over a
    // baseline at y 124.75. The middle bands are bells exp (-(|x - c| / 15.64)^2.47) at x 478.98, 515.48, 551.49;
    // 40 Hz and 10 kHz are shoulders falling off past x 457.97 / 575.05. Drawn over x 432.25 ... 600.75.
    constexpr float originX = 432.0f, originY = 70.0f;            // (the component's place)
    constexpr float baseline = 124.75f, bellPerDb = 51.2f / 6.0f, shoulderPerDb = 52.7f / 6.0f;
    constexpr float bellX[3] { 478.98f, 515.48f, 551.49f };
    const float left = 432.25f, right = 600.75f;
    auto shape = [&] (int band, float x)
    {
        if (band == 0) return gains[0] * shoulderPerDb / (1.0f + std::exp ((x - 457.97f) / 6.40f));
        if (band == 4) return gains[4] * shoulderPerDb / (1.0f + std::exp ((575.05f - x) / 6.35f));
        return gains[band] * bellPerDb * std::exp (-std::pow (std::abs (x - bellX[band - 1]) / 15.64f, 2.47f));
    };
    g.addTransform (AffineTransform::translation (-originX, -originY));
    for (int b = 0; b < 5; ++b)
    {
        if (gains[b] <= 0.0f) continue;
        Path p;
        p.startNewSubPath (left, baseline);
        constexpr int steps = 168;
        for (int i = 0; i <= steps; ++i)
        {
            const float x = left + (right - left) * (float) i / (float) steps;
            p.lineTo (x, baseline - shape (b, x));
        }
        p.lineTo (right, baseline);
        p.closeSubPath();
        g.setColour (theme::gold.withAlpha (0.183f));
        g.fillPath (p);
        // the outline where the shape stands above the baseline (the baseline is drawn once, below), down to the
        // baseline where a shoulder meets the edge
        Path edge;
        bool open = false;
        for (int i = 0; i <= steps; ++i)
        {
            const float x = left + (right - left) * (float) i / (float) steps, h = shape (b, x);
            if (h < 0.2f) { open = false; continue; }
            if (! open)
            {
                edge.startNewSubPath (x, i == 0 ? baseline : baseline - h);
                if (i == 0) edge.lineTo (x, baseline - h);
                open = true;
            }
            else
                edge.lineTo (x, baseline - h);
            if (i == steps) edge.lineTo (x, baseline);
        }
        g.setColour (theme::gold.withAlpha (0.375f));
        g.strokePath (edge, PathStrokeType (0.5f));
    }
    g.setColour (theme::gold.withAlpha (0.375f));
    g.fillRect (left, baseline - 0.25f, right - left, 0.5f);
}
}
