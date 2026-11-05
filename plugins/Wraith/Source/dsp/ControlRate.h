#pragma once

// The reference's parameter smoothing (MEASUREMENTS.md "Smoothing"): audio runs in chunks of 128 samples; at the
// start of each chunk a parameter's target moves a fixed share of the way to the new value (k = chunk time / 10 ms,
// an Euler one-pole), and inside the chunk the value ramps linearly from the last target to the new one.
namespace wr::dsp
{
inline constexpr int chunkSize = 128;

struct ControlRate
{
    double from = 0, to = 0, k = 0.2667;
    bool snapped = false;

    void setRate (double fs, double tauSeconds) { k = (chunkSize / fs) / tauSeconds; }
    void snap (double v) { from = to = v; snapped = true; }
    // at the start of a chunk: move toward the goal (the first call after prepare jumps to it)
    void advance (double goal)
    {
        if (! snapped) { snap (goal); return; }
        from = to;
        to += k * (goal - to);
    }
    // the value at sample j (0 based) of the chunk
    double at (int j) const { return from + (to - from) * (double) (j + 1) / (double) chunkSize; }
};
}
