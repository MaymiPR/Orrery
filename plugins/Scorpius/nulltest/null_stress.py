"""Stress null tests of Scorpius: the reference against our processor over a wide grid of settings, levels, signals,
sample rates, block sizes and parameter automation, beyond the fixed cases of nulltest.py. Amounts, levels and gains
are taken between the fitted nodes on purpose (odd values), so interpolation is tested too; a seeded grid of random
settings covers what nobody thought of.

    python null_stress.py                    # every group, every run
    python null_stress.py --only random      # groups (or runs) whose name contains 'random'
    python null_stress.py --vst3             # our built VST3 instead of our renderer (tools/ScRender)
Writes nulltest/results_stress.json ("run | group | case / signal": residual in dB); with --only the new results are
merged into the file. The reference's renders come from its cache (nulltest/renders, local), ours never."""
import argparse, json, os, sys
import numpy as np
import scipy.signal as sg
import sc_ref as o
import null_chain as C
import probe_autom as A
from nulltest import at_rate
from probe_order import drums

FS = o.FS
SECS = 4.0
BANDS = ('40Hz', '100Hz', '1kHz', '3kHz', '10kHz')
AMOUNTS = (0.45, 0.7, 0.9)            # between the fitted nodes (the harmonics are fitted at 0.3, 0.6, 0.8 and 1)
PAR_LEVELS = (0.25, 0.55, 0.9)
STEPS = (-30, -24, -18, -12, -6, -3, -1)      # input level steps, dBFS peak


def at(x, db):
    """x with its peak at db dBFS"""
    return (x * 10 ** (db / 20) / np.max(np.abs(x))).astype(np.float32)


def mix(seed):
    """a dense stereo mix: the drum loop, a chord with a slow tremolo and pink noise, a little different per channel"""
    rng = np.random.default_rng(seed)
    t = np.arange(int(SECS * FS)) / FS
    d = drums(SECS, seed)
    ch = []
    for c in range(2):
        chord = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) for f in (110, 220.5, 277.2, 329.6, 659.3)) * 0.08
        chord = chord * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t + c))
        ch.append(d + chord + 0.05 * o.noise(SECS, 0, seed=seed + 10 + c, pink=True))
    return np.stack(ch)


def sig_bass(db=-6):
    """bass-heavy: a sub line with slides and the drum loop"""
    t = np.arange(int(SECS * FS)) / FS
    f = 40 + 25 * (np.sin(2 * np.pi * 0.4 * t) > 0) + 10 * np.sin(2 * np.pi * 0.13 * t)
    return at(np.sin(2 * np.pi * np.cumsum(f) / FS) * 0.7 + drums(SECS, 9) * 0.6, db)


def sig_bright(db=-8, seed=21):
    """treble-heavy: differentiated drums, sibilant noise bursts and a 6 to 12 kHz tone cluster"""
    rng = np.random.default_rng(seed)
    n = int(SECS * FS); t = np.arange(n) / FS
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) for f in (6100, 7900, 9300, 11800)) * 0.15
    hp = np.diff(rng.standard_normal(n + 1))
    env = (np.sin(2 * np.pi * 2.5 * t) > 0.6) * 1.0
    return at(x + hp * env * 0.4 + np.diff(drums(SECS, 4), prepend=0) * 2, db)


def sig_wide(db=-10):
    """the mix with extreme stereo: the right channel partly inverted, plus a left-only lead"""
    m = mix(8)
    t = np.arange(m.shape[1]) / FS
    lead = 0.25 * np.sin(2 * np.pi * 880 * t) * (np.sin(2 * np.pi * 0.5 * t) > 0)
    return at(np.stack([m[0] + lead, -0.7 * m[1] + 0.3 * m[0]]), db)


def sig_dynamic(db=-4):
    """quiet and loud passages: the mix with its peak at -30, -10 and the given level, a third of the time each"""
    m = at(mix(12), 0)
    n = m.shape[1] // 3
    g = np.concatenate([np.full(n, -30.0), np.full(n, -10.0), np.full(m.shape[1] - 2 * n, float(db))])
    return (m * 10 ** (g / 20)).astype(np.float32)


def sig_sweep(db=-6):
    """a logarithmic sine sweep, 20 Hz to 20 kHz, with 10 ms fades"""
    t = np.arange(int(SECS * FS)) / FS
    x = sg.chirp(t, 20, SECS, 20000, method='logarithmic', phi=-90)
    k = int(0.01 * FS); fade = np.ones(len(x)); fade[:k] = np.linspace(0, 1, k); fade[-k:] = np.linspace(1, 0, k)
    return (x * fade * 10 ** (db / 20)).astype(np.float32)


