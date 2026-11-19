"""Null tests on a real mix: a demo track (reference/demo_future_house.wav, git-ignored: it is not ours to publish)
through the reference and our built VST3 at the track's own rate, block 512, with the settings a user would try in a
host: the start-up settings, each stage switched off in turn, each stage alone, and the reverb and the character
section switched off and on while the track plays. The track is a full mix, not a vocal, so it is a stress case for a
vocal chain: the levels, the bass and the density are beyond what the stages were fitted on. The reverb is the room
throughout (the reference plays its plate only with its editor open).

    python null_track.py [wav] [--model] [--vary]  (--model: our processor via WrRender instead of the VST3; --vary: irregular
                                               host blocks, as FL Studio sends them)
Writes nulltest/results_track.json (results_track_vary.json with --vary): per case the residual over the whole track
and over its worst second, in dB."""
import json, os, sys
import numpy as np
import wr_ref as h
import nulltest_lib as nl

WAV = os.path.join(h.ROOT, 'reference', 'demo_future_house.wav')
BLOCK = 512
NAMES = {'RIDER': 'rider', 'CHAR': 'character', 'EQ': 'eq', 'DBL': 'doubler', 'REV': 'reverb'}


def cases(fs, n):
    """(name, norm, auto); auto positions in samples of the track, on block boundaries"""
    off, on = n // 3 // BLOCK * BLOCK, 2 * n // 3 // BLOCK * BLOCK
    when = f'at {off / fs:.0f} s, on at {on / fs:.0f} s'
    toggle = lambda key: [(h.STATES[key], off, 0.0), (h.STATES[key], on, 1.0)]
    cs = [('start-up settings', {}, None), ('every stage on', h.ONLY(*h.STATES), None), ('every stage off', h.NONE, None)]
    cs += [(f'{NAMES[k]} off, the others on', h.ONLY(*(o for o in h.STATES if o != k)), None) for k in h.STATES]
    cs += [(f'{NAMES[k]} alone', h.ONLY(k), None) for k in h.STATES]
    cs += [(f'reverb switched off {when}', {}, toggle('REV')),
           (f'character switched off {when}', {}, toggle('CHAR'))]
    return cs


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    path = args[0] if args else WAV
    if not os.path.isfile(path):
        print(f'no track at {os.path.relpath(path, h.ROOT) if not args else path}: the demo track is local and git-ignored; '
              'put it there or name a WAV file')
        sys.exit(2)
    x, fs = nl.read_wav(path)
    x = nl.stereo(x[0] if x.shape[0] == 1 else x[:2])
    pre = fs // 10                                  # skipped: the first 0.1 s, as in nulltest.py
    cs = cases(fs, x.shape[1])
    jobs = [dict(x=x, norm=nm, auto=au) for _, nm, au in cs]
    vary = '--vary' in sys.argv
    model = '--model' in sys.argv
    settle = h.SETTLE.get(fs, 0)                    # the reference loads its reverb late at 44.1 kHz
    ref = h.render_many([dict(j, settle=settle) if settle else j for j in jobs], 'ref', fs=fs, block=BLOCK, cache=True, vary=vary)
    ours = h.render_many(jobs, 'model' if model else 'ours', fs=fs, block=BLOCK, vary=vary and not model)
    res = {}
    for (name, *_), r, o in zip(cs, ref, ours):
        d = nl.residual_db(r, o, pre)
        w, sec = nl.worst_second(r, o, pre, fs=fs)     # where it is worst, in seconds after the skipped start
        res[name] = dict(residual_dB=round(float(d), 2), worst_second_dB=round(float(w), 2), worst_at_s=int(sec))
        print(f'{d:8.2f} dB   worst second {w:7.2f} dB at {sec:3d} s   {name}', flush=True)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results_track_vary.json' if vary else 'results_track.json')
    json.dump(res, open(out, 'w'), indent=1)
    nl.summarize({k: v['residual_dB'] for k, v in res.items()})
