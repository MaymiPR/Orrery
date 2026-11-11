#pragma once
#include <cmath>
#include <complex>
#include <vector>

// A power-of-two FFT for the plug-ins' DSP, plain C++. Every operation runs in the order of JUCE's own fallback FFT
// (juce::dsp::FFT on Windows and Linux): decimation in time, radix-4 stages and a last radix-2 stage when the order is
// odd, the twiddles a computed quarter wave extended by symmetry. A block that used juce::dsp::FFT keeps its output
// to the last bit on those systems. No allocation after construction; one instance serves one thread.
namespace orrery
{
class Fft
{
public:
    explicit Fft (int order)
        : size (1 << order), forward (1 << order, false), inverse (1 << order, true), scratch ((size_t) 1 << order)
    {
    }

    int getSize() const noexcept { return size; }

    // data holds 2 * getSize() floats: getSize() real samples in, getSize() complex bins out (interleaved, the upper
    // half the conjugate mirror of the lower)
    void forwardReal (float* data) noexcept
    {
        if (size == 1) return;
        for (int i = 0; i < size; ++i) scratch[(size_t) i] = { data[i], 0 };
        forward.perform (scratch.data(), reinterpret_cast<Complex*> (data));
    }

    // data holds 2 * getSize() floats: the bins 0 .. getSize() / 2 in (the upper half is rebuilt from them); out, the
    // real parts of the inverse transform scaled by 1 / getSize() in the first getSize() floats, the imaginary parts
    // after them
    void inverseReal (float* data) noexcept
    {
        if (size == 1) return;
        auto* bins = reinterpret_cast<Complex*> (data);
        for (int i = size >> 1; i < size; ++i) bins[i] = std::conj (bins[size - i]);
        inverse.perform (bins, scratch.data());
        const float scaleFactor = 1.0f / (float) size;
        for (int i = 0; i < size; ++i) scratch[(size_t) i] *= scaleFactor;
        for (int i = 0; i < size; ++i)
        {
            data[i] = scratch[(size_t) i].real();
            data[i + size] = scratch[(size_t) i].imag();
        }
    }

private:
    using Complex = std::complex<float>;

    struct Config
    {
        Config (int sizeOfFft, bool inverseTransform)
            : fftSize (sizeOfFft), isInverse (inverseTransform), twiddles ((size_t) sizeOfFft)
        {
            const double inverseFactor = (isInverse ? 2.0 : -2.0) * 3.141592653589793238 / (double) fftSize;
            if (fftSize <= 4)
            {
                for (int i = 0; i < fftSize; ++i)
                {
                    const double phase = i * inverseFactor;
                    twiddles[(size_t) i] = { (float) std::cos (phase), (float) std::sin (phase) };
                }
            }
            else
            {
                for (int i = 0; i < fftSize / 4; ++i)
                {
                    const double phase = i * inverseFactor;
                    twiddles[(size_t) i] = { (float) std::cos (phase), (float) std::sin (phase) };
                }
                for (int i = fftSize / 4; i < fftSize / 2; ++i)
                {
                    const Complex other = twiddles[(size_t) (i - fftSize / 4)];
                    twiddles[(size_t) i] = { isInverse ? -other.imag() : other.imag(), isInverse ? other.real() : -other.real() };
                }
                twiddles[(size_t) (fftSize / 2)] = { -1.0f, 0.0f };
                for (int i = fftSize / 2; i < fftSize; ++i)
                    twiddles[(size_t) i] = std::conj (twiddles[(size_t) (fftSize / 2 - (i - fftSize / 2))]);
            }

            // the radices: fours while the size divides by four, then a two (the rest radix 1)
            const int root = (int) std::sqrt ((double) fftSize);
            int divisor = 4, n = fftSize;
            for (auto& f : factors)
            {
                while ((n % divisor) != 0)
                {
                    if (divisor == 2) divisor = 3;
                    else if (divisor == 4) divisor = 2;
                    else divisor += 2;
                    if (divisor > root) divisor = n;
                }
                n /= divisor;
                f = { divisor, n };
            }
        }

        void perform (const Complex* input, Complex* output) const noexcept { perform (input, output, 1, factors); }

        struct Factor { int radix, length; };

        void perform (const Complex* input, Complex* output, int stride, const Factor* facs) const noexcept
        {
            const Factor factor = *facs++;
            Complex* const originalOutput = output;
            const Complex* const outputEnd = output + factor.radix * factor.length;
            if (stride == 1 && factor.radix <= 5)
            {
                for (int i = 0; i < factor.radix; ++i)
                    perform (input + stride * i, output + i * factor.length, stride * factor.radix, facs);
                butterfly (factor, output, stride);
                return;
            }
            if (factor.length == 1)
            {
                do
                {
                    *output++ = *input;
                    input += stride;
                }
                while (output < outputEnd);
            }
            else
            {
                do
                {
                    perform (input, output, stride * factor.radix, facs);
                    input += stride;
                    output += factor.length;
                }
                while (output < outputEnd);
            }
            butterfly (factor, originalOutput, stride);
        }

        void butterfly (Factor factor, Complex* data, int stride) const noexcept
        {
            if (factor.radix == 2) butterfly2 (data, stride, factor.length);
            else if (factor.radix == 4) butterfly4 (data, stride, factor.length);
        }

        void butterfly2 (Complex* data, int stride, int length) const noexcept
        {
            Complex* dataEnd = data + length;
            const Complex* tw = twiddles.data();
            for (int i = length; --i >= 0;)
            {
                Complex s = *dataEnd;
                s *= (*tw);
                tw += stride;
                *dataEnd++ = *data - s;
                *data++ += s;
            }
        }

        void butterfly4 (Complex* data, int stride, int length) const noexcept
        {
            const int lengthX2 = length * 2, lengthX3 = length * 3;
            const int strideX2 = stride * 2, strideX3 = stride * 3;
            const Complex* twiddle1 = twiddles.data();
            const Complex* twiddle2 = twiddle1;
            const Complex* twiddle3 = twiddle1;
            for (int i = length; --i >= 0;)
            {
                const Complex s0 = data[length] * *twiddle1;
                const Complex s1 = data[lengthX2] * *twiddle2;
                const Complex s2 = data[lengthX3] * *twiddle3;
                Complex s3 = s0;
                s3 += s2;
                Complex s4 = s0;
                s4 -= s2;
                Complex s5 = *data;
                s5 -= s1;
                *data += s1;
                data[lengthX2] = *data;
                data[lengthX2] -= s3;
                twiddle1 += stride;
                twiddle2 += strideX2;
                twiddle3 += strideX3;
                *data += s3;
                if (isInverse)
                {
                    data[length] = { s5.real() - s4.imag(), s5.imag() + s4.real() };
                    data[lengthX3] = { s5.real() + s4.imag(), s5.imag() - s4.real() };
                }
                else
                {
                    data[length] = { s5.real() + s4.imag(), s5.imag() - s4.real() };
                    data[lengthX3] = { s5.real() - s4.imag(), s5.imag() + s4.real() };
                }
                ++data;
            }
        }

        const int fftSize;
        const bool isInverse;
        std::vector<Complex> twiddles;
        Factor factors[32] {};
    };

    int size;
    Config forward, inverse;
    std::vector<Complex> scratch;
};
}
