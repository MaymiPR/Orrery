"""The reference's renders checked for repeatability: every nulltest.py case (and optionally the stress cases) rendered
fresh twice and compared with the cached render. A deterministic host gives no difference (below -200 dB); a cached
render that disagrees with two agreeing fresh ones is replaced.

    python refcheck.py [--stress] [--fix]"""
import os, sys
import numpy as np
import tgp, nulltest as N


def diff_db(a, b):
    a, b = a[:, N.PRE:], b[:, N.PRE:]
    return 10 * np.log10(max(np.sum((a - b) ** 2), 1e-40) / max(np.sum(a ** 2), 1e-30))


def check(jobs, names, fix=False):
    cached = tgp.render_many(jobs, 'ref', cache=True)
    f1 = tgp.render_many(jobs, 'ref'); f2 = tgp.render_many(jobs, 'ref')
    bad = 0
    for nm, j, c, a, b in zip(names, jobs, cached, f1, f2):
        d12, d1c = diff_db(a, b), diff_db(a, c)
        flag = '' if max(d12, d1c) < -150 else '   <-- differs'
        bad += bool(flag)
        print(f'{d12:8.1f} {d1c:8.1f}   {nm}{flag}')
        if flag and fix and d12 < -150:
            k = tgp._key(j, 'ref', tgp.FS, 512)
            np.save(os.path.join(tgp.CACHE, k + '.npy'), a); print('      cache replaced')
    return bad


if __name__ == '__main__':
    sigs = {k: f() for k, f in N.SIGNALS.items()}
    pad = lambda x: np.concatenate([np.zeros((2, N.PRE) if x.ndim == 2 else N.PRE, np.float32), x], axis=-1)
    jobs = [dict(x=pad(sigs[s]), norm=nm, params=pm) for _, s, nm, pm in N.CASES]
    print('fresh-fresh  fresh-cache (dB)')
    bad = check(jobs, [c[0] for c in N.CASES], '--fix' in sys.argv)
    print(bad, 'of', len(jobs), 'differ')
