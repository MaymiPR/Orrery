#pragma once
#if defined (_M_X64) || defined (_M_AMD64) || defined (__x86_64__)
 #if defined (_MSC_VER) && ! defined (__clang__)
  #include <immintrin.h>
  #include <intrin.h>
 #else
  #include <cpuid.h>
 #endif
#endif

// The vector units the learned blocks and the convolver choose their widest loops by (Convolver.h, LearnedWaveNet.h):
// the processor's feature bits, read once. All false where the processor is not x86-64.
namespace sc::dsp
{
struct CpuFeatures
{
    bool avx = false, fma = false, avx2 = false, avx512f = false;
};

inline const CpuFeatures& cpuFeatures()
{
    static const CpuFeatures features = []
    {
        CpuFeatures f;
#if defined (_M_X64) || defined (_M_AMD64) || defined (__x86_64__)
        auto cpuid = [] (int leaf, unsigned (&r)[4])
        {
 #if defined (_MSC_VER) && ! defined (__clang__)
            int v[4];
            __cpuidex (v, leaf, 0);
            for (int k = 0; k < 4; ++k) r[k] = (unsigned) v[k];
 #else
            __cpuid_count (leaf, 0, r[0], r[1], r[2], r[3]);
 #endif
        };
        // the processor's bits count only where the operating system saves the registers: XCR0 says which (bits 1
        // and 2 for AVX, 5 to 7 too for AVX-512), and is readable when OSXSAVE is set
        auto xcr0 = []() -> unsigned long long
        {
 #if defined (_MSC_VER) && ! defined (__clang__)
            return _xgetbv (0);
 #else
            unsigned lo = 0, hi = 0;
            __asm__ __volatile__ (".byte 0x0f, 0x01, 0xd0" : "=a" (lo), "=d" (hi) : "c" (0));      // xgetbv
            return ((unsigned long long) hi << 32) | lo;
 #endif
        };
        unsigned r[4];
        cpuid (1, r);
        const unsigned long long saved = (r[2] & (1u << 27)) != 0 ? xcr0() : 0;
        const bool osAvx = (saved & 0x6u) == 0x6u, osAvx512 = (saved & 0xe6u) == 0xe6u;
        f.avx = osAvx && (r[2] & (1u << 28)) != 0;
        f.fma = osAvx && (r[2] & (1u << 12)) != 0;
        cpuid (7, r);
        f.avx2 = osAvx && (r[1] & (1u << 5)) != 0;
        f.avx512f = osAvx512 && (r[1] & (1u << 16)) != 0;
#endif
        return f;
    }();
    return features;
}
}
