#pragma once
#include <algorithm>
#include <cmath>
#include "Tuning.h"

// The Gain Rider (MEASUREMENTS.md "Rider"): an RMS detector on the mid signal (attack from Speed, a fixed release),
// a gain toward the target (Amount x (target - level)), at most +20 dB of boost, and below the Floor a boost limit that
// falls linearly to 0 dB over |Floor| / 5 dB. One gain for both channels.
namespace wr::dsp
{
class Rider
{
public:
    void prepare (double sampleRate, const Tuning& t)
    {
        fs = sampleRate;
        tun = t;
        relCoef = coef (t.riderReleaseMs);
        smoothCoef = coef (t.riderSmoothMs);
        reset();
    }
    void reset() { power = -1; gainDb = 0; }

    inline void process (double& l, double& r, double speedSeconds, double amount, double floorDb)
    {
        const double m = 0.5 * (l + r), p = m * m;
        if (power < 0) power = p;
        const double att = coef (tun.riderAttackScale * speedSeconds * 1000.0);
        power = p + (p > power ? att : relCoef) * (power - p);
        const double level = 10.0 * std::log10 (power + 1e-30) + tun.riderOffsetDb;     // dB re the target
        double g = -level;
        if (g > 0)
        {
            const double width = tun.riderGateWidth * std::fabs (floorDb);
            const double limit = width > 0 ? std::clamp (tun.riderMaxBoostDb * (level - floorDb) / width, 0.0, tun.riderMaxBoostDb)
                                           : tun.riderMaxBoostDb;
            g = std::min (g, limit);
        }
        else g = std::max (g, -tun.riderMaxCutDb);
        g *= amount;
        gainDb = g + smoothCoef * (gainDb - g);
        const double lin = std::pow (10.0, gainDb / 20.0);
        l *= lin;
        r *= lin;
    }

    double currentGainDb() const { return gainDb; }

private:
    double coef (double ms) const { return ms > 0 ? std::exp (-1.0 / (ms * 0.001 * fs)) : 0.0; }
    double fs = 48000.0;
    Tuning tun;
    double power = -1, gainDb = 0, relCoef = 0, smoothCoef = 0;
};
}
