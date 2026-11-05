"""Character stage, the expander alone (MEASUREMENTS.md "Character"): its static curve, gain
timing and its own peak detector, fitted to the reference's gain (read through the side channel, fit_char_gain.py)
as an rms dB error on quiet tone steps (where the expander acts; the energy-weighted score cannot see it), plus the
drums' energy-weighted gain score. The compressor keeps its shipped constants. Runs on WR_RENDER=dev.

    python fit_expander.py [--iters 50]
"""
import argparse, json, os
import numpy as np
import nulltest_lib as nl
import ts as h
import fit_char as fc
import fit_char_gain as fg

PARAMS = [('expThresholdDb', -55.0, -80.0, -30.0, False), ('expRatio', 2.2, 1.0, 6.0, False), ('expKneeDb', 15.0, 0.0, 30.0, False),
          ('expAttackMs', 20.0, 0.1, 2000.0, True), ('expReleaseMs', 2.0, 0.1, 500.0, True),
          ('expDetAttackMs', 0.3, 0.01, 100.0, True), ('expDetReleaseMs', 358.0, 10.0, 5000.0, True)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iters', type=int, default=50)
    ap.add_argument('--out', default=os.path.join(h.PLUGIN, 'nulltest', 'renders', 'exp_fit.json'))
    a = ap.parse_args()
    st = lambda lv, hold: nl.steps(lv, hold)
    quiet = [('q1 c0', st([-40, -60, -30, -70, -20, -80, -45, -90], 0.6), 0, 8),
             ('q2 c0', st([-35, -55, -65, -50, -75, -45, -85, -60], 0.6), 0, 8),
             ('q3 c50', st([-50, -70, -40, -80, -55, -65], 0.8), 50, 0)]
    loud = [('drums c0 f8', nl.drums(4.0, -6.0), 0, 8), ('drums c50 f-30', nl.drums(4.0, -6.0), 50, -30),
            ('drums c-50 f50', nl.drums(4.0, -6.0), -50, 50), ('music c0 f8', nl.stereo(nl.music(4.0, -10.0)).mean(0), 0, 8)]
    cs = quiet + loud
    refs, xs = fg.ref_gains(cs)
    jobs = fg.jobs_of(cs)
    base = json.load(open(os.path.join(h.PLUGIN, 'nulltest', 'renders', 'char_shipped.json')))
    fixed = {k: v for k, v in base.items() if k not in dict((p[0], 1) for p in PARAMS)}
    sk = fg.FS // 10

    def evaluate(tunes, _a=None, _b=None):
        outs = h.render_many([dict(j, tune=t) for t in tunes for j in jobs], 'model')
        n = len(jobs); res = []
        for k in range(len(tunes)):
            row = []
            for i in range(n):
                zo = fg.demod(outs[k * n + i])
                if i < len(quiet):
                    d = 20 * np.log10(np.abs(refs[i][sk:]) / np.abs(zo[sk:]))
                    row.append(10 * np.log10(np.mean(d ** 2)) - 20)      # rms dB error as a score, 1 dB rms = -20
                else:
                    row.append(fg.gscore(refs[i], zo, xs[i]))
            res.append(row)
        return res
    fc.evaluate = evaluate
    t0 = dict(base, expDetAttackMs=0.3, expDetReleaseMs=358.0)
    for (name, *_), r in zip(cs, evaluate([t0])[0]): print(f'start {name:16s} {r:7.1f}')
    best = fc.run_cma(fc.from_tune(t0, PARAMS), None, None, a.iters, 0.1, a.out, PARAMS, fixed)
    t = fc.to_tune(best[0], PARAMS, fixed)
    for (name, *_), r in zip(cs, evaluate([t])[0]): print(f'fit   {name:16s} {r:7.1f}')
    print(json.dumps({k: t[k] for k, *_ in PARAMS}, indent=1))


if __name__ == '__main__':
    main()
