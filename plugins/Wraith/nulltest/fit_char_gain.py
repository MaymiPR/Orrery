"""Character stage, the dynamics fitted to the gain itself (MEASUREMENTS.md "Character"): the
reference's gain trajectory read through the side channel (probe_side.py: L = d + p, R = d - p, the detector hears
d only) against ours read the same way, CMA-ES over Source/dsp/Character.h's constants (fit_char.run_cma). The score
per case is fit_char.score on the demodulated gains (energy-weighted plus the mean of 50 ms windows), so quiet
passages and the gaps between hits count. A held-out set is reported beside it.

    python fit_char_gain.py [--iters 150] [--start renders/char_fit.json] [--out renders/char_gain_fit.json]
    python fit_char_gain.py --eval [--start ...]
"""
import argparse, json, os
import numpy as np
from scipy.signal import butter, filtfilt
import nulltest_lib as nl
import wr_ref as h
import fit_char as fc

FS = 48000
FP, PDB = 4000.0, -46.0
PARAMS = [('expThresholdDb', -55.0, -80.0, -30.0, False), ('expRatio', 2.2, 1.0, 6.0, False), ('expKneeDb', 10.0, 0.0, 30.0, False),
          ('expAttackMs', 20.0, 0.1, 2000.0, True), ('expReleaseMs', 2.0, 0.1, 500.0, True),
          ('expDetAttackMs', 1.0, 0.01, 100.0, True), ('expDetReleaseMs', 350.0, 10.0, 5000.0, True),
          ('cmpThresholdDb', -20.0, -40.0, 0.0, False), ('cmpRatio', 33.0, 1.5, 200.0, True), ('cmpKneeDb', 6.6, 0.0, 30.0, False),
          ('cmpAttackMs', 1.3, 0.02, 50.0, True), ('cmpReleaseLowMs', 53.0, 1.0, 2000.0, True), ('cmpReleaseHighMs', 137.0, 1.0, 2000.0, True),
          ('cmpReleaseSwitchDb', 13.0, 0.0, 40.0, False), ('cmpMakeupDb', 0.3, -6.0, 6.0, False)]
FIXED = {'detRmsMs': 0.0, 'charPostMask': 0.0, 'clipDrive': 0.0}


def probe():
    t = np.arange(int(5 * FS)) / FS
    return (10 ** (PDB / 20) * np.sin(2 * np.pi * FP * t)).astype(np.float32)


def cases():
    st = lambda lv, hold, f=1000: nl.steps(lv, hold, f=f)
    bursts = np.concatenate([nl.noise(0.5, -40 if k % 2 == 0 else -12, seed=k) for k in range(6)])
    long = lambda lv: np.concatenate([nl.tone(1000, 1.0, -40), nl.tone(1000, 2.0, lv), nl.tone(1000, 1.0, -40)])
    train = [('long -10 c0', long(-10), 0, 8), ('long -3 c0', long(-3), 0, 8),
             ('steps a c0', st([-40, -10, -30, -6, -50, -20, -12, -60], 0.5), 0, 8),
             ('steps b c0', st([-40, -60, -30, -70, -20, -80, -45, -90], 0.6), 0, 8),
             ('steps c c50', st([-50, -25, -45, -15, -60, -35], 0.7), 50, 0),
             ('steps d c-50', st([-30, 0, -20, -6, -40, -10], 0.7, 300), -50, 0),
             ('bursts c0', bursts, 0, 0),
             ('drums c0 f8', nl.drums(4.0, -6.0), 0, 8),
             ('drums c50 f-30', nl.drums(4.0, -6.0), 50, -30),
             ('drums c-50 f50', nl.drums(4.0, -6.0), -50, 50),
             ('music c0 f8', nl.stereo(nl.music(4.0, -10.0)).mean(0), 0, 8),
             ('music c50 f-30', nl.stereo(nl.music(4.0, -10.0)).mean(0), 50, -30)]
    held = [('long -20 c0', np.concatenate([nl.tone(1000, 1.0, -40), nl.tone(1000, 2.0, -20), nl.tone(1000, 1.0, -40)]), 0, 8),
            ('music c25 f-30', nl.stereo(nl.music(4.0, -12, seed=11)).mean(0), 25, -30),
            ('pink c-25', nl.pink(3.0, -20, seed=4), -25, 0),
            ('drums c50 f20', nl.drums(3.0, -10, seed=9), 50, 20)]
    return train, held


