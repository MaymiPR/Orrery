#pragma once
#include <vector>
#include "Biquad.h"
#include "Character.h"
#include "Doubler.h"
#include "Rider.h"
#include "ControlRate.h"
#include "Ramp.h"
#include "Reverb.h"
#include "Tuning.h"

// The whole audio path (MEASUREMENTS.md):
//   input gain -> rider -> character -> eq -> reverb -> doubler -> output gain
// Plain C++ apart from the reverb's convolutions (juce_dsp). The host bypass gives the input unchanged
// (the reference reports no latency). Parameters arrive once per block in Params; the engine runs in 128-sample
// chunks and smooths every continuous parameter at that control rate, as the reference does.
namespace wr::dsp
{
struct Params
{
    float inputGainDb = 0.0f, outputGainDb = 0.0f;
    bool riderOn = false; float riderSpeed = 0.003f, riderAmount = 0.7f, riderFloorDb = -30.0f;
    bool characterOn = false; float compression = 0.0f, focus = 0.0f;
    bool eqOn = false; float eqLowDb = 0.0f, eqHighDb = 0.0f;
    bool doublerOn = false; float doublerStereo = 0.5f, doublerMix = 0.1f;
    bool reverbOn = false; float reverbFilterHz = 20000.0f, reverbMix = 0.1f; int reverbType = 0;
    bool bypass = false;
};

class Engine
{
public:
    void prepare (double sampleRate, int maxBlock, const Tuning&);
    void reset();
    int latency() const { return 0; }

    // stereo in place; keyL / keyR: the side-chain the character section listens to instead (nullptr: the signal)
    void process (float* l, float* r, int n, const Params&, const float* keyL = nullptr, const float* keyR = nullptr);

private:
    void processChunk (float* l, float* r, int n, const Params&, const float* keyL, const float* keyR);

    Tuning tun;
    double fs = 48000.0;
    ControlRate inGain, outGain;
    Rider rider;
    // character (MEASUREMENTS.md "Character"): Focus and the drive move on linear ramps
    Character character;
    Ramp focus, driveDb;
    // EQ (MEASUREMENTS.md "EQ"): low then high shelf per channel; the gains (dB) move on linear ramps
    Ramp eqLowDb, eqHighDb;
    double eqLowMade = 1e9, eqHighMade = 1e9;     // the gains the coefficients were made for
    bool started = false;
    Biquad eqLow[2], eqHigh[2];
    // doubler (MEASUREMENTS.md "Doubler"): the wet signal crossfaded with the dry by Mix
    Doubler doubler;
    ControlRate dblMix;
    // reverb (MEASUREMENTS.md "Reverb"): convolution, then the low-pass on the wet signal, then the linear crossfade
    Reverb reverb;
    ControlRate revMix;
    Ramp revFilterHz;
    double revFilterMade = -1;
    Biquad revLp[2];
    float sendL[chunkSize] {}, sendR[chunkSize] {}, wetL[chunkSize] {}, wetR[chunkSize] {};
};
}
