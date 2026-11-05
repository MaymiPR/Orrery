#pragma once
#include <algorithm>
#include "BandDynamics.h"
#include "Filters.h"
#include "FirBank.h"
#include "Tuning.h"

// The character section (MEASUREMENTS.md 3): a 3-band FIR split (FirBank; it carries the section's 3.15 ms delay);
// each band's nonlinear stage works on the band with steeper edges (s), the rest of the band passes linearly
// (y = x - s + F(s): the FIR bands' shallow stopbands are not compressed or shaped, MEASUREMENTS.md 3.11);
// the side-chain goes through a second copy of the same split, so the detectors hear it as they hear the input; per band a stereo-linked parallel
// compressor (dry + wet, the wet path compressed; the GR meters show the wet path's reduction; the detector hears the
// mid signal only) followed by a sine shaper (odd harmonics, H3 phase-locked at 180 degrees), the band's make-up gain
// and a side gain (the band widened, increasingly with the amount). Runs at the processing rate.
namespace po::dsp
{
class Character
{
public:
    // delaySamples: the section's latency at the processing rate (the FIR filters' delay)
    // exactRates: the FIR filters may be the reference's own ones for this rate (FirBank::prepare)
    // hostRate / hostDelay: with oversampling, the rate the filters are taken from and their delay there
    void prepare (double processingRate, double delaySamples, const Tuning& t, bool exactRates = false,
                  double hostRate = 48000.0, double hostDelay = 151.27917)
    {
        fs = processingRate;
        tune = &t;
        firs.prepare (fs, delaySamples, exactRates, hostRate, hostDelay);
        scFirs.prepare (fs, delaySamples, exactRates, hostRate, hostDelay);
        reset();
        lastAmount = -1.0;
    }
    void reset()
    {
        firs.reset(); scFirs.reset();
        for (auto& d : dyn) d.reset();
        for (auto& g : grMax) g = 0.0;
    }

    // amount 0 .. 1 (= 0 .. 200 %); interpolates the tabled band settings
    void setAmount (double amount)
    {
        if (exactly (amount, lastAmount)) return;
        lastAmount = amount;
        atZero = amount <= 0.0 && tune->charZeroRest > 0.5;
        const double x = std::clamp (amount, 0.0, 1.0) * (kAmountNodes - 1);
        const int k = std::min (kAmountNodes - 2, (int) x);
        const double f = x - k;
        for (int b = 0; b < 3; ++b)
        {
            double p[kBandParams];
            for (int q = 0; q < kBandParams; ++q) p[q] = tune->band[b][k][q] + (tune->band[b][k + 1][q] - tune->band[b][k][q]) * f;
            auto& s = st[b];
            s.makeup = std::pow (10.0, p[bpMakeup] / 20.0);
            // the shaper is sin (k u) / k (identified per cycle: u - c u^3 + 0.3 c^2 u^5 ..., nulltest/ident.py);
            // the tables keep c = k^2 / 6, its cubic coefficient
            s.drive = std::sqrt (std::max (0.0, 6.0 * p[bpCubic]));
            s.width = std::pow (10.0, p[bpWidth] / 20.0);
            s.dry = std::clamp (p[bpShapeDry], -1.0, 1.0);    // the high band's is slightly negative from 100 %
            s.shapeMid = p[bpShapeMid];
            dyn[b].configure (p, tune->detectorPeak[b], tune->feedback[b] != 0, fs);
        }
    }

