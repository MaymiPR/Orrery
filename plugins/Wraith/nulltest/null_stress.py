"""Stress null tests: the reference against our processor over a wide grid of settings, levels, signals, sample rates,
block sizes and parameter automation, beyond the fixed cases of nulltest.py. Every stage alone at three settings, the
stages in pairs, the factory presets that play the room or no reverb, the full chain at input levels from -30 to
-1 dBFS, a seeded grid of random settings and automation of the gains and the EQ gains. The settings are taken off the
fitted nodes on purpose (odd values), so interpolation is tested too. The plate is left out: the reference plays it
only with its editor open (null_plate.py).

    python null_stress.py                    # every group
    python null_stress.py --only alone       # groups (or runs) whose name contains 'alone'
    python null_stress.py --vst3             # our built VST3 instead of WrRender
Writes nulltest/results_stress.json: "run | group | case / signal" to the residual in dB. With --only the cases of
the run are merged into the file that is there."""
import argparse, json, os, sys
import numpy as np
import wr_ref as h
import nulltest as N
import nulltest_lib as nl

FS = h.FS
HERE = os.path.dirname(os.path.abspath(__file__))


def at_peak(x, db):
    x = np.asarray(x, np.float64)
    return (x * 10 ** (db / 20) / np.max(np.abs(x))).astype(np.float32)


def sig_bass(fs, db=-6.0):
    """bass-heavy: a sub line with slides and a kick"""
    t = np.arange(int(N.SECS * fs)) / fs
    f = 40 + 25 * (np.sin(2 * np.pi * 0.4 * t) > 0) + 10 * np.sin(2 * np.pi * 0.13 * t)
    return at_peak(np.sin(2 * np.pi * np.cumsum(f) / fs) * 0.7 + nl.drums(N.SECS, -6.0, seed=9, fs=fs) * 0.6, db)


def sig_bright(fs, db=-8.0, seed=21):
    """treble-heavy: dense hats, sibilant noise bursts and a tone cluster from 6 to 12 kHz"""
    rng = np.random.default_rng(seed)
    n = int(N.SECS * fs); t = np.arange(n) / fs
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) for f in (6100, 7900, 9300, 11800)) * 0.15
    hp = np.diff(rng.standard_normal(n + 1))
    env = (np.sin(2 * np.pi * 2.5 * t) > 0.6) * 1.0
    return at_peak(x + hp * env * 0.4 + np.diff(nl.drums(N.SECS, -6.0, seed=4, fs=fs), prepend=0) * 2, db)


def sig_wide(fs, db=-10.0):
    """the music mix with extreme stereo: the right channel partly inverted, plus a left-only lead"""
    m = nl.music(N.SECS, db, seed=8, fs=fs)
    t = np.arange(m.shape[1]) / fs
    lead = 0.25 * np.sin(2 * np.pi * 880 * t) * (np.sin(2 * np.pi * 0.5 * t) > 0)
    return np.stack([m[0] + lead * 10 ** (db / 20), -0.7 * m[1] + 0.3 * m[0]]).astype(np.float32)


def sig_dynamic(fs, db=-4.0):
    """quiet and loud passages: the mix at -30, -10 and the given level, a third of the time each (detector settling)"""
    m = nl.music(N.SECS, 0.0, seed=12, fs=fs)
    n = m.shape[1] // 3
    g = np.concatenate([np.full(n, -30.0), np.full(n, -10.0), np.full(m.shape[1] - 2 * n, db)])
    return (m * 10 ** (g / 20)).astype(np.float32)


def sig_voice(fs, db=-8.0, seed=31):
    """voice-like, mono: a harmonic tone near 150 Hz with a glide and a 5.5 Hz vibrato, its harmonics weighted by three
    formants, sung in syllables with a breath between phrases, and noise bursts (sibilants) between the syllables"""
    rng = np.random.default_rng(seed)
    n = int(N.SECS * fs); t = np.arange(n) / fs
    f0 = 150 * 2 ** (np.sin(2 * np.pi * 0.31 * t) * 3 / 12) * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t))
    ph = 2 * np.pi * np.cumsum(f0) / fs
    tone = np.zeros(n)
    for k in range(1, 41):                          # up to 7.3 kHz: below half of every rate tested
        f = k * f0
        w = 0.03 + sum(a * np.exp(-0.5 * ((f - c) / bw) ** 2) for c, bw, a in ((650, 180, 1.0), (1150, 220, 0.6), (2700, 350, 0.35)))
        tone += np.sin(k * ph) * w / k
    syl = np.sin(2 * np.pi * 2.6 * t)
    phrase = np.clip(np.sin(2 * np.pi * 0.4 * t) * 4 + 3, 0, 1)
    voiced = np.clip(syl * 3, 0, 1) * phrase
    burst = np.clip(-syl * 3 - 2, 0, 1) * phrase
    hiss = np.diff(rng.standard_normal(n + 1))
    return at_peak(tone / np.max(np.abs(tone)) * voiced + 0.25 * hiss / np.max(np.abs(hiss)) * burst, db)


