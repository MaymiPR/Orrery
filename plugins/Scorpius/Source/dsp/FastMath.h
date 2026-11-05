#pragma once

// tanh and the logistic sigmoid for the learned models' activations, as a rational (Pade 7/6) approximation of tanh:
// within 1e-6 of it up to |x| = 4.97 and clamped beyond, several times cheaper than std::tanh / std::exp.
namespace sc::dsp
{
inline float fastTanh (float x)
{
    x = x < -4.97f ? -4.97f : (x > 4.97f ? 4.97f : x);      // (as std::clamp, in a form the loops vectorise)
    const float x2 = x * x;
    const float num = x * (135135.0f + x2 * (17325.0f + x2 * (378.0f + x2)));
    const float den = 135135.0f + x2 * (62370.0f + x2 * (3150.0f + x2 * 28.0f));
    return num / den;
}

inline float fastSigmoid (float x) { return 0.5f + 0.5f * fastTanh (0.5f * x); }

// e^x for |x| <= 80 by scaling and squaring: the (2, 2) Pade approximant of e^(x / 256), squared eight times (relative
// error under 1e-5). Unlike the clamped forms above it keeps the tails: 1 - sigmoid(x) = e^-x for large x is what
// sets an LSTM's forget gate near 1, so the slow cells' memory (MEASUREMENTS.md 14).
inline float tailExp (float x)
{
    x = x < -80.0f ? -80.0f : (x > 80.0f ? 80.0f : x);
    const float u = x * (1.0f / 256.0f);
    float e = (12.0f + u * (6.0f + u)) / (12.0f + u * (u - 6.0f));
    e *= e; e *= e; e *= e; e *= e; e *= e; e *= e; e *= e; e *= e;
    return e;
}

inline float tailSigmoid (float x) { return 1.0f / (1.0f + tailExp (-x)); }

inline float tailTanh (float x)
{
    const float e = tailExp (-2.0f * x);
    return (1.0f - e) / (1.0f + e);
}
}