    // one stereo sample in place; sc = the external side-chain sample (nullptr: the input drives the detectors)
    inline void process (double& l, double& r, const double* scL = nullptr, const double* scR = nullptr)
    {
        double bl[FirBank::kFilters], br[FirBank::kFilters];
        firs.process (0, l, bl);
        firs.process (1, r, br);
        if (scL == nullptr) { bands (l, r, bl, br, nullptr, nullptr); return; }
        double cl[FirBank::kFilters], cr[FirBank::kFilters];
        scFirs.process (0, *scL, cl);
        scFirs.process (1, *scR, cr);
        bands (l, r, bl, br, cl, cr);
    }
    // the same for a stretch of n samples (up to maxStretch) in two passes: the crossover across all of them
    // (crossover, and crossoverSidechain for EXT), then each sample's bands in turn (processAt)
    static constexpr int maxStretch = 256;
    void crossover (const double* l, const double* r, int n)
    {
        double* ol[FirBank::kFilters]; double* orr[FirBank::kFilters];
        for (int b = 0; b < FirBank::kFilters; ++b) { ol[b] = split[0][b]; orr[b] = split[1][b]; }
        firs.processBlock (0, l, n, ol);
        firs.processBlock (1, r, n, orr);
    }
    void crossoverSidechain (const double* l, const double* r, int n)
    {
        double* ol[FirBank::kFilters]; double* orr[FirBank::kFilters];
        for (int b = 0; b < FirBank::kFilters; ++b) { ol[b] = scSplit[0][b]; orr[b] = scSplit[1][b]; }
        scFirs.processBlock (0, l, n, ol);
        scFirs.processBlock (1, r, n, orr);
    }
    // sidechain: the stretch's side-chain was split too (crossoverSidechain) and drives the detectors
    inline void processAt (int i, double& l, double& r, bool sidechain = false)
    {
        double bl[FirBank::kFilters], br[FirBank::kFilters];
        for (int b = 0; b < FirBank::kFilters; ++b) { bl[b] = split[0][b][i]; br[b] = split[1][b][i]; }
        if (! sidechain) { bands (l, r, bl, br, nullptr, nullptr); return; }
        double cl[FirBank::kFilters], cr[FirBank::kFilters];
        for (int b = 0; b < FirBank::kFilters; ++b) { cl[b] = scSplit[0][b][i]; cr[b] = scSplit[1][b][i]; }
        bands (l, r, bl, br, cl, cr);
    }

private:
    // the bands' processing of one stereo sample, given the crossover's outputs (cl / cr: the side-chain's, or nullptr)
    inline void bands (double& l, double& r, const double* bl, const double* br, const double* cl, const double* cr)
    {
        if (atZero) for (auto& d : dyn) d.reset();
        double dl[3], dr[3];
        const double* sl = bl + 3;      // what the nonlinear stages hear
        const double* sr = br + 3;
        if (cl != nullptr)
            for (int b = 0; b < 3; ++b) { dl[b] = cl[b + 3]; dr[b] = cr[b + 3]; }
        else
            for (int b = 0; b < 3; ++b) { dl[b] = sl[b]; dr[b] = sr[b]; }

        l = r = 0.0;
        for (int b = 0; b < 3; ++b)
        {
            const auto& s = st[b];
            const double n = dyn[b].step (0.5 * (dl[b] + dr[b]), 0.5 * (dl[b] - dr[b]), cl != nullptr);
            grMax[b] = std::max (grMax[b], dyn[b].gr);
            double yl = sl[b] * n, yr = sr[b] * n, extraMid = 0.0;
            if (s.drive > 1.0e-6)
            {
                // y = d u + (1 - d) sin (k u) / k, as u plus its distortion
                const double el = (1.0 - s.dry) * (std::sin (s.drive * yl) / s.drive - yl);
                const double er = (1.0 - s.dry) * (std::sin (s.drive * yr) / s.drive - yr);
                yl += el; yr += er;
                extraMid = 0.5 * s.shapeMid * (el + er);
            }
            yl += bl[b] - sl[b];
            yr += br[b] - sr[b];
            const double m = s.makeup * (0.5 * (yl + yr) + extraMid), sd = 0.5 * s.makeup * s.width * (yl - yr);
            l += m + sd;
            r += m - sd;
        }
    }

public:
    // deepest wet-path reduction (dB, positive) per band since the last call: low, mid, high
    void takeGr (float* out)
    {
        for (int b = 0; b < 3; ++b) { out[b] = (float) grMax[b]; grMax[b] = 0.0; }
    }

private:
    struct Band { double makeup = 1, drive = 0, width = 1, dry = 0, shapeMid = 0; };
    double fs = 48000.0, lastAmount = -1.0;
    bool atZero = false;
    const Tuning* tune = nullptr;
    FirBank firs, scFirs;
    Band st[3];
    BandDynamics dyn[3];
    double grMax[3] {};
    double split[2][FirBank::kFilters][maxStretch] {};     // a stretch's crossover outputs (crossover, processAt)
    double scSplit[2][FirBank::kFilters][maxStretch] {};   // the same for the side-chain (crossoverSidechain)
};
}