SIG = {name: make for name, (make, _) in N.SIGNALS.items()}          # pink -18, sweep -12, drums -6, music -10
SIG.update({
    'music -30': lambda fs: nl.music(N.SECS, -30.0, fs=fs), 'music -20': lambda fs: nl.music(N.SECS, -20.0, fs=fs),
    'music -6': lambda fs: nl.music(N.SECS, -6.0, fs=fs), 'music -1': lambda fs: nl.music(N.SECS, -1.0, fs=fs),
    'drums -18': lambda fs: nl.drums(N.SECS, -18.0, fs=fs), 'drums -1': lambda fs: nl.drums(N.SECS, -1.0, fs=fs),
    'voice -30': lambda fs: sig_voice(fs, -30.0), 'voice -18': lambda fs: sig_voice(fs, -18.0),
    'voice -8': lambda fs: sig_voice(fs, -8.0), 'voice -1': lambda fs: sig_voice(fs, -1.0),
    'bass -6': lambda fs: sig_bass(fs, -6.0), 'bright -8': lambda fs: sig_bright(fs, -8.0),
    'wide -10': lambda fs: sig_wide(fs, -10.0), 'dynamic -4': lambda fs: sig_dynamic(fs, -4.0),
})

SHORT = {'Gain Rider Amount': 'amount', 'Gain Rider Floor': 'floor', 'Gain Rider Speed': 'speed', 'Compression': 'compression',
         'Focus': 'focus', 'EQ Low Gain': 'low', 'EQ High Gain': 'high', 'Doubler Mix': 'mix', 'Doubler Stereo': 'stereo',
         'Reverb Mix': 'mix', 'Reverb Filter': 'filter', 'Input Gain': 'in', 'Output Gain': 'out'}

# Three settings per stage, off the fitted nodes; the first of each is the one the pairs use.
STAGES = {
    'RIDER': ('rider', ('voice -8', 'dynamic -4'), [
        {'Gain Rider Amount': 0.35, 'Gain Rider Floor': -41.5, 'Gain Rider Speed': 0.002},
        {'Gain Rider Amount': 0.85, 'Gain Rider Floor': -23.5, 'Gain Rider Speed': 0.007},
        {'Gain Rider Amount': 0.55, 'Gain Rider Floor': -33.5, 'Gain Rider Speed': 0.005}]),
    'CHAR': ('character', ('voice -8', 'music -10'), [
        {'Compression': 17, 'Focus': -13}, {'Compression': -33, 'Focus': 27}, {'Compression': 38, 'Focus': 41}]),
    'EQ': ('eq', ('voice -8', 'music -10'), [
        {'EQ Low Gain': 3.3, 'EQ High Gain': -4.7}, {'EQ Low Gain': -10.5, 'EQ High Gain': 7.9},
        {'EQ Low Gain': 11.1, 'EQ High Gain': 11.7}]),
    'DBL': ('doubler', ('voice -8', 'music -10'), [
        {'Doubler Mix': 0.25, 'Doubler Stereo': 0.8}, {'Doubler Mix': 0.55, 'Doubler Stereo': 0.15},
        {'Doubler Mix': 0.85, 'Doubler Stereo': 1.0}]),
    'REV': ('reverb', ('voice -8', 'music -10'), [
        {'Reverb Mix': 0.25, 'Reverb Filter': 12500}, {'Reverb Mix': 0.6, 'Reverb Filter': 5200},
        {'Reverb Mix': 0.9, 'Reverb Filter': 2700}]),
}


def label(params):
    return ', '.join(f'{SHORT[k]} {v:g}' for k, v in params.items())


