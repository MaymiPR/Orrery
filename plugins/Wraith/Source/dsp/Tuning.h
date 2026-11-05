#pragma once
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>

// Every constant of the DSP, from the measurements (MEASUREMENTS.md) and the fits (nulltest/fit_*.py). Kept in one
// struct so the offline renderer (tools/WrRender.cpp) can override any of them by name while fitting
// (tune:key=value); the plug-in uses the defaults. Add a field and a line in set() per constant; the comment names
// the MEASUREMENTS.md section that decided it.
namespace wr::dsp
{
struct Tuning
{
    double smoothTauMs = 9.98;       // MEASUREMENTS.md "Smoothing": the control-rate one-pole (k = 128 / fs / tau)
    double eqLowHz = 200.0, eqHighHz = 5000.0, eqQ = 0.7;   // MEASUREMENTS.md "EQ": RBJ shelves, exact at every rate
    double eqRampMs = 5.0, glideMs = 5.0, eqChunked = 0;     // MEASUREMENTS.md "Smoothing": how the EQ gains move
    // MEASUREMENTS.md "Rider": the static law (exact) and the detector timing (fitted by nulltest/fit_rider.py)
    double riderOffsetDb = 16.0;
    double riderMaxBoostDb = 20.0;
    double riderMaxCutDb = 30.0;
    double riderGateWidth = 0.2;
    double riderAttackScale = 1.0;
    double riderReleaseMs = 100.0;
    double riderSmoothMs = 0.0;
    // MEASUREMENTS.md "Doubler": the modulation and stereo matrix (measured), the voices' filters and the lows that pass
    // the line (regressed on the voices' tracked delays, then refined on the nulls: nulltest/fit_voice_filter.py,
    // fit_dbl_voice.py)
    double dblCenterMs = 7.52042;       // centre, depth, rate and phase matched to the reference's tracked delays
    double dblDepthMs = 1.50281;        // (nulltest/probe_dbl_rate.py, MEASUREMENTS.md 7.1)
    double dblRateHz = 0.0;             // 0: the measured rate at the sample rate (Doubler::rateAt); else this rate
    double dblPhase = 0.99722;
    double dblVoiceGain = 0.33961;
    double dblLpHz = 15509.0;
    double dblLpQ = 0.2622;
    double dblDryGain = 1.0017;
    double dblStereoK = 1.6364;
    double dblInterp = 1.0;
    double dblLp2Hz = 6727.3;           // a second low-pass and a first-order high-pass per voice (0: off)
    double dblLp2Q = 0.541;
    double dblHpHz = 507.66;
    double dblBassHz = 91.094;          // the lows that pass the line: an RBJ low-pass of the mid signal, added (0: off)
    double dblBassQ = 0.8442;
    double dblBassGain = 1.0472;
    // MEASUREMENTS.md "Character": the dynamics after the Focus EQ (nulltest/fit_char.py; the expander
    // and its own detector from the reference's gain, nulltest/fit_expander.py, MEASUREMENTS.md 4.3)
    double expThresholdDb = -40.0224;
    double expRatio = 2.18047;
    double expKneeDb = 12.1528;
    double expAttackMs = 5.86141;
    double expReleaseMs = 0.406733;
    double cmpThresholdDb = -16.513105;
    double cmpRatio = 33.420335;
    double cmpKneeDb = 6.581593;
    double cmpAttackMs = 1.342135;
    double cmpReleaseLowMs = 38.968717;    // the release times refitted with the overshoot (fit_overshoot.py)
    double cmpReleaseHighMs = 82.398575;
    double cmpReleaseSwitchDb = 6.477767;
    double cmpMakeupDb = 0.095455;         // refitted with the static curve's table (fit_curve.py)
    double detRmsMs = 0.0;
    double detRmsOffsetDb = 0.0;
    double clipDrive = 0.0;
    double expDetAttackMs = 0.114;    // the expander's own peak detector (release 0: the instantaneous level)
    double expDetReleaseMs = 266.5;
    double charPostMask = 0.0;         // bit k: Focus EQ section k after the dynamics instead of before
    // MEASUREMENTS.md 4.4, the compressor's overshoot (amount 0: off): extra reduction while the reduction, smoothed,
    // stands above its slow average (nulltest/fit_overshoot.py --dynamics-only)
    double cmpTrAmount = 0.517621, cmpTrAvgAttackMs = 51.330868, cmpTrAvgReleaseMs = 35.457249,
           cmpTrAttackMs = 9.797586, cmpTrReleaseMs = 142.887700, cmpTrSmoothMs = 9.834373;
    // MEASUREMENTS.md 4.1, the compressor's static curve as a table: the reduction's slope (dB per dB of the driven
    // level) at knots cmpCurveStepDb apart from cmpCurveStartDb (nulltest/fit_curve.py --penalty 5); step 0: the
    // threshold, ratio and knee above instead
    static constexpr size_t curveKnots = 9;
    double cmpCurveStepDb = 5.0, cmpCurveStartDb = -27.520086;
    double cmpCurveSlope[curveKnots] { 0.129259, 0.123322, 0.028830, 0.933917, 0.991675, 1.0, 1.0, 0.942705, 0.966171 };
    double driveDbPerStep = 0.2;
    double focusRampMs = 5.0;
    double driveRampMs = 5.0;
    double revQ = 0.7, filterRampMs = 5.0;                   // MEASUREMENTS.md "Reverb": the wet low-pass and its moves

