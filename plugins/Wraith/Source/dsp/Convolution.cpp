#include "Convolution.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>

namespace wr::dsp
{
namespace
{
int nextPowerOfTwo (int n)
{
    --n;
    n |= (n >> 1);
    n |= (n >> 2);
    n |= (n >> 4);
    n |= (n >> 8);
    n |= (n >> 16);
    return n + 1;
}

// to the nearest integer, ties to even (the FPU's rounding), as JUCE's roundToInt
int roundToInt (double v)
{
    const double shifted = v + 6755399441055744.0;
    std::int64_t bits;
    std::memcpy (&bits, &shifted, sizeof bits);
    return (int) (std::int32_t) (std::uint32_t) (bits & 0xffffffff);
}

template <typename T>
bool approximatelyEqual (T a, T b)
{
    if (! (std::isfinite (a) && std::isfinite (b))) return a == b;
    const T diff = std::abs (a - b);
    return diff <= std::numeric_limits<T>::min() || diff <= std::numeric_limits<T>::epsilon() * std::max (std::abs (a), std::abs (b));
}
}

//==============================================================================
UniformConvolution::UniformConvolution (const float* samples, size_t numSamples, size_t maxBlockSize)
    : blockSize ((size_t) nextPowerOfTwo ((int) maxBlockSize)),
      fftSize (blockSize > 128 ? 2 * blockSize : 4 * blockSize),
      fft ((int) std::lround (std::log2 ((double) fftSize))),
      numSegments (numSamples / (fftSize - blockSize) + 1u),
      numInputSegments (blockSize > 128 ? numSegments : 3 * numSegments),
      bufferInput (fftSize, 0.0f), bufferOutput (fftSize * 2, 0.0f), bufferTempOutput (fftSize * 2, 0.0f),
      bufferOverlap (fftSize, 0.0f),
      inputSegments (numInputSegments, std::vector<float> (fftSize * 2, 0.0f)),
      impulseSegments (numSegments, std::vector<float> (fftSize * 2, 0.0f))
{
    size_t currentPtr = 0;
    for (auto& segment : impulseSegments)
    {
        float* impulseResponse = segment.data();
        if (&segment == &impulseSegments.front()) impulseResponse[0] = 1.0f;
        const size_t count = std::min (fftSize - blockSize, numSamples - currentPtr);
        std::copy (samples + currentPtr, samples + currentPtr + count, impulseResponse);
        fft.forwardReal (impulseResponse);
        prepareForConvolution (impulseResponse);
        currentPtr += fftSize - blockSize;
    }
    reset();
}

void UniformConvolution::reset()
{
    for (auto* b : { &bufferInput, &bufferOverlap, &bufferTempOutput, &bufferOutput }) std::fill (b->begin(), b->end(), 0.0f);
    for (auto& segment : inputSegments) std::fill (segment.begin(), segment.end(), 0.0f);
    currentSegment = 0;
    inputDataPos = 0;
}

void UniformConvolution::process (const float* input, float* output, size_t numSamples)
{
    // overlap-add with uniform partitions and no latency: every call transforms the block so far
    size_t numSamplesProcessed = 0;
    const size_t indexStep = numInputSegments / numSegments;
    float* inputData = bufferInput.data();
    float* outputTempData = bufferTempOutput.data();
    float* outputData = bufferOutput.data();
    float* overlapData = bufferOverlap.data();

    while (numSamplesProcessed < numSamples)
    {
        const bool inputDataWasEmpty = inputDataPos == 0;
        const size_t numSamplesToProcess = std::min (numSamples - numSamplesProcessed, blockSize - inputDataPos);
        std::copy (input + numSamplesProcessed, input + numSamplesProcessed + numSamplesToProcess, inputData + inputDataPos);

        float* inputSegmentData = inputSegments[currentSegment].data();
        std::copy (inputData, inputData + fftSize, inputSegmentData);
        fft.forwardReal (inputSegmentData);
        prepareForConvolution (inputSegmentData);

        // the older segments' products, once per block
        if (inputDataWasEmpty)
        {
            std::fill (outputTempData, outputTempData + fftSize + 1, 0.0f);
            size_t index = currentSegment;
            for (size_t i = 1; i < numSegments; ++i)
            {
                index += indexStep;
                if (index >= numInputSegments) index -= numInputSegments;
                accumulate (inputSegments[index].data(), impulseSegments[i].data(), outputTempData);
            }
        }

        std::copy (outputTempData, outputTempData + fftSize + 1, outputData);
        accumulate (inputSegmentData, impulseSegments.front().data(), outputData);
        updateSymmetricFrequencyDomainData (outputData);
        fft.inverseReal (outputData);

        for (size_t i = 0; i < numSamplesToProcess; ++i)
            output[numSamplesProcessed + i] = outputData[inputDataPos + i] + overlapData[inputDataPos + i];

        inputDataPos += numSamplesToProcess;
        if (inputDataPos == blockSize)
        {
            std::fill (inputData, inputData + fftSize, 0.0f);
            inputDataPos = 0;
            for (size_t i = blockSize; i < fftSize - blockSize; ++i) outputData[i] += overlapData[i];
            std::copy (outputData + blockSize, outputData + fftSize, overlapData);
            currentSegment = currentSegment > 0 ? currentSegment - 1 : numInputSegments - 1;
        }
        numSamplesProcessed += numSamplesToProcess;
    }
}

void UniformConvolution::processOneBlockLate (const float* input, float* output, size_t numSamples)
{
    // the same partitions, transformed once per full block: the output is the previous block's result
    size_t numSamplesProcessed = 0;
    const size_t indexStep = numInputSegments / numSegments;
    float* inputData = bufferInput.data();
    float* outputTempData = bufferTempOutput.data();
    float* outputData = bufferOutput.data();
    float* overlapData = bufferOverlap.data();

    while (numSamplesProcessed < numSamples)
    {
        const size_t numSamplesToProcess = std::min (numSamples - numSamplesProcessed, blockSize - inputDataPos);
        std::copy (input + numSamplesProcessed, input + numSamplesProcessed + numSamplesToProcess, inputData + inputDataPos);
        std::copy (outputData + inputDataPos, outputData + inputDataPos + numSamplesToProcess, output + numSamplesProcessed);
        numSamplesProcessed += numSamplesToProcess;
        inputDataPos += numSamplesToProcess;

        if (inputDataPos == blockSize)
        {
            float* inputSegmentData = inputSegments[currentSegment].data();
            std::copy (inputData, inputData + fftSize, inputSegmentData);
            fft.forwardReal (inputSegmentData);
            prepareForConvolution (inputSegmentData);

            std::fill (outputTempData, outputTempData + fftSize + 1, 0.0f);
            size_t index = currentSegment;
            for (size_t i = 1; i < numSegments; ++i)
            {
                index += indexStep;
                if (index >= numInputSegments) index -= numInputSegments;
                accumulate (inputSegments[index].data(), impulseSegments[i].data(), outputTempData);
            }
            std::copy (outputTempData, outputTempData + fftSize + 1, outputData);
            accumulate (inputSegmentData, impulseSegments.front().data(), outputData);
            updateSymmetricFrequencyDomainData (outputData);
            fft.inverseReal (outputData);

            for (size_t i = 0; i < blockSize; ++i) outputData[i] += overlapData[i];
            std::fill (inputData, inputData + fftSize, 0.0f);
            for (size_t i = blockSize; i < fftSize - blockSize; ++i) outputData[i] += overlapData[i];
            std::copy (outputData + blockSize, outputData + fftSize, overlapData);
            currentSegment = currentSegment > 0 ? currentSegment - 1 : numInputSegments - 1;
            inputDataPos = 0;
        }
    }
}

// after each FFT: the real parts, then the negated imaginary parts, of the lower half of the bins
void UniformConvolution::prepareForConvolution (float* samples) const
{
    const size_t half = fftSize / 2;
    for (size_t i = 0; i < half; i++) samples[i] = samples[i << 1];
    samples[half] = 0;
    for (size_t i = 1; i < half; i++) samples[i + half] = -samples[((fftSize - i) << 1) + 1];
}

// output += input * impulse over the lower half of the bins, in that layout
void UniformConvolution::accumulate (const float* input, const float* impulse, float* output) const
{
    const size_t half = fftSize / 2;
    for (size_t i = 0; i < half; ++i) output[i] += input[i] * impulse[i];
    for (size_t i = 0; i < half; ++i) output[i] -= input[half + i] * impulse[half + i];
    for (size_t i = 0; i < half; ++i) output[half + i] += input[i] * impulse[half + i];
    for (size_t i = 0; i < half; ++i) output[half + i] += input[half + i] * impulse[i];
    output[fftSize] += input[fftSize] * impulse[fftSize];
}

// back to interleaved bins, the upper half the conjugate mirror, for the inverse transform
void UniformConvolution::updateSymmetricFrequencyDomainData (float* samples) const
{
    const size_t half = fftSize / 2;
    for (size_t i = 1; i < half; i++)
    {
        samples[(fftSize - i) << 1] = samples[i];
        samples[((fftSize - i) << 1) + 1] = -samples[half + i];
    }
    samples[1] = 0.f;
    for (size_t i = 1; i < half; i++)
    {
        samples[i << 1] = samples[(fftSize - i) << 1];
        samples[(i << 1) + 1] = -samples[((fftSize - i) << 1) + 1];
    }
}

//==============================================================================
void Convolution::prepare (const float* left, const float* right, int n, double responseRate, double sampleRate, int maxBlock)
{
    constexpr int headSize = 256;
    std::vector<float> response[2];
    const float* source[2] { left, right };
    for (int c = 0; c < 2; ++c)
    {
        response[c] = approximatelyEqual (responseRate, sampleRate) ? std::vector<float> (source[c], source[c] + n)
                                                                     : resampleResponse (source[c], n, responseRate, sampleRate);
        const float gain = (float) (responseRate / sampleRate);       // the same energy per second at the new rate
        if (! approximatelyEqual (gain, 1.0f))
            for (auto& v : response[c]) v *= gain;
    }
    const size_t length = response[0].size(), size = std::min (length, (size_t) headSize);
    for (int c = 0; c < 2; ++c)
    {
        head[c] = std::make_unique<UniformConvolution> (response[c].data(), size, (size_t) maxBlock);
        tail[c].reset();
        if (size != length) tail[c] = std::make_unique<UniformConvolution> (response[c].data() + size, length - size, (size_t) headSize);
    }
    tailBuffer.assign ((size_t) std::max (1, maxBlock), 0.0f);
}

void Convolution::reset()
{
    for (auto& e : head) if (e != nullptr) e->reset();
    for (auto& e : tail) if (e != nullptr) e->reset();
}

void Convolution::process (float* l, float* r, int n)
{
    float* ch[2] { l, r };
    for (int c = 0; c < 2; ++c)
    {
        if (tail[c] != nullptr) tail[c]->processOneBlockLate (ch[c], tailBuffer.data(), (size_t) n);
        head[c]->process (ch[c], ch[c], (size_t) n);
        if (tail[c] != nullptr)
            for (int i = 0; i < n; ++i) ch[c][i] += tailBuffer[(size_t) i];
    }
}

//==============================================================================
std::vector<float> resampleResponse (const float* samples, int n, double fromRate, double toRate)
{
    const double ratio = fromRate / toRate;                                   // input samples per output sample
    const int finalSize = roundToInt (std::max (1.0, n / ratio));
    const int sampsNeeded = roundToInt (finalSize * ratio) + 3;
    std::vector<float> buffer ((size_t) (roundToInt (finalSize * ratio) + 32), 0.0f);
    std::copy (samples, samples + std::min (n, sampsNeeded), buffer.begin());
    const int bufferSize = (int) buffer.size();

    // the two-pole low-pass at the lower rate's Nyquist frequency: before the interpolation when going down, after it
    // when going up
    const double proportionalRate = ratio > 1.0 ? 0.5 / ratio : 0.5 * ratio;
    const double sqrt2 = 1.4142135623730950488, pi = 3.141592653589793238;
    const double nn = 1.0 / std::tan (pi * std::max (0.001, proportionalRate)), nSquared = nn * nn;
    const double c1 = 1.0 / (1.0 + sqrt2 * nn + nSquared);
    const double coefficients[6] { c1, c1 * 2.0f, c1, 1.0, c1 * 2.0 * (1.0 - nSquared), c1 * (1.0 - sqrt2 * nn + nSquared) };
    auto applyFilter = [&] (float* x, int num)
    {
        double x1 = 0, x2 = 0, y1 = 0, y2 = 0;
        while (--num >= 0)
        {
            const double in = *x;
            double out = coefficients[0] * in + coefficients[1] * x1 + coefficients[2] * x2 - coefficients[4] * y1
                         - coefficients[5] * y2;
#if defined (_M_X64) || defined (_M_IX86) || defined (__x86_64__) || defined (__i386__)
            if (! (out < -1.0e-8 || out > 1.0e-8)) out = 0;
#endif
            x2 = x1; x1 = in;
            y2 = y1; y1 = out;
            *x++ = (float) out;
        }
    };
    if (ratio > 1.0001) applyFilter (buffer.data(), sampsNeeded);

    std::vector<float> out ((size_t) finalSize);
    int bufferPos = 0, nextPos = 1 % bufferSize;
    double subSampleOffset = 0.0;
    for (int m = 0; m < finalSize; ++m)
    {
        const float alpha = (float) subSampleOffset;
        out[(size_t) m] = buffer[(size_t) bufferPos] + alpha * (buffer[(size_t) nextPos] - buffer[(size_t) bufferPos]);
        subSampleOffset += ratio;
        while (subSampleOffset >= 1.0)
        {
            if (++bufferPos >= bufferSize) bufferPos = 0;
            nextPos = (bufferPos + 1) % bufferSize;
            subSampleOffset -= 1.0;
        }
    }
    if (ratio < 0.9999) applyFilter (out.data(), finalSize);
    return out;
}
}
