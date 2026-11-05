"""The doubler's voice constants refined on the nulls (MEASUREMENTS.md "Doubler"), from the
regressed voice filter (fit_voice_filter.py): CMA-ES (fit_char.run_cma) over gain, filters, centre, depth and phase
and the lows that pass the line (an undelayed low-pass), on pink, music and drums at Mix 1 and Mix 0.43. The
reference's pseudo-random wobble (0.044 ms rms) is not modelled, so the full-wet nulls keep its floor. Runs on the
second renderer (WR_RENDER=dev).

    python fit_dbl_voice.py [--iters 40] [--start renders/dbl_t1.json]
"""
import argparse, json, os
import numpy as np
import nulltest_lib as nl
import ts as h
import fit_char as fc

PARAMS = [('dblVoiceGain', 0.3365, 0.1, 0.8, False), ('dblHpHz', 363.7, 50.0, 1500.0, True), ('dblLpHz', 12879.0, 4000.0, 22000.0, True),
          ('dblLpQ', 0.368, 0.2, 2.0, True), ('dblLp2Hz', 10731.0, 4000.0, 22000.0, True), ('dblLp2Q', 0.864, 0.2, 2.0, True),
          ('dblCenterMs', 7.5317, 7.3, 7.8, False), ('dblDepthMs', 1.4994, 1.3, 1.7, False), ('dblPhase', 0.0098, -0.03, 0.05, False),
          ('dblBassHz', 90.0, 20.0, 400.0, True), ('dblBassQ', 0.6, 0.3, 1.5, True), ('dblBassGain', 1.0, 0.0, 2.0, False)]
FIXED = {}
SIGS = [nl.stereo(nl.pink(4, -18, seed=11)), nl.music(4, -10), nl.stereo(nl.drums(4, -6))]
SETS = [(1.0, 0.5), (0.4344, 0.6166)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iters', type=int, default=40)
    ap.add_argument('--start', default=os.path.join(h.PLUGIN, 'nulltest', 'renders', 'dbl_t1.json'))
    ap.add_argument('--out', default=os.path.join(h.PLUGIN, 'nulltest', 'renders', 'dbl_fit.json'))
    a = ap.parse_args()
    jobs = [dict(x=x, norm=h.ONLY('DBL'), params={'Doubler Mix': m, 'Doubler Stereo': s}) for x in SIGS for m, s in SETS]
    refs = h.render_many(jobs, 'ref', cache=True)

    def evaluate(tunes, _a=None, _b=None):
        outs = h.render_many([dict(j, tune=t) for t in tunes for j in jobs], 'model')
        n = len(jobs)
        return [[nl.residual_db(refs[i], outs[k * n + i], 4800) for i in range(n)] for k in range(len(tunes))]
    fc.evaluate = evaluate
    start = json.load(open(a.start))
    best = fc.run_cma(fc.from_tune(start, PARAMS), None, None, a.iters, 0.08, a.out, PARAMS, FIXED)
    print(json.dumps(fc.to_tune(best[0], PARAMS, FIXED), indent=1))


if __name__ == '__main__':
    main()
