"""How sensitive a case is to tiny differences: the reference against itself with white noise added to the input at a
level far below anything audible (default -100 dBFS RMS), and the same for ours. A case whose reference moves by much
more than the perturbation sits on decisions (limiter plans on near-ties) that no model short of bit-exact can follow;
its residual against the reference has that floor.

    python probe_sensitivity.py "lim: pink -6" [-100]"""
import sys
import numpy as np
import tgp, nulltest as N

if __name__ == '__main__':
    pat = sys.argv[1]; lvl = float(sys.argv[2]) if len(sys.argv) > 2 else -100.0
    sigs = {k: f() for k, f in N.SIGNALS.items()}
    pad = lambda x: np.concatenate([np.zeros((2, N.PRE) if x.ndim == 2 else N.PRE, np.float32), x], axis=-1)
    st = lambda x: np.vstack([x, x]) if x.ndim == 1 else x
    for name, s, nm, pm in [c for c in N.CASES if pat in c[0]]:
        x = st(pad(sigs[s])).astype(np.float64)
        e = np.random.default_rng(5).standard_normal(x.shape) * 10 ** (lvl / 20)
        jobs = [dict(x=x.astype(np.float32), norm=nm, params=pm), dict(x=(x + e).astype(np.float32), norm=nm, params=pm)]
        r = tgp.render_many(jobs, 'ref', cache=True); o = tgp.render_many(jobs, 'model')
        print(f'{name}: perturbation {lvl:.0f} dBFS -> reference moves {N.residual_db(r[0], r[1]):.2f} dB, ours {N.residual_db(o[0], o[1]):.2f} dB; '
              f'ref vs ours {N.residual_db(r[0], o[0]):.2f} dB')
