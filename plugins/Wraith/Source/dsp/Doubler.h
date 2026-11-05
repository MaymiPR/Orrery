#pragma once
#include <cmath>
#include <vector>
#include "Biquad.h"
#include "Tuning.h"

// The Doubler (MEASUREMENTS.md "Doubler"): the input plus two voices read from a delay line of the mid signal, their
// delays centre +- depth x sin (2 pi rate t) in antiphase (the rate measured per sample rate, near 0.503 Hz), each
// voice band-limited (low-passes, a high-pass), and the lows of the mid signal added undelayed; Stereo sends each voice
// to its own side with 1 + k s and to the other with 1 - k s. The caller crossfades: out = (1 - mix) dry + mix wet.
namespace wr::dsp
{
class Doubler
{
public:
    void prepare (double sampleRate, const Tuning& t)
    {
        fs = sampleRate;
        tun = t;
        size = 1;
        while (size < (int) ((t.dblCenterMs + t.dblDepthMs + 5.0) * 0.001 * fs) + 8) size <<= 1;
        line.assign ((size_t) size, 0.0);
        for (auto& f : lp) f.c = Coeffs::lowPass (fs, std::fmin (t.dblLpHz, 0.49 * fs), t.dblLpQ);
        for (auto& f : lp2) f.c = Coeffs::lowPass (fs, std::fmin (t.dblLp2Hz > 0 ? t.dblLp2Hz : 1000.0, 0.49 * fs), t.dblLp2Q);
        // the first-order high-pass (bilinear, its corner exact)
        const double k = std::tan (3.14159265358979323846 * std::fmin (t.dblHpHz > 0 ? t.dblHpHz : 10.0, 0.49 * fs) / fs);
        hpB = 1.0 / (1.0 + k);
        hpA = (1.0 - k) / (1.0 + k);
        bass.c = Coeffs::lowPass (fs, std::fmin (t.dblBassHz > 0 ? t.dblBassHz : 100.0, 0.49 * fs), t.dblBassQ);
        rate = t.dblRateHz > 0 ? t.dblRateHz : rateAt (fs);
        reset();
    }

    // the modulation's rate as measured on the reference at four sample rates (MEASUREMENTS.md 7.1): not 0.5 Hz, and not
    // monotonic in the sample rate; between them linear in the sample rate, outside them the nearest
    static double rateAt (double sampleRate)
    {
        static constexpr double rates[][2] { { 44100.0, 0.502218 }, { 48000.0, 0.502995 }, { 88200.0, 0.503458 }, { 96000.0, 0.503278 } };
        if (sampleRate <= rates[0][0]) return rates[0][1];
        for (size_t k = 1; k < 4; ++k)
            if (sampleRate <= rates[k][0])
                return rates[k - 1][1] + (rates[k][1] - rates[k - 1][1]) * (sampleRate - rates[k - 1][0]) / (rates[k][0] - rates[k - 1][0]);
        return rates[3][1];
    }

    void reset()
    {
        std::fill (line.begin(), line.end(), 0.0);
        pos = 0;
        phase = tun.dblPhase;
        for (auto& f : lp) f.reset();
        for (auto& f : lp2) f.reset();
        hpX[0] = hpX[1] = hpY[0] = hpY[1] = 0;
        bass.reset();
    }

    // stereo in place (the wet signal)
    inline void process (double& l, double& r, double stereo)
    {
        const double in = 0.5 * (l + r);
        const double lows = tun.dblBassHz > 0 ? tun.dblBassGain * bass.process (in) : 0.0;   // the lows past the line
        line[(size_t) pos] = in;
        const double s = std::sin (2.0 * 3.14159265358979323846 * phase);
        phase += rate / fs;
        if (phase >= 1.0) phase -= 1.0;
        const double a = voice (0, read ((tun.dblCenterMs - tun.dblDepthMs * s) * 0.001 * fs));
        const double b = voice (1, read ((tun.dblCenterMs + tun.dblDepthMs * s) * 0.001 * fs));
        pos = (pos + 1) & (size - 1);
        const double k = tun.dblStereoK * stereo, g = tun.dblVoiceGain;
        const double dl = l, dr = r;
        l = tun.dblDryGain * dl + g * ((1 + k) * a + (1 - k) * b) + lows;
        r = tun.dblDryGain * dr + g * ((1 - k) * a + (1 + k) * b) + lows;
    }

private:
    // one voice's filters: the low-pass (and the second one), then the high-pass when set
    double voice (int v, double x)
    {
        x = lp[v].process (x);
        if (tun.dblLp2Hz > 0) x = lp2[v].process (x);
        if (tun.dblHpHz <= 0) return x;
        const double y = hpB * (x - hpX[v]) + hpA * hpY[v];
        hpX[v] = x;
        hpY[v] = y;
        return y;
    }

    // the line delayed by d samples (fractional), by 4-point cubic interpolation (Hermite)
    double read (double d) const
    {
        const double p = (double) pos - d;
        const double fl = std::floor (p);
        const double t = p - fl;
        const int i = (int) fl;
        auto at = [this] (int k) { return line[(size_t) (k & (size - 1))]; };
        const double xm1 = at (i - 1), x0 = at (i), x1 = at (i + 1), x2 = at (i + 2);
        if (tun.dblInterp < 0.5) return x0 + t * (x1 - x0);
        const double c1 = 0.5 * (x1 - xm1), c2 = xm1 - 2.5 * x0 + 2.0 * x1 - 0.5 * x2, c3 = 0.5 * (x2 - xm1) + 1.5 * (x0 - x1);
        return ((c3 * t + c2) * t + c1) * t + x0;
    }

    double fs = 48000.0;
    Tuning tun;
    std::vector<double> line;
    int size = 1, pos = 0;
    double phase = 0, rate = 0.5;
    Biquad lp[2], lp2[2], bass;
    double hpB = 1, hpA = 0, hpX[2] {}, hpY[2] {};
};
}
