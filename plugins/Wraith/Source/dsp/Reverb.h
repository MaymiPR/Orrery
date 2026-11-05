#pragma once
#include <juce_dsp/juce_dsp.h>
#include <array>
#include <memory>
#include "Biquad.h"

// The reverb (MEASUREMENTS.md "Reverb"): the reference's measured room and plate responses at the nearest of
// 44.1 / 48 / 88.2 / 96 kHz (nulltest/pack_reverb.py), left and right independent, run by zero-latency convolutions;
// the wet signal then passes an RBJ low-pass (Q 0.7) at the Filter frequency. Mix crossfades linearly: the caller
// gives out = (1 - m) dry + m wet.
namespace wr::dsp
{
class Reverb
{
public:
    void prepare (double fs, int block);
    void reset();
    bool hasResponse (int type) const { return conv[(size_t) type] != nullptr; }

    // wet signal of one reverb (0 room, 1 plate) into wl / wr, for n samples of in l / r
    void process (const float* l, const float* r, float* wl, float* wr, int n, int type);

private:
    std::array<std::unique_ptr<juce::dsp::Convolution>, 2> conv;
    juce::AudioBuffer<float> buf;
    int running = -1;
};
}
