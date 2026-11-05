#pragma once
#include <cmath>
#include <vector>
#include "Biquad.h"
#include "FocusEq.h"
#include "Ramp.h"
#include "Tuning.h"

// The Character stage (MEASUREMENTS.md "Character"): the Focus EQ, then a downward expander, the Compression drive
// (0.2 dB per step above -50), and a compressor that holds the output near its ceiling and overshoots after a rise
// in level. One gain for both channels, computed from the mid signal (the reference's detectors hear mid only).
namespace wr::dsp
{
class Character
{
public:
    void prepare (double sampleRate, const Tuning& t)
    {
        fs = sampleRate;
        tun = t;
        const size_t ns = sizeof (focuseq::sections) / sizeof (focuseq::sections[0]);
        const size_t na = sizeof (focuseq::allpasses) / sizeof (focuseq::allpasses[0]);
        for (auto& c : eq) c.assign (ns, Biquad());
        // the sections, as fitted at the nearest sample rate in the table where it has them
        secs.assign (std::begin (focuseq::sections), std::end (focuseq::sections));
        double near = 0;            // 0: no rate in the table looked at yet
        for (const auto& e : focuseq::rateSections)
            if (near <= 0 || std::fabs (std::log (e.fs / fs)) < std::fabs (std::log (near / fs))) near = e.fs;
        for (const auto& e : focuseq::rateSections)
            if (exactly (e.fs, near) && e.index < ns) { auto& x = secs[e.index]; x.hz = e.hz; x.q = e.q; x.a = e.a; x.b = e.b; }
        for (auto& c : ap) c.assign (na, Biquad());
        for (size_t k = 0; k < na; ++k)     // the all-passes, as fitted at the same nearest rate where the table has them
        {
            double hz = focuseq::allpasses[k].hz, q = focuseq::allpasses[k].q;
            for (const auto& e : focuseq::rateAllpasses)
                if (exactly (e.fs, near) && e.index == k) { hz = e.hz; q = e.q; }
            const auto c = allPass (fs, clampHz (hz), q);
            ap[0][k].c = ap[1][k].c = c;
        }
        madeFocus = 1e9;
        auto coef = [&] (double ms) { return ms > 0 ? std::exp (-1.0 / (ms * 0.001 * fs)) : 0.0; };
        expAtt = coef (t.expAttackMs); expRel = coef (t.expReleaseMs);
        cmpAtt = coef (t.cmpAttackMs); cmpRelLow = coef (t.cmpReleaseLowMs); cmpRelHigh = coef (t.cmpReleaseHighMs);
        detCoef = coef (t.detRmsMs);
        expDetAtt = coef (t.expDetAttackMs); expDetRel = coef (t.expDetReleaseMs);
        trAvgAtt = coef (t.cmpTrAvgAttackMs); trAvgRel = coef (t.cmpTrAvgReleaseMs);
        trAtt = coef (t.cmpTrAttackMs); trRel = coef (t.cmpTrReleaseMs); trSm = coef (t.cmpTrSmoothMs);
        curveAt[0] = 0;             // the reduction at each knot of the measured curve
        for (size_t k = 1; k < Tuning::curveKnots; ++k)
            curveAt[k] = curveAt[k - 1] + 0.5 * t.cmpCurveStepDb * (t.cmpCurveSlope[k - 1] + t.cmpCurveSlope[k]);
        reset();
    }

    void reset()
    {
        for (auto& c : eq) for (auto& b : c) b.reset();
        for (auto& c : ap) for (auto& b : c) b.reset();
        expDb = 0; cmpDb = 0; rms = 0; expLev = 0; trAvg = 0; trDb = 0; trRed = 0;
    }

