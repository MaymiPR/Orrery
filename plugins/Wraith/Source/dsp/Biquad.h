#pragma once
#include <cmath>

// A biquad in transposed direct form II (double state), with the RBJ cookbook designs the measurements matched
// (MEASUREMENTS.md "EQ": w0 = 2 pi f0 / fs, no prewarping).
namespace wr::dsp
{
struct Coeffs
{
    double b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0;

    static Coeffs shelf (double fs, double f0, double q, double gainDb, bool low)
    {
        const double A = std::pow (10.0, gainDb / 40.0), w0 = 2.0 * 3.14159265358979323846 * f0 / fs;
        const double c = std::cos (w0), k = 2.0 * std::sqrt (A) * std::sin (w0) / (2.0 * q);
        double b[3], a[3];
        if (low)
        {
            b[0] = A * ((A + 1) - (A - 1) * c + k); b[1] = 2 * A * ((A - 1) - (A + 1) * c); b[2] = A * ((A + 1) - (A - 1) * c - k);
            a[0] = (A + 1) + (A - 1) * c + k;       a[1] = -2 * ((A - 1) + (A + 1) * c);      a[2] = (A + 1) + (A - 1) * c - k;
        }
        else
        {
            b[0] = A * ((A + 1) + (A - 1) * c + k); b[1] = -2 * A * ((A - 1) + (A + 1) * c); b[2] = A * ((A + 1) + (A - 1) * c - k);
            a[0] = (A + 1) - (A - 1) * c + k;       a[1] = 2 * ((A - 1) - (A + 1) * c);       a[2] = (A + 1) - (A - 1) * c - k;
        }
        return { b[0] / a[0], b[1] / a[0], b[2] / a[0], a[1] / a[0], a[2] / a[0] };
    }

    static Coeffs highPass (double fs, double f0, double q)
    {
        const double w0 = 2.0 * 3.14159265358979323846 * f0 / fs, c = std::cos (w0), al = std::sin (w0) / (2.0 * q);
        const double a0 = 1 + al;
        return { (1 + c) / 2 / a0, -(1 + c) / a0, (1 + c) / 2 / a0, -2 * c / a0, (1 - al) / a0 };
    }

    static Coeffs peak (double fs, double f0, double q, double gainDb)
    {
        const double A = std::pow (10.0, gainDb / 40.0), w0 = 2.0 * 3.14159265358979323846 * f0 / fs;
        const double c = std::cos (w0), al = std::sin (w0) / (2.0 * q), a0 = 1 + al / A;
        return { (1 + al * A) / a0, -2 * c / a0, (1 - al * A) / a0, -2 * c / a0, (1 - al / A) / a0 };
    }

    static Coeffs lowPass (double fs, double f0, double q)
    {
        const double w0 = 2.0 * 3.14159265358979323846 * f0 / fs, c = std::cos (w0), al = std::sin (w0) / (2.0 * q);
        const double a0 = 1 + al;
        return { (1 - c) / 2 / a0, (1 - c) / a0, (1 - c) / 2 / a0, -2 * c / a0, (1 - al) / a0 };
    }
};

struct Biquad
{
    Coeffs c;
    double z1 = 0, z2 = 0;
    void reset() { z1 = z2 = 0; }
    inline double process (double x)
    {
        const double y = c.b0 * x + z1;
        z1 = c.b1 * x - c.a1 * y + z2;
        z2 = c.b2 * x - c.a2 * y;
        return y;
    }
};
}
