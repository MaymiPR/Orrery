#include "Reverb.h"
#include <algorithm>
#include <WraithIR.h>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

namespace wr::dsp
{
namespace
{
// the responses for one rate (scripts/pack_reverb.py): per reverb a length, then L and R interleaved as 16-bit floats
struct Packed { double fs; const char* data; int size; };

float half (std::uint16_t h)
{
    const std::uint32_t s = (std::uint32_t) (h & 0x8000u) << 16, e = (h >> 10) & 0x1fu, m = h & 0x3ffu;
    std::uint32_t f;
    if (e == 0)
    {
        if (m == 0) f = s;
        else
        {
            int ee = -1;
            std::uint32_t mm = m;
            do { ++ee; mm <<= 1; } while ((mm & 0x400u) == 0);
            f = s | ((std::uint32_t) (127 - 15 - ee) << 23) | ((mm & 0x3ffu) << 13);
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
    const auto* p = reinterpret_cast<const unsigned char*> (pk.data);
    const auto* end = p + pk.size;
    for (size_t t = 0; t < conv.size(); ++t)
    {
        conv[t].reset();
        if (p + 4 > end) continue;
        std::uint32_t n;
        std::memcpy (&n, p, 4);
        p += 4;
        if (n == 0 || p + (size_t) n * 4 > end) continue;
        std::vector<float> left (n), right (n);
        for (size_t i = 0; i < n; ++i)
        {
            std::uint16_t v[2];
            std::memcpy (v, p + i * 4, 4);
            left[i] = half (v[0]);
            right[i] = half (v[1]);
        }
        p += (size_t) n * 4;
        conv[t] = std::make_unique<Convolution>();
        conv[t]->prepare (left.data(), right.data(), (int) n, pk.fs, fs, std::max (1, block));
    }
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
    type = std::clamp (type, 0, 1);
    if (conv[(size_t) type] == nullptr) type = 0;
    auto& c = conv[(size_t) type];
    if (c == nullptr) { std::fill (wl, wl + n, 0.0f); std::fill (wr, wr + n, 0.0f); return; }
    if (type != running) { running = type; c->reset(); }
    std::copy (l, l + n, wl);
    std::copy (r, r + n, wr);
    c->process (wl, wr, n);
}
}
