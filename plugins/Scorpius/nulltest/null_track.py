"""Null tests on a real mix: a demo track (reference/demo_future_house.wav, git-ignored: it is not ours to publish)
through the reference and our built VST3 at the track's own rate, block 512, with the settings a user would try in a
host: the default preset, each factory preset (null_chain.py), each module switched off in turn, and the compression
and the drive switched off and on again while the track plays.

    python null_track.py [wav] [--model]     (--model: our processor through tools/ScRender instead of the VST3)
Writes nulltest/results_track.json: per case the residual over the whole track and over its worst second, in dB."""
import json, os, sys
import numpy as np
import scipy.io.wavfile as wf
import sc_ref as o
import null_chain as C

WAV = os.path.join(o.ROOT, 'reference', 'demo_future_house.wav')
BLOCK = 512
BATCH = 4               # cases per host run: a whole track per case is held in memory


def load(path):
    """(2, n) float32 and the sample rate of a PCM or float WAV"""
    fs, a = wf.read(path)
    if a.dtype.kind == 'u': a = (a.astype(np.float64) - 128.0) / 128.0
    elif a.dtype.kind == 'i': a = a.astype(np.float64) / float(2 ** (8 * a.dtype.itemsize - 1))
    a = a.T if a.ndim == 2 else np.stack([a, a])
    if a.shape[0] == 1: a = np.vstack([a, a])
    return a[:2].astype(np.float32), int(fs)


def cases(fs, n):
    """[(name, job settings)]; the switches move at 20 s and 40 s, or at a third and two thirds of a short track"""
    t1 = 20 if n >= 45 * fs else max(1, int(n / fs / 3))
    t2 = 2 * t1
    on = lambda t: int(t * fs) // BLOCK * BLOCK
    cs = [('default', {})]
    cs += [(f'preset {name}', s) for name, s in C.SETTINGS.items() if name != 'default']
    # compression off is the preset "no compression"
    cs += [(f'{key} off', dict(params={name: 0})) for key, name in o.MODULES.items() if key != 'comp']
    cs += [(f'{key} switched off at {t1} s, on at {t2} s', dict(auto=[(o.MODULES[key], on(t1), 0), (o.MODULES[key], on(t2), 1)]))
           for key in ('comp', 'drive')]
    return cs


def residual(a, b):
    return 10 * np.log10(max(float(np.sum((a - b) ** 2)), 1e-30) / max(float(np.sum(a ** 2)), 1e-30))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    unknown = [a for a in sys.argv[1:] if a.startswith('--') and a != '--model']
    if unknown:
        print(__doc__)
        sys.exit(2)
    path = args[0] if args else WAV
    if not os.path.isfile(path):
        print(f'no track: {os.path.relpath(path, o.ROOT) if not args else path} is missing (the demo track is local, '
              'git-ignored); nothing rendered')
        sys.exit(2)
    plugin = 'model' if '--model' in sys.argv else 'ours'
    needs = [('the renderer', o.SCEXE)] if plugin == 'model' else [('RefRender', o.EXE), ('the VST3', o.PLUGINS['ours'][0])]
    missing = [what for what, p in needs if not os.path.exists(p)]
    if missing:
        print('not built: ' + ', '.join(missing) + ': nothing rendered')
        sys.exit(2)
    x, fs = load(path)
    skip = int(o.SKIP * fs / o.FS)                  # the reference ramps its settings in at the start of a render
    cs = cases(fs, x.shape[1])
    res = {}
    for i in range(0, len(cs), BATCH):
        part = cs[i:i + BATCH]
        jobs = [dict(x=x, **s) for _, s in part]
        ref = o.render_many(jobs, 'ref', fs=fs, block=BLOCK, cache=True)
        ours = o.render_many(jobs, plugin, fs=fs, block=BLOCK)
        for (name, _), r, y in zip(part, ref, ours):
            n = min(r.shape[1], y.shape[1])
            a, b = r[:, skip:n].astype(np.float64), y[:, skip:n].astype(np.float64)
            d = residual(a, b)
            # the worst second, among the seconds where the reference is not silent (above -100 dBFS RMS)
            sec = {k // fs: residual(a[:, k:k + fs], b[:, k:k + fs]) for k in range(0, a.shape[1] - fs + 1, fs)
                   if np.mean(a[:, k:k + fs] ** 2) > 1e-10}
            at = max(sec, key=sec.get) if sec else 0
            worst = sec[at] if sec else d
            res[name] = dict(residual_dB=round(float(d), 2), worst_second_dB=round(float(worst), 2), worst_at_s=int(at))
            print(f'{d:8.2f} dB   worst second {worst:7.2f} dB at {at:3d} s   {name}', flush=True)
        del ref, ours
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results_track.json')
    open(out, 'w', encoding='utf-8', newline='\n').write(json.dumps(res, indent=1) + '\n')
    print('wrote', os.path.relpath(out, o.ROOT))