def ms(d, p):
    return np.stack([d + p[:len(d)], d - p[:len(d)]]).astype(np.float32)


def jobs_of(cs, with_probe=True):
    p = probe() if with_probe else np.zeros(5 * FS, np.float32)
    return [dict(x=ms(np.asarray(x, np.float32), p), norm=h.ONLY('CHAR'), params={'Compression': c, 'Focus': fo}) for _, x, c, fo in cs]


_B = butter(4, 1500 / (FS / 2))


def demod(y, y0=None):
    s = 0.5 * (y[0] - y[1]) - (0.5 * (y0[0] - y0[1]) if y0 is not None else 0)
    t = np.arange(len(s)) / FS
    z = s * np.exp(-2j * np.pi * FP * t) * 2 / 10 ** (PDB / 20)
    return filtfilt(*_B, z.real) + 1j * filtfilt(*_B, z.imag)


def ref_gains(cs):
    a = h.render_many(jobs_of(cs), 'ref', cache=True); b = h.render_many(jobs_of(cs, False), 'ref', cache=True)
    return [demod(y, y0) for y, y0 in zip(a, b)], [np.asarray(x, np.float32) for _, x, _, _ in cs]


def gscore(zr, zo, x):
    """the gain error as the stage's output would show it: fit_char.score on (gain x signal) for both"""
    xs = np.asarray(x, np.float64)
    return fc.score([np.stack([(zr * xs).real, (zr * xs).imag])], [np.stack([(zo * xs).real, (zo * xs).imag])])[0]


def make_eval(cs, refs, xs):
    jobs = jobs_of(cs)
    def evaluate(tunes, _tj=None, _tref=None):
        outs = h.render_many([dict(j, tune=t) for t in tunes for j in jobs], 'model')
        n = len(jobs)
        return [[gscore(refs[i], demod(outs[k * n + i]), xs[i]) for i in range(n)] for k in range(len(tunes))]
    return evaluate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iters', type=int, default=150)
    ap.add_argument('--out', default=os.path.join(h.PLUGIN, 'nulltest', 'renders', 'char_gain_fit.json'))
    ap.add_argument('--start', default=None)
    ap.add_argument('--eval', action='store_true')
    ap.add_argument('--sigma', type=float, default=0.12)
    a = ap.parse_args()
    train, held = cases()
    tr, tx = ref_gains(train); hr, hx = ref_gains(held)
    ev_t, ev_h = make_eval(train, tr, tx), make_eval(held, hr, hx)
    start = json.load(open(a.start)) if a.start else {}
    t0 = dict(FIXED, **{k: start.get(k, s) for k, s, *_ in PARAMS})
    if a.eval:
        for label, cs, ev in (('train', train, ev_t), ('held-out', held, ev_h)):
            for (name, *_), r in zip(cs, ev([t0])[0]): print(f'{label:8s} {name:18s} {r:7.1f} dB')
        return
    fc.evaluate = ev_t
    best = fc.run_cma(fc.from_tune(t0, PARAMS), None, None, a.iters, a.sigma, a.out, PARAMS, FIXED)
    t = fc.to_tune(best[0], PARAMS, FIXED)
    print(json.dumps(t, indent=1))
    for (name, *_), r in zip(held, ev_h([t])[0]): print(f'held-out {name:18s} {r:7.1f} dB')


if __name__ == '__main__':
    main()
