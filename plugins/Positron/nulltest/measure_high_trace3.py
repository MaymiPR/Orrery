"""The high band's gain n(t) on noise, reference against ours (measure_high_trace2.py's inversion), and what the difference
follows: the band's level, whether the detector is rising or falling, the mid band's level.

    python measure_high_trace3.py [signal] [amount 0..1] [--band mid]       signal: a nulltest.py signal name (default 'pink -6')"""
import sys
import numpy as np
from scipy.signal import lfilter
import tgp, nulltest as N, ident as I, charmodel as CM, charsim as C
from measure_high_trace2 import invert
import os, re


def header_laws(row):
    """the laws at a table row as the plug-in has them (Source/dsp/CharacterTable.h)"""
    txt = open(os.path.join(tgp.PLUGIN, 'Source', 'dsp', 'CharacterTable.h')).read()
    peak = [int(v) for v in re.search(r'characterDetectorPeak\[3\] \{ ([^}]*) \}', txt).group(1).split(',')]
    blocks = re.findall(r'// (low|mid|high)\n(.*?)\n    \},', txt, re.S)
    out = {}
    for bi, (nm, body) in enumerate(blocks):
        rows = [[float(v) for v in l.strip().strip('{},').split(',')] for l in body.strip().split('\n')]
        law = dict(zip(C.NAMES, rows[row])); law['k'] = float(np.sqrt(6 * law.pop('cubic'))); law['peak'] = peak[bi]
        law.pop('makeup'); law.pop('width')
        out[nm] = law
    return out


BAND = 2


def traces(x, amt):
    row = int(round(amt * 16))
    j = dict(x=x, norm={**tgp.CHAR_ONLY, 'Character': amt}, raw=True)
    r = tgp.render_many([j], 'ref', cache=True)[0]; o = tgp.render_many([j], 'model')[0]
    laws = header_laws(row)
    xb, sb = CM.prep(x)
    ys = [CM.band(xb[b], sb[b], laws[CM.NAMES[b]], I.GAINS16[b][row], CM.WIDTH[CM.NAMES[b]][row]) for b in range(3)]
    B = BAND; others = sum(ys[b] for b in range(3) if b != B)
    M = 10 ** (I.GAINS16[B][row] / 20); k, d = laws[CM.NAMES[B]]['k'], laws[CM.NAMES[B]]['shapeDry']
    s = sb[B][0]; out = {}
    print('charmodel vs plug-in: %.1f dB' % N.residual_db(o, sum(ys)))
    for who, yh in (('ref', (r - others)[0]), ('ours', (o - others)[0])):
        u = invert(yh / M - (xb[B][0] - s), k, d)
        with np.errstate(all='ignore'): out[who] = np.where(np.abs(s) > 0.3 * np.std(s[N.PRE:]), u / s, np.nan)
    return r, o, s, sb, out, laws


def smooth_db(n, w):
    """median of 20 log10 n over windows of w samples"""
    m = len(n) // w
    return np.array([np.nanmedian(20 * np.log10(n[i * w:(i + 1) * w])) for i in range(m)])


if __name__ == '__main__':
    if '--band' in sys.argv:
        i = sys.argv.index('--band'); BAND = CM.NAMES.index(sys.argv[i + 1]); del sys.argv[i:i + 2]
    sig = sys.argv[1] if len(sys.argv) > 1 else 'pink -6'
    amt = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    x = N.SIGNALS[sig](); x = np.vstack([x, x]) if x.ndim == 1 else x
    x = np.concatenate([np.zeros((2, N.PRE), np.float32), x], -1)
    r, o, s, sb, n, laws = traces(x, amt)
    print(CM.NAMES[BAND], 'law', {k: round(v, 3) if isinstance(v, float) else v for k, v in laws[CM.NAMES[BAND]].items()})
    w = 96
    gr, go = smooth_db(n['ref'], w)[N.PRE // w:], smooth_db(n['ours'], w)[N.PRE // w:]
    ok = np.isfinite(gr) & np.isfinite(go)
    dg = go - gr
    print(f'n (dB, {w}-sample medians): ref mean {np.mean(gr[ok]):.3f} sd {np.std(gr[ok]):.3f}; ours mean {np.mean(go[ok]):.3f} sd {np.std(go[ok]):.3f}')
    print(f'ours - ref: mean {np.mean(dg[ok]):+.3f} dB, sd {np.std(dg[ok]):.3f}; corr(ref, ours) {np.corrcoef(gr[ok], go[ok])[0, 1]:.4f}')
    # regress the ref trace on ours: slope < 1 means ours moves too much
    A = np.vstack([go[ok] - go[ok].mean(), np.ones(ok.sum())]).T
    sl = np.linalg.lstsq(A, gr[ok] - gr[ok].mean(), rcond=None)[0][0]
    print(f'ref = {sl:.3f} x ours (deviations from the mean)')
    # what the difference follows
    m = 0.5 * (sb[BAND][0] + sb[BAND][1])
    pk = np.abs(m)
    fast = lfilter([0.02], [1, -0.98], pk); slow = lfilter([0.0005], [1, -0.9995], pk)
    feat = {'band |mid| (96 max)': np.array([pk[i * w:(i + 1) * w].max() for i in range(len(pk) // w)]),
            'band rms 2 ms': np.array([np.sqrt(np.mean(m[i * w:(i + 1) * w] ** 2)) for i in range(len(m) // w)]),
            'fast env': fast[::w][:len(pk) // w], 'slow env': slow[::w][:len(pk) // w]}
    for k, v in feat.items():
        v = 20 * np.log10(v[N.PRE // w:][:len(dg)] + 1e-9)
        print(f'   corr(diff, {k}) {np.corrcoef(dg[ok], v[ok])[0, 1]:+.3f}')
    dref = np.diff(gr)
    up = np.concatenate([[False], dref < 0]) & ok; dn = np.concatenate([[False], dref > 0]) & ok
    print(f'   while ref gain falls (attack): diff {np.mean(dg[up]):+.3f}; rises (release): {np.mean(dg[dn]):+.3f}')
    # lagged correlation of the gain traces: is ours early or late?
    a, b = gr[ok] - gr[ok].mean(), go[ok] - go[ok].mean()
    for lag in (-4, -2, -1, 0, 1, 2, 4):
        print(f'   lag {lag:+d} x {w}: corr {np.corrcoef(a[max(0, lag):len(a) + min(0, lag)], b[max(0, -lag):len(b) + min(0, -lag)])[0, 1]:.4f}')
