#pragma once
#include <algorithm>
#include <vector>
#include "Convolver.h"
#include "FastMath.h"

// A learned module as a stacked LSTM (nulltest/train_gru.py, CELL=lstm): y = Post(skip u + W LSTM(u)), u = Pre(x).
// Pre a short FIR, the LSTM PyTorch's equations (gates i, f, g, o), Post a long FIR (Convolver.h); skip 0 is the
// network alone (SKIP=0), and with one-tap filters of 1 (PURE=1) y = W LSTM(x). The weights are ours, trained on the
// reference's input and output (written into LearnedModels.h by nulltest/export_models.py).
namespace sc::dsp
{
struct LSTMWeights
{
    int hidden, layers;
    std::vector<float> pre, post;
    std::vector<std::vector<float>> wih, whh, bih, bhh;   // per layer: (4H) x in, (4H) x H, 4H, 4H (PyTorch layout)
    std::vector<float> wout; float bout;                 // 1 x H
    float skip = 1.0f;                                   // the input's share added to the network's output
    std::vector<std::vector<float>> h0, c0;              // per layer: the state a reset starts from (empty: zero)
};

class LearnedLSTM
{
public:
    void prepare (const LSTMWeights& w)
    {
        weights = &w;
        const int H = w.hidden;
        post.prepare (w.post);
        pre.assign (w.pre.size(), 0.0f);
        // the weights by input (columns), so each update runs over contiguous gate rows (no reduction)
        colIh.clear(); colHh.clear(); bias.clear();
        for (int l = 0; l < w.layers; ++l)
        {
            const int in = l == 0 ? 1 : H;
            std::vector<float> ih ((size_t) (4 * H * in)), hh ((size_t) (4 * H * H)), b ((size_t) (4 * H));
            for (int r = 0; r < 4 * H; ++r)
            {
                for (int k = 0; k < in; ++k) ih[(size_t) (k * 4 * H + r)] = w.wih[(size_t) l][(size_t) (r * in + k)];
                for (int k = 0; k < H; ++k) hh[(size_t) (k * 4 * H + r)] = w.whh[(size_t) l][(size_t) (r * H + k)];
                b[(size_t) r] = w.bih[(size_t) l][(size_t) r] + w.bhh[(size_t) l][(size_t) r];
            }
            colIh.push_back (ih); colHh.push_back (hh); bias.push_back (b);
        }
        h.assign ((size_t) w.layers, std::vector<float> ((size_t) H, 0.0f)); c = h;
        gates.assign ((size_t) (4 * H), 0.0f);
        reset();
    }
    void reset()
    {
        std::fill (pre.begin(), pre.end(), 0.0f);
        // the state the network rests in on silence where the model gives it (a module switched on behaves like one
        // that ran on silence), else zero
        const auto& w = *weights;
        for (size_t l = 0; l < h.size(); ++l)
        {
            if (l < w.h0.size() && w.h0[l].size() == h[l].size()) std::copy (w.h0[l].begin(), w.h0[l].end(), h[l].begin());
            else std::fill (h[l].begin(), h[l].end(), 0.0f);
            if (l < w.c0.size() && w.c0[l].size() == c[l].size()) std::copy (w.c0[l].begin(), w.c0[l].end(), c[l].begin());
            else std::fill (c[l].begin(), c[l].end(), 0.0f);
        }
        post.reset();
        prePos = 0;
    }
    // in place allowed
    void process (const double* in, double* out, int n)
    {
        // the hidden size known when compiling where a model uses it (the loops then unrolled and vectorised whole)
        if (weights->hidden == 24) run<24> (in, out, n);
        else run<0> (in, out, n);
    }

private:
    template <int FixedH>
    void run (const double* in, double* out, int n)
    {
        const auto& w = *weights;
        const int H = FixedH > 0 ? FixedH : w.hidden, K = (int) w.pre.size(), G = 4 * H;
        const bool onePost = w.post.size() == 1;
        float* g = gates.data();
        for (int t = 0; t < n; ++t)
        {
            pre[(size_t) prePos] = (float) in[t];
            float u = 0;
            int j = prePos;
            for (int k = 0; k < K; ++k) { u += w.pre[(size_t) k] * pre[(size_t) j]; j = j == 0 ? K - 1 : j - 1; }
            prePos = (prePos + 1) % K;
            const float* x = &u;
            for (int l = 0; l < w.layers; ++l)
            {
                const int inN = l == 0 ? 1 : H;
                const float* b = bias[(size_t) l].data();
                for (int r = 0; r < G; ++r) g[r] = b[r];
                const float* wi = colIh[(size_t) l].data();
                int p = 0;
                for (; p + 4 <= inN; p += 4)
                {
                    const float x0 = x[p], x1 = x[p + 1], x2 = x[p + 2], x3 = x[p + 3];
                    const float* c0 = wi + (size_t) p * (size_t) G; const float* c1 = c0 + G; const float* c2 = c1 + G; const float* c3 = c2 + G;
                    for (int r = 0; r < G; ++r) g[r] += (c0[r] * x0 + c1[r] * x1) + (c2[r] * x2 + c3[r] * x3);
                }
                for (; p < inN; ++p)
                {
                    const float xq = x[p]; const float* col = wi + (size_t) p * (size_t) G;
                    for (int r = 0; r < G; ++r) g[r] += col[r] * xq;
                }
                float* hl = h[(size_t) l].data(); float* cl = c[(size_t) l].data();
                const float* wh = colHh[(size_t) l].data();
                int q = 0;
                for (; q + 4 <= H; q += 4)          // four columns a pass, so the gates are loaded and stored a quarter as often
                {
                    const float h0 = hl[q], h1 = hl[q + 1], h2 = hl[q + 2], h3 = hl[q + 3];
                    const float* c0 = wh + (size_t) q * (size_t) G; const float* c1 = c0 + G; const float* c2 = c1 + G; const float* c3 = c2 + G;
                    for (int r = 0; r < G; ++r) g[r] += (c0[r] * h0 + c1[r] * h1) + (c2[r] * h2 + c3[r] * h3);
                }
                for (; q < H; ++q)
                {
                    const float hq = hl[q]; const float* col = wh + (size_t) q * (size_t) G;
                    for (int r = 0; r < G; ++r) g[r] += col[r] * hq;
                }
                // the activations gate by gate over contiguous runs (each loop vectorises), then the state; the gates'
                // sigmoid keeps its tails (a forget gate near 1 is the slow cells' memory: FastMath.h)
                for (int r = 0; r < 2 * H; ++r) g[r] = tailSigmoid (g[r]);
                for (int r = 2 * H; r < 3 * H; ++r) g[r] = fastTanh (g[r]);
                for (int r = 3 * H; r < G; ++r) g[r] = tailSigmoid (g[r]);
                for (int k = 0; k < H; ++k) cl[k] = g[H + k] * cl[k] + g[k] * g[2 * H + k];
                for (int k = 0; k < H; ++k) hl[k] = g[3 * H + k] * fastTanh (cl[k]);
                x = hl;
            }
            float o = w.bout;
            for (int k = 0; k < H; ++k) o += w.wout[(size_t) k] * x[k];
            const float v = w.skip * u + o;
            out[t] = onePost ? w.post[0] * v : post.process (v);
        }
    }

    const LSTMWeights* weights = nullptr;
    Convolver post;
    std::vector<float> pre, gates;
    std::vector<std::vector<float>> colIh, colHh, bias, h, c;
    int prePos = 0;
};
}
