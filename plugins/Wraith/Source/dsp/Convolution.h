#pragma once
#include <cstddef>
#include <memory>
#include <vector>
#include "shared/dsp/Fft.h"

// The reverb's convolution (Reverb.h), plain C++: the zero-latency non-uniformly partitioned form of JUCE's
// juce::dsp::Convolution with a 256-sample head, in the same order of operations, so its output is the same to the
// last bit wherever juce::dsp::FFT runs its own fallback FFT (Windows, Linux).
//   UniformConvolution: one channel, overlap-add over FFT segments of a fixed block size, with no latency or one block
//                       late
//   Convolution:        a stereo response: its first 256 samples at the host's block size with no latency, the rest at
//                       blocks of 256 run one block late, so that it lands right after the head
//   resampleResponse:   a response at another rate (two-pole low-pass and linear interpolation), as JUCE's
//                       ResamplingAudioSource does it
namespace wr::dsp
{
class UniformConvolution
{
public:
    UniformConvolution (const float* samples, size_t numSamples, size_t maxBlockSize);
    void reset();
    void process (const float* input, float* output, size_t numSamples);                // input and output may be one
    void processOneBlockLate (const float* input, float* output, size_t numSamples);

private:
    void prepareForConvolution (float* samples) const;
    void accumulate (const float* input, const float* impulse, float* output) const;
    void updateSymmetricFrequencyDomainData (float* samples) const;

    const size_t blockSize, fftSize;
    orrery::Fft fft;
    const size_t numSegments, numInputSegments;
    size_t currentSegment = 0, inputDataPos = 0;
    std::vector<float> bufferInput, bufferOutput, bufferTempOutput, bufferOverlap;
    std::vector<std::vector<float>> inputSegments, impulseSegments;
};

class Convolution
{
public:
    // left and right hold n samples each of a response at responseRate; maxBlock bounds every process() call
    void prepare (const float* left, const float* right, int n, double responseRate, double sampleRate, int maxBlock);
    void reset();
    void process (float* l, float* r, int n);                                            // in place

private:
    std::unique_ptr<UniformConvolution> head[2], tail[2];
    std::vector<float> tailBuffer;
};

// a response of n samples at fromRate as the same response at toRate (round (n * toRate / fromRate) samples)
std::vector<float> resampleResponse (const float* samples, int n, double fromRate, double toRate);
}
