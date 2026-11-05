// The plate knobs' shadow on the plate, drawn from design tokens (hand-written; lengths in design px).
// The light comes from the upper right (KnobModel.h lightAngle), so the knob casts its shadow the other way: the knob's
// disc, a little inset, swept along the shadow direction (a capsule), with a penumbra that widens with the distance
// from the knob and a strength that fades with it; plus a tight contact shadow at the knob's edge, strongest on the
// shadow side. darkness = 1 - (1 - cast) (1 - contact), capped at maxDarkness.
#pragma once
#include <cmath>
#include <algorithm>

namespace orrery::knobshadow
{
inline constexpr float angleDeg = 246.0f;          // shadow direction (from up, clockwise): opposite the light
inline constexpr float castLength = 20.0f;         // how far the disc is swept along that direction
inline constexpr float castInset = 2.0f;           // the swept disc's radius is the knob's minus this
inline constexpr float penumbra = 2.0f;            // soft edge right at the knob ...
inline constexpr float penumbraGrowth = 0.6f;      // ... widening by this per design px along the shadow
inline constexpr float castStrength = 0.8f;
inline constexpr float castFade = 60.0f;           // the cast shadow's strength halves about every 0.7 x this
inline constexpr float contactStrength = 0.3f, contactLength = 3.0f;
inline constexpr float maxDarkness = 0.73f;

// darkness 0 .. maxDarkness at (dx, dy) design px from the centre of a knob of radius R (y down)
inline float darkness (float dx, float dy, float R)
{
    constexpr float a = angleDeg * 3.14159265f / 180.0f;
    const float ux = std::sin (a), uy = -std::cos (a);
    const float along = dx * ux + dy * uy;                       // position along the shadow direction
    const float t = std::clamp (along, 0.0f, castLength);
    const float s = std::hypot (dx - t * ux, dy - t * uy) - (R - castInset);   // outside the swept disc
    const float d = std::max (0.0f, std::hypot (dx, dy) - R);                  // beyond the knob's edge
    const float cast = castStrength * 0.5f * std::erfc (s / (penumbra + penumbraGrowth * std::max (0.0f, along)))
                     * std::exp (-d / castFade);
    const float facing = 0.5f + 0.5f * (along / std::max (1.0e-3f, std::hypot (dx, dy)));   // 1 on the shadow side
    const float contact = contactStrength * std::exp (-d / contactLength) * facing;
    return std::min (maxDarkness, 1.0f - (1.0f - cast) * (1.0f - contact));
}
}