def random_settings(count=24, seed=2026):
    """(name, settings) of the random grid: every continuous parameter anywhere in its range (the gains within 6 dB),
    each stage on with a probability of 0.7. The draw is the same on every run."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(count):
        u = lambda lo, hi, step: float(round(round(rng.uniform(lo, hi) / step) * step, 3))
        on = [key for key in h.STATES if rng.random() < 0.7]
        params = {'Input Gain': u(-6, 6, 0.1), 'Output Gain': u(-6, 6, 0.1), 'Gain Rider Amount': u(0, 1, 0.005),
                  'Gain Rider Floor': u(-50, -18, 0.1), 'Gain Rider Speed': u(0.001, 0.01, 0.001),
                  'Compression': int(rng.integers(-50, 51)), 'Focus': int(rng.integers(-50, 51)),
                  'EQ Low Gain': u(-12, 12, 0.1), 'EQ High Gain': u(-12, 12, 0.1), 'Doubler Mix': u(0, 1, 0.005),
                  'Doubler Stereo': u(0, 1, 0.005), 'Reverb Mix': u(0, 1, 0.005), 'Reverb Filter': int(u(2000, 20000, 10))}
        out.append((f'random {i:02d} ({"+".join(on) or "none"})', dict(norm=h.ONLY(*on), params=params)))
    return out


def presets():
    """(name, the reference's settings, ours) of the factory presets without the plate whose saved state is here"""
    try:
        cases = N.preset_cases()
    except FileNotFoundError:
        print('presets: nulltest/renders/presets.json is not here (read_presets.py writes it): group left out', flush=True)
        return []
    out = []
    for name, refset, ourset, plate in cases:
        if plate: continue
        if not os.path.exists(refset['state']):
            print(f'{name}: its saved state is not here: left out', flush=True)
            continue
        out.append((name, refset, ourset))
    return out


def groups():
    """[(group, [(case name, signal, the reference's settings, ours, auto)])]; auto positions in samples at FS"""
    g = []
    both = lambda name, sig, settings, auto=None: (name, sig, settings, settings, auto)
    for key, (stage, sigs, sets) in STAGES.items():
        g.append((f'alone {stage}', [both(f'{stage} alone: {label(p)}', s, dict(norm=h.ONLY(key), params=p))
                                     for p in sets for s in sigs]))
    keys = list(STAGES)
    g.append(('pairs', [both(f'{STAGES[a][0]} + {STAGES[b][0]}', s, dict(norm=h.ONLY(a, b), params={**STAGES[a][2][0], **STAGES[b][2][0]}))
                        for i, a in enumerate(keys) for b in keys[i + 1:] for s in ('voice -8', 'drums -6')]))
    g.append(('io gain', [both(f'gains only: {label(p)}', 'music -10', dict(norm=h.NONE, params=p))
                          for p in ({'Input Gain': -12, 'Output Gain': 0}, {'Input Gain': -4.5, 'Output Gain': 7.5},
                                    {'Input Gain': 9.3, 'Output Gain': -9.3}, {'Input Gain': 12, 'Output Gain': -12})]))
    g.append(('presets', [(name, s, refset, ourset, None) for name, refset, ourset in presets() for s in ('voice -8', 'music -10')]))
    g.append(('levels', [both('full chain: start-up', s, {})
                         for s in ('music -30', 'music -20', 'music -10', 'music -6', 'music -1', 'voice -30', 'voice -18',
                                   'voice -8', 'voice -1', 'drums -18', 'drums -1', 'bass -6', 'bright -8', 'wide -10',
                                   'dynamic -4', 'sweep -12')]))
    g.append(('random', [both(name, s, settings) for name, settings in random_settings() for s in ('voice -8', 'drums -6')]))
    s = lambda sec: int(sec * FS)
    ramp = lambda name, a, b: [(name, s(0.5 + i * 0.05), round(a + (b - a) * i / 40, 4)) for i in range(41)]
    moves = [('Input Gain', s(0.8), 0.7), ('EQ High Gain', s(1.4), 0.9), ('EQ Low Gain', s(2.0), 0.2), ('Output Gain', s(2.6), 0.35),
             ('EQ High Gain', s(3.0), 0.4), ('Input Gain', s(3.4), 0.5)]
    g.append(('automation', [
        both('input gain jumps +6/-6/0, gains only', 'music -10', dict(norm=h.NONE),
             [('Input Gain', s(1), 0.75), ('Input Gain', s(2), 0.25), ('Input Gain', s(3), 0.5)]),
        both('output gain jumps -6/+9, gains only', 'drums -6', dict(norm=h.NONE),
             [('Output Gain', s(1), 0.25), ('Output Gain', s(2.5), 0.875)]),
        both('input gain ramp -12 to +12 in 41 steps, gains only', 'pink -18', dict(norm=h.NONE, params={'Input Gain': -12}),
             ramp('Input Gain', 0.0, 1.0)),
        both('eq high jumps +12/-12/0, eq only', 'music -10', dict(norm=h.ONLY('EQ')),
             [('EQ High Gain', s(1), 1.0), ('EQ High Gain', s(2), 0.0), ('EQ High Gain', s(3), 0.5)]),
        both('eq low jumps -12/+12/0, eq only', 'pink -18', dict(norm=h.ONLY('EQ')),
             [('EQ Low Gain', s(1), 0.0), ('EQ Low Gain', s(2), 1.0), ('EQ Low Gain', s(3), 0.5)]),
        both('eq low up and high down in 41 steps, eq only', 'music -10', dict(norm=h.ONLY('EQ'), params={'EQ Low Gain': 0, 'EQ High Gain': 0}),
             sorted(ramp('EQ Low Gain', 0.5, 1.0) + ramp('EQ High Gain', 0.5, 0.0), key=lambda e: e[1])),
        both('gain and eq moves, eq + reverb', 'voice -8', dict(norm=h.ONLY('EQ', 'REV')), moves),
        both('gain and eq moves, full chain: start-up', 'voice -8', {}, moves),
    ]))
    return g


RUNS = [('48 kHz, block 512', 48000, 512, None), ('44.1 kHz', 44100, 512, ['levels', 'pairs']),
        ('96 kHz', 96000, 512, ['levels', 'pairs']), ('block 64', 48000, 64, ['levels', 'automation']),
        ('block 2048', 48000, 2048, ['levels', 'automation'])]


def run(only=None, vst3=False):
    made = {}
    def sig(name, fs):
        if (name, fs) not in made: made[name, fs] = nl.stereo(SIG[name](fs))
        return made[name, fs]
    all_groups = groups()
    res = {}
    for run_name, fs, block, which in RUNS:
        cases = [(gname, c) for gname, cs in all_groups for c in cs
                 if (which is None or gname in which) and (only is None or only in gname or only in run_name)]
        if not cases: continue
        ref_jobs, our_jobs = [], []
        for gname, (name, s, refset, ourset, auto) in cases:
            r, o = dict(x=sig(s, fs), **refset), dict(x=sig(s, fs), **ourset)
            if fs in h.SETTLE: r['settle'] = h.SETTLE[fs]          # the reference loads its reverb late at this rate
            if auto:              # positions follow the rate and fall on a block boundary, as the harness wants them
                r['auto'] = o['auto'] = [(k, int(round(t * fs / FS)) // block * block, v) for k, t, v in auto]
            ref_jobs.append(r); our_jobs.append(o)
        ref = h.render_many(ref_jobs, 'ref', fs=fs, block=block, cache=True)
        ours = h.render_many(our_jobs, 'ours' if vst3 else 'model', fs=fs, block=block)
        print(f'== {run_name}', flush=True)
        pre = N.PRE * fs // FS
        for (gname, (name, s, *_)), r, o in zip(cases, ref, ours):
            d = round(float(nl.residual_db(r, o, pre)), 2)
            res[f'{run_name} | {gname} | {name} / {s}'] = d
            print(f'{d:8.2f} dB   [{gname}] {name} / {s}', flush=True)
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--only'); ap.add_argument('--vst3', action='store_true')
    a = ap.parse_args()
    res = run(a.only, a.vst3)
    if not res:
        print(f'no group or run matches {a.only!r}: nothing rendered' if a.only else 'no case: nothing rendered')
        sys.exit(2)
    out = os.path.join(HERE, 'results_stress.json')
    old = json.load(open(out)) if os.path.exists(out) and a.only else {}
    json.dump({**old, **res}, open(out, 'w'), indent=1)
    by = {}
    for k, v in res.items():
        by.setdefault(k.split(' | ')[1], []).append(v)
    print()
    for gname, v in by.items():
        print(f'{gname:18s} {len(v):4d} cases: median {np.median(v):7.1f} dB, worst {max(v):7.1f} dB')
    vals = list(res.values())
    print(f'{len(vals)} cases: median {np.median(vals):.1f} dB, worst {max(vals):.1f} dB ({max(res, key=res.get)})')
