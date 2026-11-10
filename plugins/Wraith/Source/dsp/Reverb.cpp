#include "Reverb.h"
#include <WraithIR.h>
#include <chrono>
#include <cmath>
#include <cstring>
#include <thread>

using namespace juce;

namespace wr::dsp
{
namespace
{
// the responses for one rate (scripts/pack_reverb.py): per reverb a length, then L and R interleaved as 16-bit floats
struct Packed { double fs; const char* data; int size; };

float half (uint16 h)
{
    const uint32 s = (uint32) (h & 0x8000u) << 16, e = (h >> 10) & 0x1fu, m = h & 0x3ffu;
    uint32 f;
    if (e == 0)
    {
        if (m == 0) f = s;
        else
        {
            int ee = -1;
            uint32 mm = m;
            do { ++ee; mm <<= 1; } while ((mm & 0x400u) == 0);
            f = s | ((uint32) (127 - 15 - ee) << 23) | ((mm & 0x3ffu) << 13);
        }
    }
    else if (e == 31) f = s | 0x7f800000u | (m << 13);
    else f = s | ((e + 112u) << 23) | (m << 13);
    float v;
    std::memcpy (&v, &f, 4);
    return v;
}

Packed nearestPacked (double fs)
{
    const Packed all[] = { { 44100.0, WraithIR::reverb_44100_bin, WraithIR::reverb_44100_binSize },
                           { 48000.0, WraithIR::reverb_48000_bin, WraithIR::reverb_48000_binSize },
                           { 88200.0, WraithIR::reverb_88200_bin, WraithIR::reverb_88200_binSize },
                           { 96000.0, WraithIR::reverb_96000_bin, WraithIR::reverb_96000_binSize } };
    const Packed* best = &all[0];
    for (const auto& p : all)
        if (std::abs (std::log (p.fs / fs)) < std::abs (std::log (best->fs / fs))) best = &p;
    return *best;
}
}

void Reverb::prepare (double fs, int block)
{
    const auto pk = nearestPacked (fs);
    const auto* p = reinterpret_cast<const uint8*> (pk.data);
    const auto* end = p + pk.size;
    const juce::dsp::ProcessSpec spec { fs, (uint32) jmax (1, block), 2 };
    int want[2] {};
    for (size_t t = 0; t < conv.size(); ++t)
    {
        conv[t].reset();
        if (p + 4 > end) continue;
        uint32 n;
        std::memcpy (&n, p, 4);
        p += 4;
        if (n == 0 || p + (size_t) n * 4 > end) continue;
        AudioBuffer<float> ir (2, (int) n);
        for (int i = 0; i < (int) n; ++i)
        {
            uint16 v[2];
            std::memcpy (v, p + (size_t) i * 4, 4);
            ir.setSample (0, i, half (v[0]));
            ir.setSample (1, i, half (v[1]));
        }
        p += (size_t) n * 4;
        want[t] = (int) (0.99 * n * fs / pk.fs);                     // (its length at this rate, less a margin)
        conv[t] = std::make_unique<juce::dsp::Convolution> (juce::dsp::Convolution::NonUniform { 256 });
        conv[t]->prepare (spec);
        conv[t]->loadImpulseResponse (std::move (ir), pk.fs, juce::dsp::Convolution::Stereo::yes, juce::dsp::Convolution::Trim::no,
                                      juce::dsp::Convolution::Normalise::no);
    }
    // the responses load on a background thread and are swapped in during processing (with a short crossfade): run
    // silence through every engine until each holds its whole response, so the first real block already has it
    buf.setSize (2, jmax (1, block));
    const auto t0 = Time::getMillisecondCounter();
    for (;;)
    {
        bool ready = true;
        for (size_t t = 0; t < conv.size(); ++t)
            if (conv[t] != nullptr)
            {
                buf.clear();
                juce::dsp::AudioBlock<float> blk (buf);
                conv[t]->process (juce::dsp::ProcessContextReplacing<float> (blk));
                ready = ready && conv[t]->getCurrentIRSize() >= want[t];
            }
        if (ready || Time::getMillisecondCounter() - t0 > 20000) break;
        std::this_thread::sleep_for (std::chrono::milliseconds (2));
    }
    for (int i = 0; i < (int) (0.2 * fs) / jmax (1, block) + 2; ++i)    // (past the crossfade)
        for (auto& c : conv)
            if (c != nullptr) { buf.clear(); juce::dsp::AudioBlock<float> blk (buf); c->process (juce::dsp::ProcessContextReplacing<float> (blk)); }
    reset();
}

void Reverb::reset()
{
    for (auto& c : conv)
        if (c != nullptr) c->reset();
    running = -1;
}

void Reverb::process (const float* l, const float* r, float* wl, float* wr, int n, int type)
{
    type = jlimit (0, 1, type);
    if (conv[(size_t) type] == nullptr) type = 0;
    auto& c = conv[(size_t) type];
    if (c == nullptr) { FloatVectorOperations::clear (wl, n); FloatVectorOperations::clear (wr, n); return; }
    if (type != running) { running = type; c->reset(); }
    buf.setSize (2, n, false, false, true);
    buf.copyFrom (0, 0, l, n);
    buf.copyFrom (1, 0, r, n);
    juce::dsp::AudioBlock<float> blk (buf);
    c->process (juce::dsp::ProcessContextReplacing<float> (blk));
    FloatVectorOperations::copy (wl, buf.getReadPointer (0), n);
    FloatVectorOperations::copy (wr, buf.getReadPointer (1), n);
}
}
