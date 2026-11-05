"""Identification helpers for the character section. The crossover is known exactly (Source/dsp/BandFilters.h), so for
any input the three band signals the reference processes can be computed exactly, and with them what each band does
to its signal, sample by sample."""
import os, re
import numpy as np
import tgp

FS = tgp.FS
PRE = 2 * FS
D48 = 151.27917


def band_firs():
    src = open(os.path.join(tgp.PLUGIN, 'Source', 'dsp', 'BandFilters.h')).read()
    body = src[src.index('bandIr48k[3]'):src.index('bandGain48k')]
    groups = re.findall(r'\{([^{}]*)\}', body)
    irs = [np.array([float(v) for v in g.replace('\n', ' ').split(',') if v.strip()]) for g in groups[:3]]
    gains = re.findall(r'\{([^{}]*)\}', src[src.index('bandGain48k[3][9]'):])
    gains = [np.array([float(v) for v in g.split(',') if v.strip()]) for g in gains[:3]]
    return irs, gains


IRS, GAINS = band_firs()

# the bands' small-signal gains (dB) at amount 0, 12.5, ..., 200 % (measured from impulse responses with the band
# filters known; the nodes of BandFilters.h are every other one)
GAINS16 = [[0.0, 0.3815, 0.7538, 1.1174, 1.4727, 1.8202, 2.1601, 2.4928, 2.8187, 2.9885, 3.1550, 3.3184, 3.4787, 3.6362, 3.7908, 3.9428, 4.0921],
           [0.0, 0.5753, 1.1054, 1.5960, 2.0517, 2.4766, 2.8740, 3.2464, 3.5965, 3.9607, 4.3103, 4.6464, 4.9700, 5.2819, 5.5831, 5.8741, 6.1557],
           [0.0, 0.1934, 0.3619, 0.5067, 0.6289, 0.7296, 0.8093, 0.8687, 0.9082, 1.1760, 1.4358, 1.6881, 1.9333, 2.1717, 2.4037, 2.6298, 2.8500]]


def gain_db(band, node):
    """small-signal gain at a node of the 25 % grid (fractional: 0.5 steps are measured)"""
    return GAINS16[band][int(round(node * 2))]

# What each band's nonlinear stage (detector and shaper) hears (nlhear.py): its FIR band on the pass side, but beyond
# the band edge a steep Linkwitz-Riley slope instead of the FIR's shallow stopband (the mid band's FIR passes 8 kHz at
# -29.5 dB, its nonlinear stage hears it at -40). Only the mid band's high side is made steep: the low band's stage
# hears its FIR band as it is (as far as it can be measured, to 300 Hz; a steep edge at 157 Hz would also need more
# pre-ringing than the 151 samples there are), and a steep low side for the high band made the broadband nulls worse
# (pink noise at -6 dBFS: -41.3 against -42.6 dB). The rest of the FIR band passes linearly:
#     y_b = M_b (x_b - s_b + F_b(s_b))
FC1, FC2 = 157.1, 2675.8
# The mid band's gain and shaper reach the audio through a path that differs from that edge (xprobe2.py: quiet probes
# under a loud masker in the band, the complex change of the probes): from about 2 kHz up it falls faster (-1.3 dB at
# 3.5 kHz, -2.8 at 4.6, -5.4 at 7.6 kHz) and leads in phase. The same in Hz at 44.1 to 192 kHz and at 50 to 200 %.
# MID_RATIO: the measured ratio of that path to the plain edge (midedge.py --save, from probes taken with the plain
# edge), applied to the mid band's filter from 900 Hz up. (Its low side differs by up to 0.4 dB below 100 Hz; applying
# that made music worse, midedge.py --null.)
MID_RATIO = os.path.join(tgp.ROOT, 'measurements', 'character', 'mid_ratio.npz')


def mid_ratio(f):
    """the measured ratio at frequencies f (Hz): magnitude in dB over log f and unwrapped phase over f, interpolated;
    1 below the first probe; above the last probe the phase keeps its slope"""
    z = np.load(MID_RATIO)
    fh, rh = z['fh'], z['rh']
    ph = np.unwrap(np.angle(rh)); slope = (ph[-1] - ph[-6]) / (fh[-1] - fh[-6])
    out = np.ones(len(f), complex)
    up = f >= fh[0]
    mag = np.interp(np.log(f[up]), np.log(fh), 20 * np.log10(np.abs(rh)))
    phs = np.where(f[up] <= fh[-1], np.interp(f[up], fh, ph), ph[-1] + slope * (f[up] - fh[-1]))
    out[up] = 10 ** (mag / 20) * np.exp(1j * phs)
    return out


