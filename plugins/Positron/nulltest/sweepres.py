"""Where the sweep's residual sits: the log sine sweep (20 Hz - 20 kHz, nulltest.sig_sweep) through the reference and
ours, cut into 50 ms windows; per window its frequency, the residual (dB re the reference's window) and the level of
ours re the reference (dB, positive = ours louder, i.e. compressing less). Defaults and character only.

    python sweepres.py [sweep dBFS] [--tune KEY=V ...]     (--tune: our processor with a DSP constant overridden)"""
import sys
import numpy as np
import tgp, nulltest as N

FS = tgp.FS
TUNE = {a.split('=')[0]: float(a.split('=')[1]) for i, a in enumerate(sys.argv) if i and sys.argv[i - 1] == '--tune'}


def table(r, o, db, step=0.05):
    k = np.log(20000 / 20) / N.SECS
    w = int(step * FS); rows = []
    for i in range(0, r.shape[1] - w + 1, w):
        a, b = r[:, i:i + w].astype(np.float64), o[:, i:i + w].astype(np.float64)
        ea = np.sum(a ** 2)
        if ea < 1e-20: continue
        f = 20 * np.exp(k * (i + w / 2) / FS)
        rows.append((f, 10 * np.log10(np.sum((a - b) ** 2) / ea), 10 * np.log10(np.sum(b ** 2) / ea)))
    return np.array(rows)


if __name__ == '__main__':
    db = float(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else -6.0
    x = N.sig_sweep(db)
    x = np.concatenate([np.zeros((2, N.PRE), np.float32), np.vstack([x, x])], -1)
    cases = [('defaults', {}), ('character only', tgp.CHAR_ONLY)]
    jobs = [dict(x=x, norm=nm) for _, nm in cases]
    ref = tgp.render_many(jobs, 'ref', cache=True)
    ours = tgp.render_many([dict(j, tune=TUNE) if TUNE else j for j in jobs], 'model')
    for (name, _), r, o in zip(cases, ref, ours):
        r, o = r[:, N.PRE:], o[:, N.PRE:]
        t = table(r, o, db)
        print(f'== {name}, sweep {db:+.0f} dBFS: whole {N.residual_db(r, o):.2f} dB')
        for lo, hi in ((20, 157), (157, 500), (500, 1000), (1000, 1500), (1500, 2000), (2000, 2500), (2500, 3000), (3000, 3500),
                       (3500, 5000), (5000, 10000), (10000, 20000)):
            m = (t[:, 0] >= lo) & (t[:, 0] < hi)
            if not m.any(): continue
            print(f'  {lo:6.0f} - {hi:6.0f} Hz   residual {np.max(t[m, 1]):7.2f} dB (max), {np.median(t[m, 1]):7.2f} (median)   '
                  f'ours re ref {np.min(t[m, 2]):+.3f} .. {np.max(t[m, 2]):+.3f} dB', flush=True)