    // sets a constant by name; false for an unknown key
    bool set (const std::string& key, double v)
    {
        if (key == "smoothTauMs") { smoothTauMs = v; return true; }
        if (key == "eqLowHz") { eqLowHz = v; return true; }
        if (key == "eqHighHz") { eqHighHz = v; return true; }
        if (key == "eqQ") { eqQ = v; return true; }
        if (key == "eqRampMs") { eqRampMs = v; return true; }
        if (key == "glideMs") { glideMs = v; return true; }
        if (key == "eqChunked") { eqChunked = v; return true; }
        if (key == "expThresholdDb") { expThresholdDb = v; return true; }
        if (key == "expRatio") { expRatio = v; return true; }
        if (key == "expKneeDb") { expKneeDb = v; return true; }
        if (key == "expAttackMs") { expAttackMs = v; return true; }
        if (key == "expReleaseMs") { expReleaseMs = v; return true; }
        if (key == "cmpThresholdDb") { cmpThresholdDb = v; return true; }
        if (key == "cmpRatio") { cmpRatio = v; return true; }
        if (key == "cmpKneeDb") { cmpKneeDb = v; return true; }
        if (key == "cmpAttackMs") { cmpAttackMs = v; return true; }
        if (key == "cmpReleaseLowMs") { cmpReleaseLowMs = v; return true; }
        if (key == "cmpReleaseHighMs") { cmpReleaseHighMs = v; return true; }
        if (key == "cmpReleaseSwitchDb") { cmpReleaseSwitchDb = v; return true; }
        if (key == "cmpMakeupDb") { cmpMakeupDb = v; return true; }
        if (key == "detRmsMs") { detRmsMs = v; return true; }
        if (key == "detRmsOffsetDb") { detRmsOffsetDb = v; return true; }
        if (key == "clipDrive") { clipDrive = v; return true; }
        if (key == "expDetAttackMs") { expDetAttackMs = v; return true; }
        if (key == "expDetReleaseMs") { expDetReleaseMs = v; return true; }
        if (key == "charPostMask") { charPostMask = v; return true; }
        if (key == "cmpTrAmount") { cmpTrAmount = v; return true; }
        if (key == "cmpTrAvgAttackMs") { cmpTrAvgAttackMs = v; return true; }
        if (key == "cmpTrAvgReleaseMs") { cmpTrAvgReleaseMs = v; return true; }
        if (key == "cmpTrAttackMs") { cmpTrAttackMs = v; return true; }
        if (key == "cmpTrReleaseMs") { cmpTrReleaseMs = v; return true; }
        if (key == "cmpTrSmoothMs") { cmpTrSmoothMs = v; return true; }
        if (key == "cmpCurveStepDb") { cmpCurveStepDb = v; return true; }
        if (key == "cmpCurveStartDb") { cmpCurveStartDb = v; return true; }
        for (size_t k = 0; k < curveKnots; ++k)
            if (key == "cmpCurveSlope" + std::to_string (k)) { cmpCurveSlope[k] = v; return true; }
        if (key == "driveDbPerStep") { driveDbPerStep = v; return true; }
        if (key == "focusRampMs") { focusRampMs = v; return true; }
        if (key == "driveRampMs") { driveRampMs = v; return true; }
        if (key == "riderOffsetDb") { riderOffsetDb = v; return true; }
        if (key == "riderMaxBoostDb") { riderMaxBoostDb = v; return true; }
        if (key == "riderMaxCutDb") { riderMaxCutDb = v; return true; }
        if (key == "riderGateWidth") { riderGateWidth = v; return true; }
        if (key == "riderAttackScale") { riderAttackScale = v; return true; }
        if (key == "riderReleaseMs") { riderReleaseMs = v; return true; }
        if (key == "riderSmoothMs") { riderSmoothMs = v; return true; }
        if (key == "dblCenterMs") { dblCenterMs = v; return true; }
        if (key == "dblDepthMs") { dblDepthMs = v; return true; }
        if (key == "dblRateHz") { dblRateHz = v; return true; }
        if (key == "dblPhase") { dblPhase = v; return true; }
        if (key == "dblVoiceGain") { dblVoiceGain = v; return true; }
        if (key == "dblLpHz") { dblLpHz = v; return true; }
        if (key == "dblLpQ") { dblLpQ = v; return true; }
        if (key == "dblLp2Hz") { dblLp2Hz = v; return true; }
        if (key == "dblLp2Q") { dblLp2Q = v; return true; }
        if (key == "dblHpHz") { dblHpHz = v; return true; }
        if (key == "dblBassHz") { dblBassHz = v; return true; }
        if (key == "dblBassQ") { dblBassQ = v; return true; }
        if (key == "dblBassGain") { dblBassGain = v; return true; }
        if (key == "dblDryGain") { dblDryGain = v; return true; }
        if (key == "dblStereoK") { dblStereoK = v; return true; }
        if (key == "dblInterp") { dblInterp = v; return true; }
        if (key == "revQ") { revQ = v; return true; }
        if (key == "filterRampMs") { filterRampMs = v; return true; }
        return false;
    }

    // key=value lines, one per line; returns 0 or the number of the first bad line
    int load (const char* path)
    {
        std::ifstream f (path);
        if (! f) { std::printf ("cannot read tuning file %s\n", path); return 1; }
        std::string s;
        int n = 0;
        while (std::getline (f, s))
        {
            ++n;
            while (! s.empty() && (s.back() == '\r' || s.back() == ' ')) s.pop_back();
            if (s.empty() || s[0] == '#') continue;
            const auto eq = s.find ('=');
            if (eq == std::string::npos || ! set (s.substr (0, eq), std::strtod (s.c_str() + eq + 1, nullptr)))
            {
                std::printf ("bad tuning line %d: %s\n", n, s.c_str());
                return n;
            }
        }
        return 0;
    }
};

// the tuning in use: the defaults in the plug-in, overridden per job by WrRender
inline Tuning& tuning()
{
    static Tuning t;
    return t;
}
}
