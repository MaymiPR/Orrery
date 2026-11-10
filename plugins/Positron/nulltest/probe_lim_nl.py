"""The limiter's level estimate against estimators that are not a linear phase table (probe_lim_interp.py showed none of
those reads short raw noise bursts): on probe_lim_interp.py's 4096 isolated pulses, the reference's reading of each pulse
(probe_lim_pulse.read) against candidates evaluated on the same input windows. Errors split into band-limited pulses and
raw bursts (content up to Nyquist).

    python probe_lim_nl.py"""
import numpy as np
from scipy.signal import resample_poly
import po_ref, limiter_lib, probe_lim_pulse as P, probe_lim_interp as LI


def kinds(seed=11):
    """probe_lim_interp.pulses' draw, replayed: True where the pulse is a raw noise burst"""
    rng = np.random.default_rng(seed); out = []
    for i in range(LI.NPULSE):
        raw = rng.uniform() < 0.3; out.append(raw)
        if raw:
            m = rng.integers(2, 7); rng.standard_normal(m)
        else:
            rng.uniform(0.12, 0.5); rng.uniform(0, 1)
            if rng.uniform() < 0.5: rng.standard_normal(3)
        rng.uniform(1.6, 2.6); rng.choice([-1, 1])
    return np.array(out)


def seg_max(v, a):
    return np.max(np.abs(v[a:a + 300]))


def kaiser_sinc(taps, beta, sub):
    T = np.zeros((sub, taps))
    for ph in range(sub):
        k = np.arange(taps) - (taps // 2 - 1) - ph / sub; r = k / (taps / 2)
        w = np.where(np.abs(r) >= 1, 0, np.i0(beta * np.sqrt(np.clip(1 - r * r, 0, None))) / np.i0(beta))
        T[ph] = np.sinc(k) * w; T[ph] /= T[ph].sum()
    return T


def table_levels(x, T):
    c = T.shape[1] // 2 - 1
    out = np.abs(x).copy()
    for ph in range(T.shape[0]):
        y = np.convolve(x, T[ph][::-1], 'full')[T.shape[1] - 1 - c:][:len(x)]
        out = np.maximum(out, np.abs(y))
    return out


def catmull(x, sub=16):
    """Catmull-Rom between x[n] and x[n+1] at sub phases"""
    xm, x0, x1, x2 = np.roll(x, 1), x, np.roll(x, -1), np.roll(x, -2)
    out = np.abs(x).copy()
    for t in np.arange(1, sub) / sub:
        a0 = x0; a1 = 0.5 * (x1 - xm); a2 = xm - 2.5 * x0 + 2 * x1 - 0.5 * x2; a3 = 0.5 * (x2 - xm) + 1.5 * (x0 - x1)
        out = np.maximum(out, np.abs(((a3 * t + a2) * t + a1) * t + a0))
    return out


def parabola(x):
    """at a local maximum of |x|: the vertex of the parabola through it and its neighbours"""
    a, b, c = np.abs(np.roll(x, 1)), np.abs(x), np.abs(np.roll(x, -1))
    den = a - 2 * b + c
    with np.errstate(all='ignore'):
        p = 0.5 * (a - c) / den
        v = b - 0.25 * (a - c) * p
    peak = (b >= a) & (b >= c) & (den < 0)
    return np.where(peak, np.maximum(b, v), b)


def upsampled(x, L, taps=None):
    y = resample_poly(x, L, 1) if taps is None else resample_poly(x, L, 1, window=('kaiser', taps))
    return np.max(np.abs(y[:len(x) * L].reshape(-1, L)), axis=1)


if __name__ == '__main__':
    x, at = LI.pulses(); raw = kinds()
    xin = P.limiter_input(x)
    j = dict(x=np.stack([x, x]).astype(np.float32), norm=po_ref.LIM_ONLY, params={'Limiter Input Gain': 0})
    y = po_ref.render_many([j], 'ref', cache=True)[0][0]; ym = po_ref.render_many([j], 'model')[0][0]
    ref = P.read(xin, y, at); ours = P.read(xin, ym, at)
    sc = 1.00014     # limLevelScale
    k24 = np.array([max(1.0, seg_max(table_levels(xin[a - 40:a + 340], kaiser_sinc(24, 12, 16)) * sc, 40)) for a in at])
    ok = np.abs(ours - k24) < 2e-4         # pulses whose reading is the level in our own plug-in (no plan in the way)
    print(f'{ok.sum()} usable pulses ({np.sum(ok & raw)} raw bursts)')
    cands = {'ours (plug-in)': None,
             'kaiser sinc 24 b12 x16': table_levels(xin, kaiser_sinc(24, 12, 16)) * sc,
             'kaiser sinc 24 b12 x4': table_levels(xin, kaiser_sinc(24, 12, 4)) * sc,
             'kaiser sinc 24 b12 x8': table_levels(xin, kaiser_sinc(24, 12, 8)) * sc,
             'kaiser sinc 24 b12 x32': table_levels(xin, kaiser_sinc(24, 12, 32)) * sc, 'kaiser sinc 32 b12 x16': table_levels(xin, kaiser_sinc(32, 12, 16)) * sc,
             'catmull-rom x16': catmull(xin) * sc, 'parabola': parabola(xin) * sc,
             'resample_poly x4': upsampled(xin, 4) * sc, 'resample_poly x8': upsampled(xin, 8) * sc,
             'samples only': np.abs(xin) * sc}
    for name, lv in cands.items():
        est = ours if lv is None else np.array([max(1.0, seg_max(lv, a)) for a in at])
        e = (est - ref)[ok]; r = raw[ok]
        print(f'{name:26s} band-limited rms {np.sqrt(np.mean(e[~r] ** 2)):.2e} max {np.max(np.abs(e[~r])):.2e}   '
              f'raw rms {np.sqrt(np.mean(e[r] ** 2)):.2e} max {np.max(np.abs(e[r])):.2e}  mean {np.mean(e[r]):+.2e}')
