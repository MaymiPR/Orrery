"""The high band's steady gain curve fitted directly to the reference's tone staircase (measure_high_release.staircase, 8 kHz, -24 ...
+3 dBFS in 0.5 dB steps, read through the band's measured shaper): mix, threshold, ratio and knee of the band's gain
computer (charsim), the detector a sample-peak follower with the release read from tone drops (measure_high_release.py, 48 dB/s),
no slow second detector. Prints the fitted law and the curve's error, ref against the fit and against the table.

    python fit_high_static.py [amount 0..1] [release ms]"""
import sys
import numpy as np
from scipy.optimize import least_squares
import tgp, ident as I, charmodel as CM, charsim as C, hirel as H
from measure_high_trace3 import header_laws

if __name__ == '__main__':
    amt = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    rel = float(sys.argv[2]) if len(sys.argv) > 2 else 181.0
    f = 8000.0
    x, levs, n = H.staircase(f)
    levs_, cr, co = H.static_curve(amt, f)
    law = header_laws(int(round(amt * 16)))['high']
    s = CM.prep(x)[1][2]
    m = 0.5 * (s[0] + s[1])
    med = lambda g: np.array([20 * np.log10(np.median(g[I.PRE + i * n + n // 2:I.PRE + (i + 1) * n])) for i in range(len(levs))])
    def curve(q, extra=None):
        mix, th, ratio, knee = q
        p = dict(mix=mix, thresh=th, ratio=ratio, knee=knee, attack=law['attack'], release=rel)
        if extra: p.update(extra)
        return med(C.band_gain(m, p, peak=1))
    sel = levs >= -20
    r = least_squares(lambda q: (curve(q) - cr)[sel], [law['mix'], law['thresh'], law['ratio'], law['knee']],
                      bounds=([0, -40, 1, 0], [1, 0, 20, 30]))
    tab = {k: law[k] for k in ('attack', 'release', 'attack2', 'release2', 'slowOffset')}
    ct = curve([law['mix'], law['thresh'], law['ratio'], law['knee']], tab)
    print(f'amount {amt * 200:.0f} %: fitted mix {r.x[0]:.4f} thresh {r.x[1]:.3f} ratio {r.x[2]:.3f} knee {r.x[3]:.3f}'
          f'  (table {law["mix"]:.4f} {law["thresh"]:.3f} {law["ratio"]:.3f} {law["knee"]:.3f})')
    print(f'   curve error rms: fit {np.sqrt(np.mean((curve(r.x) - cr)[sel] ** 2)):.4f} dB, table {np.sqrt(np.mean((ct - cr)[sel] ** 2)):.4f} dB, '
          f'ours (plug-in) {np.sqrt(np.mean((co - cr)[sel] ** 2)):.4f} dB')
    for l, a, b, c in zip(levs[sel][::4], cr[sel][::4], curve(r.x)[sel][::4], ct[sel][::4]): print(f'   {l:6.1f} ref {a:8.3f} fit {b:8.3f} table {c:8.3f}')