def nl_firs(n_taps=1024, fs=FS, irs=None, ratio=True):
    """irs: the band filters at fs (default: the 48 kHz ones); ratio: the mid band's measured path (MID_RATIO)"""
    irs = IRS if irs is None else irs
    nf = 1 << 16
    f = np.fft.rfftfreq(nf, 1 / fs)
    lp = lambda fc: 1 / (1 + (f / fc) ** 4)
    hp = lambda fc: (f / fc) ** 4 / (1 + (f / fc) ** 4)
    target, side = [lp(FC1), lp(FC2), hp(FC2)], [f < 0, f > FC2, f < 0]
    out = []
    for b in range(3):
        H = np.fft.rfft(irs[b], nf)
        W = np.where(side[b], np.minimum(1.0, target[b] / np.maximum(np.abs(H), 1e-15)), 1.0)
        if b == 1 and ratio and os.path.exists(MID_RATIO): W = W * mid_ratio(f)
        out.append(np.fft.irfft(H * W, nf)[:n_taps])
    return out


NL_IRS = nl_firs()


def nl_bands(x):
    """the three signals the bands' nonlinear stages hear, like bands()"""
    x = np.atleast_2d(x)
    return np.array([[np.convolve(c, h)[:x.shape[1]] for c in x] for h in NL_IRS])


def bands(x):
    """the three band signals (raw-aligned with the reference's raw output) for a mono or stereo input"""
    x = np.atleast_2d(x)
    return np.array([[np.convolve(c, h)[:x.shape[1]] for c in x] for h in IRS])      # (3, ch, n)


def per_cycle_fit(y, xb, period, start, stop, order=(1, 3)):
    """regress y on powers of xb over windows of one period: returns per-window coefficients (n_windows, len(order))
    and the residual energy re y"""
    out, res = [], []
    p = int(round(period))
    for a in range(start, stop - p, p):
        X = np.stack([xb[a:a + p] ** k for k in order], 1)
        c, *_ = np.linalg.lstsq(X, y[a:a + p], rcond=None)
        out.append(c); res.append(np.sum((X @ c - y[a:a + p]) ** 2) / max(np.sum(y[a:a + p] ** 2), 1e-30))
    return np.array(out), np.array(res)


def gain_trace(y, x, band, node, k, rel_min=0.3):
    """the reference's band gain n(t) sample by sample: y = sum of bands, the other two treated as linear; the band's
    output inverted through the sine shaper (y_b = M sin(k n x_b) / k). Past the fold (k u > pi / 2) asin has two
    answers: the one closer to the previous estimate is taken. Samples where |x_b| is under rel_min of its local
    peak are NaN (the division is ill-conditioned there)."""
    xb = bands(x)[:, 0]
    M = [10 ** (GAINS[b][node] / 20) for b in range(3)]
    yb = (y - sum(M[b] * xb[b] for b in range(3) if b != band)) / M[band]
    xx = xb[band]
    arg = np.clip(k * yb, -1, 1)
    a = np.arcsin(arg)
    u1 = a / k; u2 = (np.sign(a) * np.pi - a) / k
    env = np.maximum.accumulate(np.abs(xx))          # placeholder, replaced below by a local peak
    from scipy.ndimage import maximum_filter1d
    env = maximum_filter1d(np.abs(xx), 2 * int(FS / 50) + 1)
    ok = np.abs(xx) > rel_min * env
    n = np.full(len(y), np.nan)
    with np.errstate(divide='ignore', invalid='ignore'):
        n1 = u1 / xx; n2 = u2 / xx
    prev = 1.0
    idx = np.where(ok)[0]
    for i in idx:
        c1, c2 = n1[i], n2[i]
        v = c1 if abs(c1 - prev) <= abs(c2 - prev) or abs(arg[i]) < 0.9 else c2
        n[i] = v; prev = v
    return n, xx
