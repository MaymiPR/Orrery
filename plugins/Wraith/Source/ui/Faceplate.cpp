#include "Faceplate.h"
#include "Look.h"
#include "Controls.h"
#include "shared/ui/Theme.h"

using namespace juce;
namespace theme = orrery::theme;

namespace wr::ui
{
using namespace wr::look;

namespace
{
// a card in a given colour (theme::drawCard's border and corner)
void card (Graphics& g, Rectangle<float> r, Colour fill, float radius = 6.0f)
{
    g.setColour (fill);
    g.fillRoundedRectangle (r, radius);
    g.setColour (theme::line);
    g.drawRoundedRectangle (r.reduced (0.5f), radius, 1.0f);
}

// a stadium well (a slot or a hole)
void stadiumWell (Graphics& g, const Box& b) { theme::drawWell (g, b.r(), std::min (b.w, b.h) * 0.5f); }
}

Image renderFaceplate (float dpx)
{
    const int w = (int) std::ceil (designW * dpx), h = (int) std::ceil ((designH - topBarH) * dpx);
    Image img (Image::RGB, w, h, false, SoftwareImageType());
    Graphics g (img);
    g.addTransform (AffineTransform::translation (0.0f, -topBarH).scaled (dpx));
    g.setColour (theme::bg);
    g.fillRect (Rectangle<float> (0.0f, topBarH, designW, designH - topBarH));

    // the plates: cards on true black, the input and output ones a step up from the four in the middle
    for (int s = 0; s < numSections; ++s)
        card (g, { plateX0[s], plateTop, plateX1[s] - plateX0[s], plateBottom - plateTop }, darkPlate (s) ? plateIo : plateMid);
    card (g, { stripX0, plateTop, stripX1 - stripX0, plateBottom - plateTop }, plateIo);

    // the slots and holes as wells (the pills draw their own)
    for (int s = 0; s < numSections; ++s)
        for (float x : { plateX0[s] + 3.0f, plateX1[s] - 14.0f })
        {
            if (darkPlate (s)) for (auto& sp : slotsIo) stadiumWell (g, { x, sp.y, slotW, sp.h });
            else for (auto& sp : slotsMiddle) stadiumWell (g, { x, sp.y, slotW, sp.h });
        }
    for (auto& b : wideHoles) stadiumWell (g, b);

    // the knob wells and the meters' wells (the meter draws inside its own)
    for (auto& b : well) theme::drawWell (g, b.r(), 8.0f);
    for (auto& b : ioWell) theme::drawWell (g, b.r(), 8.0f);
    for (auto& b : meter) theme::drawWell (g, b.r(), 8.0f);

    // a small dark rivet in each plate corner
    for (int s = 0; s < numSections; ++s)
        for (float x : { plateX0[s] + rivetInset, plateX1[s] - rivetInset - 1.0f })
            for (float y : { rivetTopY, rivetBottomY })
            {
                const auto c = Rectangle<float> (2.0f * rivetR, 2.0f * rivetR).withCentre ({ x - 0.5f, y - 0.5f });
                g.setColour (theme::well);
                g.fillEllipse (c.expanded (0.6f));
                g.setColour (rivet);
                g.fillEllipse (c);
            }

    // section labels
    g.setFont (theme::font (11.5f));
    g.setColour (label);
    const char* names[numSections] { "input", "character", "eq", "doubler", "reverb", "output" };
    for (int s = 0; s < numSections; ++s)
        heavyText (g, names[s], centreX (s), sectionLabelY, Justification::horizontallyCentred, 0.3f);

    // the side strip: the name read upwards, the suite under it, the mark at the foot
    {
        const float cx = (stripX0 + stripX1) * 0.5f;
        paintMark (g, { cx, 372.0f }, 9.0f);
        Graphics::ScopedSaveState ss (g);
        g.addTransform (AffineTransform::rotation (-MathConstants<float>::halfPi, cx, 352.0f));
        g.setColour (theme::pearl);
        g.setFont (theme::font (15.0f).withExtraKerningFactor (0.18f));
        theme::textAt (g, "WRAITH", cx, 352.0f + 4.0f);
        g.setColour (theme::letteringFaint);
        g.setFont (theme::font (6.5f).withExtraKerningFactor (0.08f));
        theme::textAt (g, "Orrery Suite", cx, 352.0f + 12.5f);
    }
    return img;
}

void paintMark (Graphics& g, Point<float> c, float r)
{
    // the suite's mark as the top bar's logo draws it (shared/ui/Widgets.cpp), scaled to radius r: the orbit in violet,
    // lit along its lower arc as a pearl crescent, the sun, a planet nearer in
    const float k = r / 7.2f;
    g.setColour (theme::violetLight);
    g.drawEllipse (Rectangle<float> (2.0f * r, 2.0f * r).withCentre (c), jmax (1.0f, k));
    Path crescent;
    for (int i = 0; i <= 24; ++i)
    {
        const float a = MathConstants<float>::pi * (0.7f + 0.6f * (float) i / 24.0f);
        const Point<float> p (c.x - (r + 0.5f * k) * std::sin (a), c.y - (r + 0.5f * k) * std::cos (a));
        if (i == 0) crescent.startNewSubPath (p); else crescent.lineTo (p);
    }
    for (int i = 24; i >= 0; --i)
    {
        const float a = MathConstants<float>::pi * (0.7f + 0.6f * (float) i / 24.0f);
        crescent.lineTo (c.x - (r + 0.5f * k) * std::sin (a), c.y - 1.2f * k - (r - 1.6f * k) * std::cos (a));
    }
    crescent.closeSubPath();
    g.setColour (theme::pearl);
    g.fillPath (crescent);
    g.fillEllipse (Rectangle<float> (5.2f * k, 5.2f * k).withCentre (c + Point<float> (0.0f, -0.6f * k)));
    g.fillEllipse (Rectangle<float> (2.4f * k, 2.4f * k).withCentre (c + Point<float> (3.4f * k, -3.6f * k)));
}
}
