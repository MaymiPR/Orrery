#pragma once
#include <cmath>
#include <algorithm>

// The CLASSIC style's steady glow behind the stripe's particles at full brightness, an analytic shape of our own from
// a few measured tokens (design px; light 0 ... 1 per channel). Separable: a profile down the stripe times, per colour
// channel, a bell along it.
//   down: a haze that brightens towards the band, a flat-topped bump on the band (where the dashes' lanes run) with a
//         hot line along its top edge, a dimmer lip under the band and a thin line of light on the glass's lower rim;
//   along: a wide Gaussian (lavender) plus a narrow exponential core (warm) round the middle.
namespace sc::stripeglow
{
// down the stripe
constexpr float hazeFrom = 273.8f, hazeTo = 303.0f, hazeSoft = 0.5f;      // where the haze starts and ends
constexpr float hazeTop = 0.22f, hazeBand = 0.42f, hazeRiseTo = 288.0f;    // its level at the top, and from the band down
constexpr float bandY = 291.75f, bandHalf = 3.0f, bandLift = 0.32f;        // the flat-topped bump (exp (-u^4))
constexpr float lineY = 289.3f, lineWidth = 0.6f, lineLift = 0.32f;        // the hot line along the band's top edge
constexpr float lipTo = 306.9f, lipLevel = 0.15f;                          // dim light from the haze's end to the rim
constexpr float rimY = 306.2f, rimWidth = 0.45f, rimLift = 0.6f;           // the line on the glass's lower rim
// along it, per channel (red, green, blue): a exp (-((x - centre) / width)^2) + b exp (-|x - centre| / coreWidth[c])
constexpr float centre = 452.0f, width = 227.0f;
constexpr float haze[3] { 116.0f / 255.0f, 102.0f / 255.0f, 128.0f / 255.0f };   // #746680
constexpr float core[3] { 70.0f / 255.0f, 59.0f / 255.0f, 50.0f / 255.0f };      // #463b32
constexpr float coreWidth[3] { 36.0f, 21.0f, 21.0f };

inline float smooth (float a, float b, float v)
{
    const float t = std::clamp ((v - a) / (b - a), 0.0f, 1.0f);
    return t * t * (3.0f - 2.0f * t);
}

// the profile down the stripe at a design y (about 0 ... 1)
inline float down (float y)
{
    const float window = smooth (hazeFrom - hazeSoft, hazeFrom + hazeSoft, y) * (1.0f - smooth (hazeTo - hazeSoft, hazeTo + hazeSoft, y));
    const float hazeLevel = hazeTop + (hazeBand - hazeTop) * smooth (hazeFrom, hazeRiseTo, y);
    const float u = (y - bandY) / bandHalf, l = (y - lineY) / lineWidth, r = (y - rimY) / rimWidth;
    const float lip = lipLevel * smooth (hazeTo - hazeSoft, hazeTo + hazeSoft, y) * (1.0f - smooth (lipTo - 0.3f, lipTo + 0.3f, y));
    return window * hazeLevel + bandLift * std::exp (-u * u * u * u) + lineLift * std::exp (-l * l) + lip + rimLift * std::exp (-r * r);
}

// the bell along the stripe at a design x for a channel
inline float along (float x, int c)
{
    const float d = x - centre;
    return haze[c] * std::exp (-(d / width) * (d / width)) + core[c] * std::exp (-std::abs (d) / coreWidth[c]);
}
}
