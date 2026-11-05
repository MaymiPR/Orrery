"""Null tests with the external side-chain (EXT, set through each plug-in's saved state): program material on the main
input, other material on the side-chain bus, through the reference and our VST3 (RefRender, sc=), defaults and
character only. Writes nulltest/results_sidechain.json.

    python null_sidechain.py"""
import json, os
import numpy as np
import tgp, nulltest as N, stress as S, vst3state as V

REF = os.path.join(tgp.ROOT, 'reference')
HERE = os.path.dirname(os.path.abspath(__file__))


def states():
    d = os.path.join(tgp.CACHE, 'states'); os.makedirs(d, exist_ok=True)
    ours = os.path.join(d, 'positron_sidechain_ext.bin')
    open(ours, 'wb').write(V.wrap(V.own_state(sidechain=1)))
    return {'ref': os.path.join(REF, 'state_sidechain_ext.bin'), 'ours': ours}


if __name__ == '__main__':
    pad = lambda x: np.concatenate([np.zeros((2, N.PRE) if x.ndim == 2 else N.PRE, np.float32), x], axis=-1)
    st = states()
    cases = [('music -10, side-chain drums -6', N.sig_music(-10), N.sig_drums(-6, 4), {}),
             ('music -10, side-chain pink -10', N.sig_music(-10), N.sig_noise(-10, seed=7), {}),
             ('music -10, side-chain bass -6', N.sig_music(-10), S.sig_bass(-6), {}),
             ('music -2, side-chain drums -6', N.sig_music(-2), N.sig_drums(-6, 4), {}),
             ('music -10, side-chain silent', N.sig_music(-10), 0 * N.sig_noise(-10), {}),
             ('music -10, side-chain drums -6, 200 %', N.sig_music(-10), N.sig_drums(-6, 4), {'Character': 1.0}),
             ('character only: music -10, side-chain drums -6', N.sig_music(-10), N.sig_drums(-6, 4), tgp.CHAR_ONLY),
             ('character only: pink -10, side-chain music -10', N.sig_noise(-10), N.sig_music(-10, seed=4), tgp.CHAR_ONLY)]
    res = {}
    out = {}
    for pl in ('ref', 'ours'):
        jobs = [dict(x=pad(x), sc=pad(sc), state=st[pl], norm=nm) for _, x, sc, nm in cases]
        out[pl] = tgp.render_many(jobs, pl, cache=(pl == 'ref'))
    for (name, *_), r, o in zip(cases, out['ref'], out['ours']):
        d = round(float(N.residual_db(r, o)), 2)
        res[name] = d
        print(f'{d:8.2f} dB   {name}', flush=True)
    json.dump(res, open(os.path.join(HERE, 'results_sidechain.json'), 'w'), indent=1)
