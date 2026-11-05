#pragma once
#include <algorithm>
#include <cmath>
#include <vector>

// Short-term loudness for the I/O readouts' LUFS mode (MEASUREMENTS.md 6): ITU-R BS.1770 K-weighting (its pre-filter
// shelf and RLB high-pass, designed for the host rate from the standard's analog parameters), the two channels' mean
// squares summed, over the last 3 s (in 10 ms bins). The reference's readout shows this, the same in both channels' boxes.
namespace po
{
class ShortTermLoudness
{
public:
    void prepare (double sampleRate)
    {
        // the pre-filter: a high shelf (+4 dB, 1682 Hz); the RLB weighting: a 2nd-order high-pass (38 Hz)
        {
            const double f0 = 1681.974450955533, G = 3.999843853973347, Q = 0.7071752369554196;
            const double K = std::tan (3.14159265358979323846 * f0 / sampleRate), Vh = std::pow (10.0, G / 20.0);
            const double Vb = std::pow (Vh, 0.4996667741545416), a0 = 1.0 + K / Q + K * K;
            shelf = { (Vh + Vb * K / Q + K * K) / a0, 2.0 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0,
                      2.0 * (K * K - 1.0) / a0, (1.0 - K / Q + K * K) / a0 };
        }
        {
            const double f0 = 38.13547087602444, Q = 0.5003270373238773;
            const double K = std::tan (3.14159265358979323846 * f0 / sampleRate), a0 = 1.0 + K / Q + K * K;
            highPass = { 1.0, -2.0, 1.0, 2.0 * (K * K - 1.0) / a0, (1.0 - K / Q + K * K) / a0 };
        }
        binLength = std::max (1, (int) std::lround (sampleRate * 0.01));
        bins.assign (300, 0.0);
        reset();
    }
    void reset()
    {
        for (auto& c : z) c[0] = c[1] = c[2] = c[3] = 0.0;
        std::fill (bins.begin(), bins.end(), 0.0);
        acc = sum = 0.0; filled = 0; pos = 0;
    }
    // one block of both channels (after any gain the readout is to see)
    void process (const float* l, const float* r, int n)
    {
        const float* x[2] { l, r };
        for (int i = 0; i < n; ++i)
        {
            for (int c = 0; c < 2; ++c)
            {
                const double y = run (highPass, z[c] + 2, run (shelf, z[c], x[c][i]));
                acc += y * y;
            }
            if (++filled == binLength)
            {
                sum += acc - bins[(size_t) pos];
                bins[(size_t) pos] = acc;
                pos = (pos + 1) % (int) bins.size();
                acc = 0.0; filled = 0;
                if (pos == 0) { sum = 0.0; for (const double v : bins) sum += v; }      // no drift in the running sum
            }
        }
        if (sum < 0.0) sum = 0.0;
    }
    // the summed mean square over the last 3 s; loudness (LUFS) = -0.691 + 10 log10 of it
    double meanSquare() const { return sum / ((double) binLength * (double) bins.size()); }

private:
    struct Biquad { double b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0; };
    static double run (const Biquad& f, double* s, double x)        // transposed direct form II
    {
        const double y = f.b0 * x + s[0];
        s[0] = f.b1 * x - f.a1 * y + s[1];
        s[1] = f.b2 * x - f.a2 * y;
        return y;
    }
    Biquad shelf, highPass;
    double z[2][4] {};
    std::vector<double> bins;
    double acc = 0.0, sum = 0.0;
    int binLength = 480, filled = 0, pos = 0;
};
}
