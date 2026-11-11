#pragma once
#if defined (_M_X64) || defined (_M_AMD64) || defined (__x86_64__)
 #if defined (_MSC_VER) && ! defined (__clang__)
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
        unsigned r[4];
        cpuid (1, r);
        f.avx = (r[2] & (1u << 28)) != 0;
        f.fma = (r[2] & (1u << 12)) != 0;
        cpuid (7, r);
        f.avx2 = (r[1] & (1u << 5)) != 0;
        f.avx512f = (r[1] & (1u << 16)) != 0;
#endif
        return f;
    }();
    return features;
}
}