AUTOM = 'drums -12, 3 s'              # probe_autom.table()'s signal
SIG = {
    'drums': drums, 'drums -12': lambda: drums() * 10 ** (-12 / 20),
    'bass -6': sig_bass, 'bright -8': sig_bright, 'wide -10': sig_wide, 'dynamic -4': sig_dynamic, 'sweep -6': sig_sweep,
    AUTOM: lambda: drums()[:A.PRE + 3 * FS] * 10 ** (-12 / 20),
}
SIG.update({f'drums peak {v}': (lambda v=v: at(drums(), v)) for v in STEPS})
SIG.update({f'{k} peak {v}': (lambda f=f, v=v: f(v)) for k, f in (('bass', sig_bass), ('bright', sig_bright), ('wide', sig_wide))
            for v in (-30, -12, -1)})

# the amounts and levels of the pairs: every module audible, none at a fitted node
PAIR = {'Harm Amount': 0.7, 'Comp Amount': 0.55, 'Lift Amount': 0.65, 'EQ 100Hz': 3.3, 'EQ 3kHz': 4.1,
        'Par Sub Level': 0.6, 'Par Low Level': 0.6, 'Par Loud Level': 0.6, 'Par Grit Level': 0.6}


def random_settings(count=24, seed=2026):
    """count whole-plug-in settings drawn from a fixed seed: switches, amounts, EQ gains, parallels, in and out gain"""
    rng = np.random.default_rng(seed)
    out = {}
    for i in range(count):
        p = {name: int(rng.random() < 0.75) for name in o.MODULES.values()}
        p['Drive Hi-Pass'] = int(rng.integers(0, 2))
        p['Harm Freq'] = (50, 80)[int(rng.integers(0, 2))]
        for k in ('Harm Amount', 'Comp Amount', 'Lift Amount'): p[k] = round(float(rng.uniform(0, 1)), 3)
        for b in BANDS: p[f'EQ {b}'] = round(float(rng.uniform(0, 6)), 2)
        for k in o.PARALLELS:
            p[f'Par {k} On/Off'] = int(rng.random() < 0.5)
            p[f'Par {k} Level'] = round(float(rng.uniform(0, 1)), 3)
        p['Input Gain'] = round(float(rng.uniform(-6, 6)), 1)
        p['Output Gain'] = round(float(rng.uniform(-6, 6)), 1)
        out[f'random {i:02d}'] = dict(params=p)
    return out


def groups():
    """{group: {'case / signal': dict(sig=signal name, and the job's params / hidden / auto)}}; automation positions
    are samples at 48 kHz, rescaled per run"""
    def spread(settings, sigs):
        return {f'{name} / {s}': dict(sig=s, **job) for name, job in settings.items() for s in sigs}

    g = {}
    alone = {'drive, hi-pass on': dict(params=o.ONLY('drive', hipass=1)),
             'drive, hi-pass off': dict(params=o.ONLY('drive', hipass=0)),
             'drive colour b': dict(params=o.ONLY('drive', hipass=1), hidden={'drive.driveMode': 'b'}),
             'drive colour c': dict(params=o.ONLY('drive', hipass=1), hidden={'drive.driveMode': 'c'})}
    for key, name in (('harm', 'Harm Amount'), ('comp', 'Comp Amount'), ('lift', 'Lift Amount')):
        for a in AMOUNTS: alone[f'{key} {a:g}'] = dict(params={**o.ONLY(key), name: a})
    for mode in ('Mode A', 'Mode B'):
        alone[f'comp 0.55, {mode.lower()}'] = dict(params={**o.ONLY('comp'), 'Comp Amount': 0.55},
                                                    hidden={'ids.compression.mode': mode})
    g['module alone'] = spread(alone, ('drums', 'dynamic -4'))

    serial = list(o.MODULES)
    pairs = [(a, b) for i, a in enumerate(serial) for b in serial[i + 1:]]
    pairs += [('drive', 'sub'), ('comp', 'low'), ('lift', 'loud'), ('comp', 'grit'), ('harm', 'grit')]
    g['pairs'] = spread({f'{a} + {b}': dict(params={**PAIR, **o.ONLY(a, b, hipass=1)}) for a, b in pairs}, ('drums',))

    g['presets'] = spread(C.SETTINGS, ('drums', 'bass -6', 'wide -10'))

    eq = lambda *gains: {**o.ONLY('eq'), **{f'EQ {b}': v for b, v in zip(BANDS, gains) if v}}
    one = {f'eq {b} {v:g}': dict(params={**o.ONLY('eq'), f'EQ {b}': v}) for b in BANDS for v in (1.35, 4.7)}
    mixes = [(1.3, 2.7, 0.9, 4.4, 5.6), (5.1, 0, 3.3, 0, 1.7), (6, 6, 6, 6, 6)]
    g['eq'] = {**spread(one, ('drums',)),
               **spread({'eq ' + '/'.join(f'{v:g}' for v in m): dict(params=eq(*m)) for m in mixes},
                        ('drums', 'bright -8', 'bass -6')),
               **spread({'default chain, eq 2.2/3.8/1.1/4.9/2.6': dict(params={f'EQ {b}': v for b, v in
                                                                                 zip(BANDS, (2.2, 3.8, 1.1, 4.9, 2.6))})},
                        ('drums',))}

    par = lambda k, v: dict(params={**o.ONLY(k.lower()), f'Par {k} Level': v})
    g['parallels'] = {**spread({f'{k.lower()} {v:g}': par(k, v) for k in o.PARALLELS for v in PAR_LEVELS}, ('drums',)),
                      **spread({f'{k.lower()} {v:g}': par(k, v) for k in ('Sub', 'Low') for v in PAR_LEVELS}, ('bass -6',)),
                      **spread({'default chain, all four 0.4': dict(params={f'Par {k} Level': 0.4 for k in o.PARALLELS})},
                               ('drums', 'wide -10'))}

    steps = [f'drums peak {v}' for v in STEPS] + [f'{k} peak {v}' for k in ('bass', 'bright', 'wide') for v in (-30, -12, -1)]
    g['levels'] = spread({'default': {}}, steps + ['dynamic -4', 'sweep -6'])

    g['io gain'] = spread({f'input {i:+g} output {u:+g}': dict(params={'Input Gain': i, 'Output Gain': u})
                           for i, u in ((-12, 0), (-6, 3), (6, -6), (12, -12), (0, 12), (9.5, 0))}, ('drums -12',))

    g['random'] = spread(random_settings(), ('drums', 'wide -10'))

    g['automation'] = spread({f'{name}: {p} {v0:g} to {v1:g} and back':
                              dict(params=params, auto=[(p, A.PRE + A.T1, v1), (p, A.PRE + A.T2, v0)])
                              for name, (params, p, v0, v1) in A.cases().items()}, (AUTOM,))
    return g


