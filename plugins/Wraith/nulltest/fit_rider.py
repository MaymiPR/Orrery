"""Gain Rider timing (MEASUREMENTS.md "Rider"): the static law is exact (probe_rider.py); this fits the detector's
attack (a multiple of Speed), its release, a gain smoothing time and the level offset with CMA-ES on level steps at
three speeds, music and noise bursts, with a held-out set (fit_char.py's loop and score).

    python fit_rider.py [--iters 60]       (renders through WrRenderDev: WR_RENDER=dev is set here)
    python fit_rider.py --eval [--start renders/rider_fit.json]
"""
import os
os.environ.setdefault('WR_RENDER', 'dev')
import argparse, json
import numpy as np
import nulltest_lib as nl
import wr_ref as h
import fit_char as fc

PARAMS = [('riderAttackScale', 1.0, 0.1, 20.0, True), ('riderReleaseMs', 100.0, 5.0, 3000.0, True),
          ('riderSmoothMs', 1.0, 0.01, 500.0, True), ('riderOffsetDb', 18.58, 12.0, 21.0, False)]


def cases():
    st = nl.stereo(nl.steps([-30, -10, -30, -20, -40, -20], 1.0, f=1000.0)).astype(np.float32)
    bursts = nl.stereo(np.concatenate([nl.noise(0.7, -45 if k % 2 == 0 else -20, seed=20 + k) for k in range(6)])).astype(np.float32)
    def j(x, speed, amount=1.0, floor=-50): return dict(x=x, norm=h.ONLY('RIDER'), params={'Gain Rider Speed': speed,
                                                         'Gain Rider Amount': amount, 'Gain Rider Floor': floor})
    train = [('steps s0.001', j(st, 0.001)), ('steps s0.003', j(st, 0.003)), ('steps s0.01', j(st, 0.01)),
             ('bursts s0.003', j(bursts, 0.003, 0.7, -30)),
             ('music s0.003', j(nl.stereo(nl.music(4.0, -14)).astype(np.float32), 0.003, 0.7, -30))]
    held = [('drums s0.006', j(nl.stereo(nl.drums(3.0, -12, seed=5)).astype(np.float32), 0.006, 0.8, -40)),
            ('pink s0.002', j(nl.stereo(nl.pink(3.0, -26, seed=6)).astype(np.float32), 0.002, 0.5, -45))]
    return train, held


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iters', type=int, default=60)
    ap.add_argument('--start', default=None)
    ap.add_argument('--eval', action='store_true')
    ap.add_argument('--out', default=os.path.join(h.PLUGIN, 'nulltest', 'renders', 'rider_fit.json'))
    a = ap.parse_args()
    train, held = cases()
    tj, hj = [c[1] for c in train], [c[1] for c in held]
    tref, href = h.render_many(tj, 'ref', cache=True), h.render_many(hj, 'ref', cache=True)
    start = json.load(open(a.start)) if a.start else {}
    if not a.eval:
        best = fc.run_cma(fc.from_tune(start, PARAMS), tj, tref, a.iters, 0.2, a.out, PARAMS, {})
        start = fc.to_tune(best[0], PARAMS, {})
    t = {k: start.get(k, s) for k, s, *_ in PARAMS}
    print(json.dumps(t, indent=1))
    for label, cs, jb, rf in (('train', train, tj, tref), ('held-out', held, hj, href)):
        for (name, _), r in zip(cs, fc.evaluate([t], jb, rf)[0]): print(f'{label:8s} {name:16s} {r:7.1f} dB')


if __name__ == '__main__':
    main()
