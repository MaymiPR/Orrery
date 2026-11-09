"""The first null test of a new project: proves the harness, the hosts and the build before any DSP is written.
Run it right after the first build:

    python first_null.py                     # the four checks below
    python first_null.py --ref-bypass Bypass # also: the reference's host bypass against a delayed copy of the input

Checks (PASS / FAIL, the thresholds are the ones every project reached):
  1. the reference renders: output not silent, latency read from RefRender
  2. our processor's bypass (PoRender) is the input delayed by the reported latency: below -100 dB
  3. our built VST3's bypass (RefRender) is the same: below -100 dB (the build and the renderer agree)
  4. our VST3 and our renderer agree at default settings on noise: below -100 dB (the check every number must pass)
  5. (--ref-bypass NAME) the reference's bypass is the input delayed by its latency: below -80 dB; if not, the latency
     or the state is wrong (docs/null-testing.md in the knowledge base: start-up state, settle time, parameters before the first block)
"""
import argparse, sys
import numpy as np
import tgp as h
import nulltest_lib as nl


def check(name, db, limit):
    ok = db < limit
    print(f'{"PASS" if ok else "FAIL"}  {name}: {db:7.1f} dB (limit {limit})')
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref-bypass', default=None, help='the reference bypass parameter as hosts show it, e.g. Bypass')
    ap.add_argument('--fs', type=int, default=h.FS)
    a = ap.parse_args()
    fs = a.fs
    x = nl.stereo(nl.noise(3.0, -18.0, fs=fs, seed=7))
    skip = fs // 2
    ok = True

    y_ref = h.render(x, 'ref', fs=fs)
    lat = h.latency('ref', fs)
    print(f'reference: {y_ref.shape[1]} frames, rms {nl.rms_db(y_ref):.1f} dB, latency {lat} samples at {fs} Hz')
    ok &= check('reference not silent (rms above -60 dB)', -nl.rms_db(y_ref), 60.0)

    y_model = h.render(x, 'model', fs=fs, norm={'Bypass': 1})
    ok &= check('our renderer: bypass = delayed input', nl.residual_db(x, y_model, skip), -100.0)

    y_vst3 = h.render(x, 'ours', fs=fs, norm={'Bypass': 1})
    ok &= check('our VST3: bypass = delayed input', nl.residual_db(x, y_vst3, skip), -100.0)

    y1 = h.render(x, 'model', fs=fs)
    y2 = h.render(x, 'ours', fs=fs)
    ok &= check('our VST3 = our renderer at defaults', nl.residual_db(y1, y2, skip), -100.0)

    if a.ref_bypass:
        y_rb = h.render(x, 'ref', fs=fs, norm={a.ref_bypass: 1})
        lag = nl.find_lag(x, y_rb)
        print(f'reference bypass lag by cross-correlation: {lag} samples (RefRender compensated {lat})')
        ok &= check('reference: bypass = delayed input', nl.residual_db(x, y_rb, skip), -80.0)

    print('ALL PASS' if ok else 'SOMETHING FAILED')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