    // stereo in place; focus and the drive (dB) per sample from the engine's ramps; key: the side-chain's mid sample
    // the detector hears instead of the signal (our EXT switch; nullptr: the signal itself)
    inline void process (double& l, double& r, double focus, double driveDb, const double* key = nullptr)
    {
        if (! exactly (focus, madeFocus)) designEq (focus);
        const unsigned post = (unsigned) tun.charPostMask;
        for (size_t k = 0; k < eq[0].size(); ++k)
            if (((post >> k) & 1u) == 0) { l = eq[0][k].process (l); r = eq[1][k].process (r); }
        for (size_t k = 0; k < ap[0].size(); ++k) { l = ap[0][k].process (l); r = ap[1][k].process (r); }

        // the detector: the mid signal, peak or RMS
        const double m = key == nullptr ? 0.5 * (l + r) : *key;
        double lev;
        if (tun.detRmsMs > 0) { rms = m * m + detCoef * (rms - m * m); lev = 10.0 * std::log10 (rms + 1e-30) + tun.detRmsOffsetDb; }
        else lev = 20.0 * std::log10 (std::fabs (m) + 1e-15);

        // downward expander below its threshold, with a soft knee, on its own peak detector (a slow release: the
        // reference keeps its gain through the gaps between drum hits and closes over hundreds of ms on quiet tones)
        const double am = std::fabs (m);
        expLev = am + (am > expLev ? expDetAtt : expDetRel) * (expLev - am);
        const double eLev = tun.expDetReleaseMs > 0 ? 20.0 * std::log10 (expLev + 1e-15) : lev;
        const double eTarget = -knee (tun.expThresholdDb - eLev, tun.expKneeDb) * (tun.expRatio - 1.0);
        expDb = eTarget + (eTarget < expDb ? expAtt : expRel) * (expDb - eTarget);

        // the compressor on the driven signal
        const double cl = lev + expDb + driveDb;
        const double over = knee (cl - tun.cmpThresholdDb, tun.cmpKneeDb);
        const double cTarget = tun.cmpCurveStepDb > 0 ? -curve (cl) : -over * (1.0 - 1.0 / tun.cmpRatio);
        const double rel = -cmpDb > tun.cmpReleaseSwitchDb ? cmpRelHigh : cmpRelLow;
        cmpDb = cTarget + (cTarget < cmpDb ? cmpAtt : rel) * (cmpDb - cTarget);

        // the overshoot (MEASUREMENTS.md 4.4): a share of the reduction above its slow average, held and let go on
        // its own times (after a rise the reduction runs past its steady value; after a short burst it lets go slowly)
        if (tun.cmpTrAmount > 0)
        {
            trRed = -cmpDb + trSm * (trRed + cmpDb);       // the reduction, smoothed
            trAvg = trRed + (trRed > trAvg ? trAvgAtt : trAvgRel) * (trAvg - trRed);
            const double trTarget = tun.cmpTrAmount * std::fmax (0.0, trRed - trAvg);
            trDb = trTarget + (trTarget > trDb ? trAtt : trRel) * (trDb - trTarget);
        }

        const double g = std::pow (10.0, (expDb + driveDb + cmpDb - trDb + tun.cmpMakeupDb) / 20.0);
        l *= g;
        r *= g;
        if (tun.clipDrive > 0) { l = clip (l); r = clip (r); }
        for (size_t k = 0; k < eq[0].size(); ++k)       // sections that sit after the dynamics (charPostMask bits)
            if (((post >> k) & 1u) != 0) { l = eq[0][k].process (l); r = eq[1][k].process (r); }
    }

private:
    // the static curve as measured (cmpCurveStepDb > 0): the reduction's slope, in dB per dB of the driven level, at
    // knots cmpCurveStepDb apart from cmpCurveStartDb, linear between them, 0 below the first and held above the last
    double curve (double level) const
    {
        const double step = tun.cmpCurveStepDb, x = (level - tun.cmpCurveStartDb) / step;
        if (x <= 0) return 0;
        const auto& s = tun.cmpCurveSlope;
        if (x >= Tuning::curveKnots - 1)
            return curveAt[Tuning::curveKnots - 1] + s[Tuning::curveKnots - 1] * (x - (Tuning::curveKnots - 1)) * step;
        const auto k = (size_t) x;
        const double f = x - (double) k;
        return curveAt[k] + step * (s[k] * f + 0.5 * (s[k + 1] - s[k]) * f * f);
    }
    // the amount above a threshold with a quadratic soft knee of width w (dB)
    static double knee (double x, double w)
    {
        if (w <= 0) return x > 0 ? x : 0;
        if (x <= -0.5 * w) return 0;
        if (x >= 0.5 * w) return x;
        return (x + 0.5 * w) * (x + 0.5 * w) / (2.0 * w);
    }
    double clip (double x) const { return std::tanh (tun.clipDrive * x) / tun.clipDrive; }
    double clampHz (double hz) const { return std::fmin (hz, 0.49 * fs); }
    static Coeffs allPass (double fs, double f0, double q)
    {
        const double w0 = 2.0 * 3.14159265358979323846 * f0 / fs, c = std::cos (w0), al = std::sin (w0) / (2.0 * q);
        const double a0 = 1 + al;
        return { (1 - al) / a0, -2 * c / a0, (1 + al) / a0, -2 * c / a0, (1 - al) / a0 };
    }
    void designEq (double focus)
    {
        madeFocus = focus;
        for (size_t k = 0; k < eq[0].size(); ++k)
        {
            const auto& s = secs[k];
            const double hz = clampHz (s.hz), g = s.a + s.b * focus / 50.0;
            Coeffs c;
            switch (s.kind)
            {
                case focuseq::HighPass: c = Coeffs::highPass (fs, hz, s.q); break;
                case focuseq::LowPass: c = Coeffs::lowPass (fs, hz, s.q); break;
                case focuseq::Peak: c = Coeffs::peak (fs, hz, s.q, g); break;
                case focuseq::LowShelf: c = Coeffs::shelf (fs, hz, s.q, g, true); break;
                case focuseq::HighShelf: c = Coeffs::shelf (fs, hz, s.q, g, false); break;
            }
            eq[0][k].c = eq[1][k].c = c;
        }
    }

    double fs = 48000.0;
    Tuning tun;
    std::vector<Biquad> eq[2], ap[2];
    std::vector<focuseq::Section> secs;
    double madeFocus = 1e9;
    double expDb = 0, cmpDb = 0, rms = 0, expLev = 0, trAvg = 0, trDb = 0, trRed = 0;
    double expAtt = 0, expRel = 0, cmpAtt = 0, cmpRelLow = 0, cmpRelHigh = 0, detCoef = 0, expDetAtt = 0, expDetRel = 0;
    double trAvgAtt = 0, trAvgRel = 0, trAtt = 0, trRel = 0, trSm = 0;
    double curveAt[Tuning::curveKnots] {};
};
}
