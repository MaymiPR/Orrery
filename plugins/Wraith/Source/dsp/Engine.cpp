#include "Engine.h"
#include <algorithm>
#include <cmath>

namespace wr::dsp
{
static inline double dbToGain (double db) { return std::pow (10.0, db / 20.0); }

void Engine::prepare (double sampleRate, int, const Tuning& t)
{
    tun = t;
    fs = sampleRate;
    for (auto* c : { &inGain, &outGain, &revMix, &dblMix }) c->setRate (fs, t.smoothTauMs * 0.001);
    revFilterHz.setLength ((int) std::lround (t.filterRampMs * 0.001 * fs));
    focus.setLength ((int) std::lround (t.focusRampMs * 0.001 * fs));
    driveDb.setLength ((int) std::lround (t.driveRampMs * 0.001 * fs));
    character.prepare (fs, t);
    rider.prepare (fs, t);
    doubler.prepare (fs, t);
    reverb.prepare (fs, chunkSize);
    for (auto* ramp : { &eqLowDb, &eqHighDb })
    {
        ramp->setLength ((int) std::lround ((t.eqChunked > 0 ? t.glideMs : t.eqRampMs) * 0.001 * fs));
        ramp->setChunked (t.eqChunked > 0 ? chunkSize : 0, (int) std::lround (t.eqRampMs * 0.001 * fs));
    }
    reset();
}

void Engine::reset()
{
    for (auto* c : { &inGain, &outGain, &revMix, &dblMix }) c->snapped = false;
    started = false;
    eqLowMade = eqHighMade = 1e9;
    revFilterMade = -1;
    for (auto* b : { eqLow, eqLow + 1, eqHigh, eqHigh + 1, revLp, revLp + 1 }) b->reset();
    reverb.reset();
    character.reset();
    rider.reset();
    doubler.reset();
}

void Engine::process (float* l, float* r, int n, const Params& p, const float* keyL, const float* keyR)
{
    if (p.bypass) return;
    if (! started)
    {
        eqLowDb.jump (p.eqLowDb);
        eqHighDb.jump (p.eqHighDb);
        revFilterHz.jump (p.reverbFilterHz);
        focus.jump (p.focus);
        driveDb.jump (tun.driveDbPerStep * (p.compression + 50.0));
        started = true;
    }
    eqLowDb.set (p.eqLowDb);
    eqHighDb.set (p.eqHighDb);
    revFilterHz.set (p.reverbFilterHz);
    focus.set (p.focus);
    driveDb.set (tun.driveDbPerStep * (p.compression + 50.0));
    for (auto* ramp : { &eqLowDb, &eqHighDb, &revFilterHz, &focus, &driveDb }) ramp->beginBlock (n);
    for (int pos = 0; pos < n; pos += chunkSize)
        processChunk (l + pos, r + pos, std::min (chunkSize, n - pos), p, keyL != nullptr ? keyL + pos : nullptr,
                      keyR != nullptr ? keyR + pos : nullptr);
}

void Engine::processChunk (float* l, float* r, int n, const Params& p, const float* keyL, const float* keyR)
{
    inGain.advance (dbToGain (p.inputGainDb));
    outGain.advance (dbToGain (p.outputGainDb));
    revMix.advance (p.reverbMix);
    dblMix.advance (p.doublerMix);
    for (int i = 0; i < n; ++i)
    {
        const double gi = inGain.at (i);
        double xl = l[i] * gi, xr = r[i] * gi;
        const double fo = focus.next(), dr = driveDb.next();
        if (p.riderOn) rider.process (xl, xr, p.riderSpeed, p.riderAmount, p.riderFloorDb);
        if (p.characterOn)
        {
            const double key = keyL != nullptr && keyR != nullptr ? 0.5 * ((double) keyL[i] + (double) keyR[i]) : 0.0;
            character.process (xl, xr, fo, dr, keyL != nullptr && keyR != nullptr ? &key : nullptr);
        }
        const double gLow = eqLowDb.next(), gHigh = eqHighDb.next();
        if (p.eqOn)
        {
            if (! exactly (gLow, eqLowMade)) { eqLowMade = gLow; eqLow[0].c = eqLow[1].c = Coeffs::shelf (fs, tun.eqLowHz, tun.eqQ, gLow, true); }
            if (! exactly (gHigh, eqHighMade)) { eqHighMade = gHigh; eqHigh[0].c = eqHigh[1].c = Coeffs::shelf (fs, tun.eqHighHz, tun.eqQ, gHigh, false); }
            xl = eqHigh[0].process (eqLow[0].process (xl));
            xr = eqHigh[1].process (eqLow[1].process (xr));
        }
        sendL[i] = (float) xl;
        sendR[i] = (float) xr;
    }
    if (p.reverbOn) reverb.process (sendL, sendR, wetL, wetR, n, p.reverbType);
    for (int i = 0; i < n; ++i)
    {
        double xl = sendL[i], xr = sendR[i];
        const double fc = revFilterHz.next();
        if (p.reverbOn)
        {
            if (! exactly (fc, revFilterMade)) { revFilterMade = fc; revLp[0].c = revLp[1].c = Coeffs::lowPass (fs, fc, tun.revQ); }
            const double m = revMix.at (i);
            xl = (1.0 - m) * xl + m * revLp[0].process (wetL[i]);
            xr = (1.0 - m) * xr + m * revLp[1].process (wetR[i]);
        }
        // the doubler after the reverb, as the reference's chain runs (MEASUREMENTS.md 6.1)
        if (p.doublerOn)
        {
            double wl = xl, wr = xr;
            doubler.process (wl, wr, p.doublerStereo);
            const double m = dblMix.at (i);
            xl = (1.0 - m) * xl + m * wl;
            xr = (1.0 - m) * xr + m * wr;
        }
        const double go = outGain.at (i);
        l[i] = (float) (xl * go);
        r[i] = (float) (xr * go);
    }
}
}