RUNS = [('48 kHz, block 512', 48000, 512, None), ('44.1 kHz', 44100, 512, ['presets', 'levels']),
        ('96 kHz', 96000, 512, ['presets', 'levels']), ('block 64', 48000, 64, ['levels', 'automation']),
        ('block 2048', 48000, 2048, ['levels', 'automation'])]


def run(only=None, vst3=False):
    made = {}

    def signal(name, fs):
        if (name, fs) not in made:
            if (name, FS) not in made: made[name, FS] = np.asarray(SIG[name](), np.float32)
            made[name, fs] = at_rate(made[name, FS], fs)
        return made[name, fs]

    G = groups()
    res = {}
    for run_name, fs, block, which in RUNS:
        cases = [(gname, name, c) for gname, cs in G.items() for name, c in cs.items()
                 if (which is None or gname in which) and (only is None or only in gname or only in run_name)]
        if not cases: continue
        jobs = []
        for gname, name, c in cases:
            j = {k: v for k, v in c.items() if k != 'sig'}
            j['x'] = signal(c['sig'], fs)
            if j.get('auto'): j['auto'] = [(k, int(round(t * fs / FS)), v) for k, t, v in j['auto']]
            jobs.append(j)
        ref = o.render_many(jobs, 'ref', fs=fs, block=block, cache=True)
        ours = o.render_many(jobs, 'ours' if vst3 else 'model', fs=fs, block=block)
        print(f'== {run_name}', flush=True)
        for (gname, name, _), r, y in zip(cases, ref, ours):
            d = round(float(o.null_db(r, y, skip=int(o.SKIP * fs / FS))), 2)
            res[f'{run_name} | {gname} | {name}'] = d
            print(f'{d:8.2f} dB   [{gname}] {name}', flush=True)
    return res


def summary(res):
    """the median and the worst per group (over every run), and overall"""
    by = {}
    for key, v in res.items(): by.setdefault(key.split(' | ')[1], []).append(v)
    for gname, vals in by.items():
        print(f'{gname:14s} {len(vals):4d} cases: median {np.median(vals):7.1f} dB, worst {max(vals):7.1f} dB')
    vals = list(res.values())
    print(f'{"all":14s} {len(vals):4d} cases: median {np.median(vals):7.1f} dB, worst {max(vals):7.1f} dB')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Stress null tests of Scorpius against the reference.')
    ap.add_argument('--only', help='groups (or runs) whose name contains this text')
    ap.add_argument('--vst3', action='store_true', help='our built VST3 instead of our renderer')
    a = ap.parse_args()
    needs = [('RefRender', o.EXE), ('the VST3', o.PLUGINS['ours'][0])] if a.vst3 else [('the renderer', o.SCEXE)]
    missing = [what for what, path in needs if not os.path.exists(path)]
    if missing:
        print('not built: ' + ', '.join(missing) + ': nothing rendered')
        sys.exit(2)
    res = run(a.only, a.vst3)
    if not res:
        names = ', '.join(list(groups()) + [r[0] for r in RUNS])
        print(f'no group or run matches {a.only!r}: nothing rendered (groups and runs: {names})')
        sys.exit(1)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results_stress.json')
    old = json.load(open(out, encoding='utf-8')) if os.path.exists(out) and a.only else {}
    open(out, 'w', encoding='utf-8', newline='\n').write(json.dumps({**old, **res}, indent=1) + '\n')
    summary(res)
