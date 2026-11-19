"""Nulls of our processor ('model', tools/ScRender) against the reference, module by module, on program material:
the drum-like test signal of probe_order.py at two levels and an excerpt of a mastered track (reference/, local only).
    python null_modules.py [case ...]        (cases below; prints the null in dB per signal)"""
import os, sys
import numpy as np
import sc_ref as o
from probe_order import drums

TRACK = os.path.join(o.ROOT, 'reference', 'demo_future_house.wav')


def signals():
    s = {'drums': drums(), 'drums -12': drums() * 10 ** (-12 / 20)}
    if os.path.exists(TRACK):
        import scipy.io.wavfile as wf, scipy.signal as sg
        fs, a = wf.read(TRACK)
        a = a.astype(np.float64) / (32768.0 if a.dtype == np.int16 else 1.0)
        a = sg.resample_poly(a[int(20 * fs):int(26 * fs)], 160, 147, axis=0).T.astype(np.float32)
        s['track'] = a
        s['track -10'] = a * 10 ** (-10 / 20)
    return s


EQ = lambda **g: {**o.ONLY('eq'), **{f'EQ {k}': v for k, v in g.items()}}
CASES = {
    'eq 1k 6': dict(params=EQ(**{'1kHz': 6})),
    'eq 1k 3': dict(params=EQ(**{'1kHz': 3})),
    'eq 40 6': dict(params=EQ(**{'40Hz': 6})),
    'eq 100 6': dict(params=EQ(**{'100Hz': 6})),
    'eq 3k 6': dict(params=EQ(**{'3kHz': 6})),
    'eq 10k 6': dict(params=EQ(**{'10kHz': 6})),
    'eq all 4': dict(params=EQ(**{'40Hz': 4, '100Hz': 4, '1kHz': 4, '3kHz': 4, '10kHz': 4})),
    'comp a': dict(params={**o.ONLY('comp'), 'Comp Amount': 1}, hidden={'ids.compression.mode': 'Mode A'}),
    'comp b': dict(params={**o.ONLY('comp'), 'Comp Amount': 1}, hidden={'ids.compression.mode': 'Mode B'}),
    'sub 1': dict(params={**o.ONLY('sub'), 'Par Sub Level': 1}),
    'harm 1': dict(params={**o.ONLY('harm'), 'Harm Amount': 1}),
    'harm 0.8': dict(params={**o.ONLY('harm'), 'Harm Amount': 0.8}),
    'harm 0.6': dict(params={**o.ONLY('harm'), 'Harm Amount': 0.6}),
    'harm 0.3': dict(params={**o.ONLY('harm'), 'Harm Amount': 0.3}),
    'loud 1': dict(params={**o.ONLY('loud'), 'Par Loud Level': 1}),
    'lift 1': dict(params={**o.ONLY('lift'), 'Lift Amount': 1}),
    'drive a hp on': dict(params=o.ONLY('drive', hipass=1)),
    'drive a hp off': dict(params=o.ONLY('drive', hipass=0)),
    'grit 1': dict(params={**o.ONLY('grit'), 'Par Grit Level': 1}),
    'grit 0.731': dict(params={**o.ONLY('grit'), 'Par Grit Level': 0.731}),
    'low 1': dict(params={**o.ONLY('low'), 'Par Low Level': 1}),
}


def run(names, tune=None):
    sig = signals()
    out = {}
    for n in names:
        jobs = [dict(x=x, **CASES[n]) for x in sig.values()]
        ref = o.render_many(jobs, cache=True)
        ours = o.render_many([dict(j, tune=tune or {}) for j in jobs], plugin='model')
        out[n] = {k: o.null_db(r, m) for k, r, m in zip(sig, ref, ours)}
        print(f'{n:12s}', '  '.join(f'{k} {v:6.1f}' for k, v in out[n].items()))
    return out


if __name__ == '__main__':
    run(sys.argv[1:] or list(CASES))
