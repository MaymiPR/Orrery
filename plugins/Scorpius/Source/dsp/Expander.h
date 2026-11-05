#pragma once
#include <algorithm>
#include <cmath>
#include <vector>
#include "Tuning.h"

// The low-level expander that drive, harmonics, compression and lift share (MEASUREMENTS.md 3): below a threshold
// (a sine's peak at ~-58 dBFS) the gain falls 2 dB per dB, to no lower than -44.5 dB. Once the peak has reached the
// threshold it stays open for ~1.1 s after the last time it did; below the threshold it holds the peak of the last
// ~0.1 s only. The gain follows with a one-pole on its linear value, 1 ms opening, ~0.1 s closing. Reset, it is
// closed, as after silence (the reference's modules start that way when switched on; MEASUREMENTS.md 3, 12).
namespace sc::dsp
{
class Expander
{
public:
    void prepare (double sampleRate)
    {
        fs = sampleRate;
        const auto& t = tuning();
        chunk = std::max (1, (int) std::lround (0.001 * fs));
        peaks.assign ((size_t) std::max (1, (int) std::lround (t.expShortHoldMs * 0.001 * fs / chunk)), 0.0);
        holdLong = (long) std::lround (t.expHoldMs * 0.001 * fs);
        threshold = std::pow (10.0, t.expThresholdDb / 20.0);
        release = std::exp (-1.0 / (t.expReleaseMs * 0.001 * fs));
        attack = std::exp (-1.0 / (t.expAttackMs * 0.001 * fs));
        reset();
    }
    void reset()
    {
        std::fill (peaks.begin(), peaks.end(), 0.0);
        pos = 0; count = 0; current = 0; window = 0.0; sinceOpen = holdLong;
        gain = std::pow (10.0, tuning().expFloorDb / 20.0);
    }
    // open, as if the level had just reached the threshold (its long hold then runs from here)
    void open() { reset(); gain = 1.0; sinceOpen = 0; }
    // the gain (linear) for each sample of a stereo block, from its own input
    void gains (const double* l, const double* r, double* out, int n)
    {
        const auto& t = tuning();
        for (int i = 0; i < n; ++i)
        {
            const double a = std::abs (0.5 * (l[i] + r[i]));       // (the mid: MEASUREMENTS.md 3)
            sinceOpen = a >= threshold ? 0 : std::min (sinceOpen + 1, holdLong);
            current = std::max (current, a);
            const double held = std::max (current, window);
            if (++count >= chunk)
            {
                peaks[(size_t) pos] = current;
                pos = (pos + 1) % (int) peaks.size();
                current = 0; count = 0;
                window = *std::max_element (peaks.begin(), peaks.end());
            }
            double target = 1.0;
            if (sinceOpen >= holdLong)
            {
                const double below = t.expThresholdDb - 20.0 * std::log10 (std::max (held, 1.0e-9));
                target = below <= 0 ? 1.0 : std::pow (10.0, std::max (t.expFloorDb, -t.expSlope * below) / 20.0);
            }
            gain = target + (gain - target) * (target > gain ? attack : release);
            out[i] = gain;
        }
    }

private:
    double fs = 48000.0, release = 0.0, attack = 0.0, threshold = 0.0, current = 0, gain = 1.0, window = 0.0;   // window: the peak of the chunks held
    int chunk = 48, pos = 0, count = 0;
    long holdLong = 0, sinceOpen = 0;
    std::vector<double> peaks;
};
}
