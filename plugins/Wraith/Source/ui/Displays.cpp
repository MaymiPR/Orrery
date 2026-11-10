#include "Displays.h"
#include "Theme.h"
#include "shared/ui/Theme.h"
#include "shared/ui/Widgets.h"

using namespace juce;
namespace theme = orrery::theme;

namespace wr::ui
{
using namespace wr::look;

//==============================================================================
SectionDisplay::SectionDisplay()
{
    orrery::noFocus (*this);
    setInterceptsMouseClicks (false, false);
}

void SectionDisplay::setLit (bool on, bool animate)
{
    const float t = on ? 1.0f : 0.0f;
    if (exactlyEqual (t, target) && (! animate || exactlyEqual (lit, t))) { if (! animate) { lit = t; repaint(); } return; }
    target = t;
    if (! animate) { lit = t; stopTimer(); repaint(); return; }
    fadeFrom = lit;
    fadeStart = Time::getMillisecondCounterHiRes();
    startTimerHz (60);
}

void SectionDisplay::timerCallback()
{
    const float k = (float) ((Time::getMillisecondCounterHiRes() - fadeStart) / fadeMs);
    lit = k >= 1.0f ? target : fadeFrom + (target - fadeFrom) * k;
    if (k >= 1.0f) stopTimer();
    repaint();
}

void SectionDisplay::paint (Graphics& g)
{
    // the measured parts (a ring 1.5 px at the outer edge, a tray inside it, a screen 9 px in from the sides from y + 12.5
    // to y + 91.5) in the suite's look: the ring gold while lit and a line's colour while off, a gold glow in the
    // tray along it, the screen a well; the drawing in light gold. Lit and unlit cross-fade with the section's power
    g.addTransform (AffineTransform::translation (-origin.x, -origin.y));
    const auto r = Rectangle<float> ((float) getWidth(), (float) getHeight()).translated (origin.x, origin.y);
    const float radius = 10.0f;
    auto lerp = [this] (Colour off, Colour on) { return off.interpolatedWith (on, lit); };
    g.setColour (lerp (glowOff, glow));
    g.fillRoundedRectangle (r, radius);
    const auto tray = r.reduced (1.5f);
    g.setColour (lerp (theme::card, theme::card.interpolatedWith (theme::goldDeep, 0.14f)));
    g.fillRoundedRectangle (tray, radius - 1.5f);
    for (int i = 0; i < 3; ++i)                       // the glow, fading inwards from the ring
    {
        g.setColour (theme::gold.withAlpha (lit * (0.18f - 0.06f * (float) i)));
        g.drawRoundedRectangle (tray.reduced (0.5f + 1.2f * (float) i), radius - 2.0f - 1.2f * (float) i, 1.2f);
    }
    const Rectangle<float> screen (r.getX() + 9.0f, r.getY() + 12.5f, r.getWidth() - 18.0f, 79.0f);
    theme::drawWell (g, screen, 5.0f);
    if (lit > 0.001f)
    {
        g.setColour (theme::gold.withAlpha (lit * 0.35f));
        g.drawRoundedRectangle (screen.reduced (0.5f), 5.0f, 1.0f);
    }
    if (lit > 0.001f && drawArt)
        drawArt (g);                                  // (the drawing takes the lit amount itself)
}

//==============================================================================
LevelMeter::LevelMeter (bool input) : isInput (input) { orrery::noFocus (*this); }

void LevelMeter::setLevels (const float barDb[2], const float holdDb[2], const float maxDb[2], float targetFill)
{
    for (int c = 0; c < 2; ++c) { bar[c] = barDb[c]; hold[c] = holdDb[c]; peakMax[c] = maxDb[c]; }
    fill = targetFill;
    repaint();
}

void LevelMeter::mouseDown (const MouseEvent&) { if (onResetHold) onResetHold(); }

void LevelMeter::paint (Graphics& g)
{
    g.addTransform (AffineTransform::translation (-origin.x, -origin.y));
    // (the well behind is the faceplate's)
    const int side = isInput ? 0 : 1;
    const float (&sx)[2] = segX[side];
    // readouts: the highest peak, one decimal, "-inf" below -100 (centres measured: 50 / 93 in, 910 / 954 out), in
    // gold, red over 0 dBFS
    const float textX[2][2] { { 50.0f, 93.0f }, { 910.0f, 954.0f } };
    g.setFont (theme::font (11.0f));
    for (int c = 0; c < 2; ++c)
    {
        const String t = peakMax[c] < -100.0f ? String ("-inf") : String (peakMax[c], 1);
        g.setColour (peakMax[c] > 0.0f ? theme::clip : value);
        theme::textAt (g, t, textX[side][c], 103.5f, Justification::horizontallyCentred);
    }
    // a bar per channel over the segments' column (its well 1 px round it), filled to the bar's level, the held peak
    // a pearl marker
    for (int c = 0; c < 2; ++c)
    {
        const float peakPx = meterLitPx (hold[c]);
        theme::drawMeterBar (g, Rectangle<float> (sx[c], meterTopY, segW, meterH).expanded (1.0f), meterLitPx (bar[c]) / meterH, true,
                             peakPx > 0.0f ? peakPx / meterH : -1.0f);
    }
    if (! isInput) return;

    // the target: brackets at x 38 / 105 from y 134 to 151 with a line between them top and bottom (gaps where the
    // bars run), filled while the level sits in it
    if (fill > 0.0f)
    {
        g.setColour (theme::targetFill.withAlpha (jlimit (0.0f, 1.0f, fill)));
        Path f;
        f.addRoundedRectangle (38.0f, 134.0f, 9.0f, 18.0f, 2.5f, 2.5f, true, false, true, false);
        f.addRectangle (60.0f, 134.0f, 24.0f, 18.0f);
        f.addRoundedRectangle (97.0f, 134.0f, 9.0f, 18.0f, 2.5f, 2.5f, false, true, false, true);
        g.fillPath (f);
    }
    g.setColour (theme::target);
    Path b;
    b.startNewSubPath (46.0f, 134.5f); b.lineTo (40.5f, 134.5f); b.quadraticTo (38.5f, 134.5f, 38.5f, 136.5f);
    b.lineTo (38.5f, 149.5f); b.quadraticTo (38.5f, 151.5f, 40.5f, 151.5f); b.lineTo (46.0f, 151.5f);
    b.startNewSubPath (98.0f, 134.5f); b.lineTo (103.5f, 134.5f); b.quadraticTo (105.5f, 134.5f, 105.5f, 136.5f);
    b.lineTo (105.5f, 149.5f); b.quadraticTo (105.5f, 151.5f, 103.5f, 151.5f); b.lineTo (98.0f, 151.5f);
    b.startNewSubPath (60.0f, 134.5f); b.lineTo (84.0f, 134.5f);
    b.startNewSubPath (60.0f, 151.5f); b.lineTo (84.0f, 151.5f);
    g.strokePath (b, PathStrokeType (1.0f));

    if (showFloor)
    {
        // the floor: one pearl line across the meter, broken where the bars are (y 176 at -28.1 dB, 5 px for 2.6 dB
        // as the bars' scale)
        const float y = 176.0f - (floorDb + 28.1f) * (segPitch / 2.6f);
        g.setColour (floorLine);
        g.fillRect (38.0f, y, 8.0f, 1.0f);
        g.fillRect (60.0f, y, 24.0f, 1.0f);
        g.fillRect (98.0f, y, 8.0f, 1.0f);
    }
}
}
