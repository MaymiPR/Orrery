"""The limiter at its maximum input gain (12 dB): nulls of the full chain, the limiter alone and the character section
alone on several signals, so the share of each stage in the full chain's residual shows.

    python null_lim_max.py [gain dB]"""
import sys
import numpy as np
import po_ref, nulltest as N, null_stress as S

if __name__ == '__main__':
    g = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0
    pad = lambda x: np.concatenate([np.zeros((2, N.PRE) if x.ndim == 2 else N.PRE, np.float32), x], axis=-1)
    sigs = ['music -10', 'music -2', 'drums -6', 'pink -10', 'bass -6', 'dynamic -4']
    setups = {'full chain': {}, 'limiter only': po_ref.LIM_ONLY, 'character only': po_ref.CHAR_ONLY}
    print(f'limiter input gain {g} dB' + ''.join(f'{k:>16s}' for k in setups))
    for s in sigs:
        x = pad(S.SIG[s]())
        jobs = [dict(x=x, norm=n, params={'Limiter Input Gain': g}) for n in setups.values()]
        r = po_ref.render_many(jobs, 'ref', cache=True); o = po_ref.render_many(jobs, 'model')
        print(f'{s:24s}' + ''.join(f'{N.residual_db(a, b):16.2f}' for a, b in zip(r, o)), flush=True)
