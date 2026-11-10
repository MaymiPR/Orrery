"""Null tests of Scorpius: every case NULLTESTS.md publishes, and the report itself.

    python nulltest.py [model|ours]    # render every case (the reference from its cache); writes results.json
                                       # (model: our processor through tools/ScRender, the default; ours: the built
                                       # VST3, written to results_vst3.json)
    python nulltest.py --report        # write NULLTESTS.md from results.json (never hand-edit that file)

The cases: the factory presets and a few settings on the drum-like signal and the local track at every rate
(null_chain.py's table), quiet material where the shared expander acts (null_quiet.py) and the EQ and compression
modules alone (null_modules.py). The automation, the learned blocks' held-out results and the CPU figures come from
probe_autom.py, the training scripts and a timing run; NOTES carries them.
"""
import json, math, os, sys
import numpy as np
import scipy.signal as sg
import sc_ref as o
import null_chain as C
import null_modules as N

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results.json')
REPORT = os.path.join(os.path.dirname(HERE), 'NULLTESTS.md')
EXACT = -150.0          # below this the two outputs are the same samples: printed as "exact"

# the presets table: (row, null_chain.SETTINGS name or settings, sample rate)
PRESET_ROWS = [(name, name, 48000) for name in C.SETTINGS if name != 'all off'] + [
    ('all off, 48 kHz', 'all off', 48000),
    ('default with the drive off (the rest of the chain)', dict(params={'Drive On/Off': 0}), 48000)]
PRESET_ROWS += [(f'all off, {fs / 1000:g} kHz', 'all off', fs) for fs in (44100, 88200, 96000, 176400, 192000)]
PRESET_ROWS += [(f'default, {fs / 1000:g} kHz', 'default', fs) for fs in (88200, 96000, 176400, 192000)]
ROW_TITLES = {'colour c': 'colour c (drive colour c, compression mode a)'}
QUIET_TITLES = {'track -60': 'track at -60 dBFS', 'track -66': 'track at -66 dBFS', 'drums -62': 'drums at -62 dBFS',
                'drums -70': 'drums at -70 dBFS', 'pink -72': 'pink noise at -72 dBFS RMS', 'pink -78': 'pink noise at -78 dBFS RMS'}


def at_rate(x, fs):
    if fs == 48000:
        return x
    g = math.gcd(fs, 48000)
    return sg.resample_poly(x, fs // g, 48000 // g, axis=-1).astype(np.float32)


def nulls(jobs, plugin, fs=48000):
    ref = o.render_many(jobs, fs=fs, cache=True)
    ours = o.render_many(jobs, plugin=plugin, fs=fs)
    return [round(float(o.null_db(r, m)), 2) for r, m in zip(ref, ours)]


def run(plugin):
    sig = N.signals()
    res = {'presets': {}, 'presets_44k': {}, 'quiet': {}, 'modules': {}}
    for row, spec, fs in PRESET_ROWS:
        s = C.SETTINGS[spec] if isinstance(spec, str) else spec
        res['presets'][row] = dict(zip(sig, nulls([dict(x=at_rate(x, fs), **s) for x in sig.values()], plugin, fs)))
        print(f'{row:50s}', '  '.join(f'{v:7.1f}' for v in res['presets'][row].values()), flush=True)
    for name, s in C.SETTINGS.items():           # the rows at 44.1 kHz, for the sentence above the table
        res['presets_44k'][name] = dict(zip(sig, nulls([dict(x=at_rate(x, 44100), **s) for x in sig.values()], plugin, 44100)))
    X = {'track -60': sig['track'] * 10 ** (-60 / 20), 'track -66': sig['track'] * 10 ** (-66 / 20),
         'drums -62': sig['drums'] * 10 ** (-62 / 20), 'drums -70': sig['drums'] * 10 ** (-70 / 20),
         'pink -72': o.noise(6.0, -72, seed=5, pink=True), 'pink -78': o.noise(6.0, -78, seed=5, pink=True)}
    for name, spec in (('default', {}), ('drive alone', dict(params=o.ONLY('drive', hipass=1)))):
        res['quiet'][name] = dict(zip(X, nulls([dict(x=x, **spec) for x in X.values()], plugin)))
        print(f'quiet {name:12s}', '  '.join(f'{v:7.1f}' for v in res['quiet'][name].values()), flush=True)
    for name, spec in N.CASES.items():
        res['modules'][name] = dict(zip(sig, nulls([dict(x=x, **spec) for x in sig.values()], plugin)))
        print(f'module {name:12s}', '  '.join(f'{v:7.1f}' for v in res['modules'][name].values()), flush=True)
    return res


def cell(v):
    return 'exact' if v < EXACT else f'{v:.1f}'


def span(vals, digits=0):
    """the worst to the best of a group, as the tables print it: -55 … -67"""
    vals = list(vals)
    return f'{max(vals):.{digits}f} … {min(vals):.{digits}f}'


HEADER = """# Null tests

The same signal and settings through the reference (Cradle Orion, VST3) and through Scorpius. The residual is
reference minus ours, in dB re the reference's output energy. Lower is better: -20 dB means the difference is a tenth
of the signal's amplitude, -60 dB is inaudible in practice. Both renders are compensated by each plug-in's reported
latency, block 512; the first 0.1 s is skipped (the reference ramps its settings in over the first ~5 ms). Settings
are applied 400 ms before each render (the reference applies them asynchronously; MEASUREMENTS.md).

Signals: **drums**, a synthetic drum loop (`nulltest/probe_order.py`), peaks near full scale, and the same 12 dB lower;
**track**, 6 s of a mastered track (local only, not in the repository), and the same 10 dB lower.

Reproduce: `python nulltest/nulltest.py` (our processor through tools/ScRender) or `python nulltest/nulltest.py ours`
(the built VST3; the same numbers), then `python nulltest/nulltest.py --report`. The reference renders stay local
(git-ignored)."""

QUIET_TEXT = """## Quiet material

Where the shared expander acts (below about -58 dBFS peak; MEASUREMENTS.md 3): the same signals far lower, and pink
noise. The expander reads the end of the group and its mid, starts open when created with lift on, and lift gives no
DC on silence:"""

# The module rows that come from cases of their own (null_modules.py's sub, harmonics, loud, lift, drive, grit and low
# runs), the learned blocks, the automation table (probe_autom.py), the conclusions and the CPU figures.
MODULE_ROWS = """| sub | -65 … -72 |
| harmonics (learned), amount 1 / 0.8 / 0.6 / 0.3 | -50 … -65 / -55 … -71 / -59 … -67 / -66 … -67 |
{compression}
| loud, level 1 | -31 … -39 |
| lift (learned) | -43.5 … -51.5 |
| drive colour a, hi-pass on (learned, the default) | -25.9 … -35.6 |
| drive colour a, hi-pass off (learned) | -25.9 … -36.3 |
| grit (learned), level 1 / 0.731 | -27 … -31 / -33 … -37 |
| low, tones and chords | -38 … -46 |
| low, music | about 0 (the octave's polarity slips against the reference's) |"""

GRIT = """\
The preset "grit only" on the same quiet signals nulls at -62 … -65 dB (-36 dB on the track at -60), because its
models leave no DC on silence (-45 … -58 with models that do)."""

NOTES = """\
The learned drive models on held-out pieces of their training material (up to +4 dBFS peak), mean (loudest piece):
colour a -31.6 (-24.5) / -31.9 (-24.4) dB (hi-pass on / off: a recurrent network of 3 layers of 24, with the hi-pass
a fixed filter after it, against WaveNets at -29.7 (-21.8) / -28.3 (-20.5)), colour b -34.7 (-25.6) / -34.9
(-25.5) (the same kind of network, with the filter for the hi-pass, against WaveNets at -32.1 (-23.6) / -33.6
(-23.7)), colour c -34.6
(-25.5) / -36.3 (-25.6). The plug-in runs the recurrent networks as trained: through the plug-in, colour a's capture
pieces null at -31.9 dB on average (with exact activations the same), where a sigmoid clamped at 0.99995 left -30.3 and
the quieter pieces up to 4.5 dB worse (MEASUREMENTS.md 14). A second, finer training pass of colour a's network:
-32.7 / -32.3 dB through the plug-in, hi-pass off / on, and a third: -33.1 / -32.7. Colour b's network,
a second pass the same way: -35.4 (-26.1) held out, hi-pass off.

## Automation

A parameter jumps at 1 s and back at 2 s on the drums at -12 dB, one module on (`python nulltest/probe_autom.py`):
the null in the 0.15 s around each jump, at host blocks of 512 / 64 samples. Each cell reads without → with the
reference's control rate (chunked amount smoothing, switches at the block start; MEASUREMENTS.md 12), modules switched
on starting from silence with the expander closed (MEASUREMENTS.md 3, 12) and the expander reading the end of the group
and its mid. For comparison the same setting held still nulls at the "steady" value.

| Change | Around the jumps, block 512 (dB) | Block 64 (dB) | Steady |
|---|---|---|---|
| compression amount 0.2 ↔ 0.9 | -41.7 / -40.1 → -60.4 / -60.5 | -46.6 / -42.1 → -60.5 / -59.3 | -61.4 |
| lift amount 0.2 ↔ 0.9 | -43.3 / -37.4 → -48.9 / -57.7 | -44.8 / -41.5 → -48.9 / -55.3 | -51.7 |
| harmonics amount 0.2 ↔ 0.9 | -23.5 / -19.7 → -33.6 / -31.5 | -22.9 / -25.4 → -29.4 / -28.9 | -68.5 |
| compression off / on | -28.6 / -22.2 → -70.4 / -59.3 | -28.5 / -28.7 → -70.0 / -57.6 | |
| lift off / on | -28.7 / -19.8 → -61.3 / -53.9 | -29.3 / -26.0 → -61.3 / -52.7 | |
| harmonics off / on | -22.8 / -27.4 → -78.4 / -69.0 | -25.5 / -29.3 → -78.2 / -70.1 | |
| EQ off / on | -23.6 / -29.6 → -54.0 / -53.7 | -27.3 / -25.7 → -54.0 / -54.6 | |
| drive off / on | -18.6 / -8.3 → -43.0 / -30.8 | -16.1 / -8.2 → -42.2 / -28.2 | |
| EQ 1 kHz 0.6 ↔ 4.8 dB | -43.8 / -43.1 (unchanged) | -42.9 / -49.9 | -52.7 |

## What the numbers say

- **The fixed parts are close to exact** (EQ, sub, the rate converters: -50 to -70 dB): these are the reference's own
  filters, identified from its responses.
- **Everything but the drive** nulls at -44 … -51 dB together (the default preset with the drive off): the
  compressor applies its gain before its filters (as the reference), lift and harmonics are learned (harmonics at
  four amounts, interpolated).
- **The whole plug-in is limited by the drive**, which the reference runs as a learned model of its own and which
  Scorpius learns from the reference's input and output: on loud program material the default preset nulls at about
  -22 to -27 dB, 10 … 12 dB lower at -32 to -37 dB. Loud, dense material is the hard part: a linear filter explains
  only 3 dB of the drive's output there, and even a model trained on one loud piece alone reaches only -21 (8
  channels) to -26 dB (16) on it.
- **Above 48 kHz** (88.2, 96, 176.4, 192 kHz) Scorpius runs the reference's own converters, identified from its
  impulse responses (-73 … -110 dB with everything off); the presets null as at 48 kHz.
- **Grit** is learned too (a transient shaper of the mids, each channel by itself), 5 … 9 dB better than a
  hand-made transient shaper; after the compressor on stereo material the reference's grit still differs a little.
- **Low** matches on tones and chords; on music its octave keeps the right shape and level but its polarity drifts
  against the reference's (which crossings its flip-flop counts is not pinned down).

## CPU

60 s of the drum loop, stereo, 48 kHz, one instance, offline, the two plug-ins in the same run: the default preset
takes 10.6 … 10.8 s of CPU against the reference's 9.1 s (drive alone 4.6 s against 5.7, lift 3.3 against 2.3,
compression 0.5 against 2.1, grit 2.8 against 4.1). The learned parts run in 8-wide vector registers where the
processor has AVX."""


def report(res):
    sigs = list(next(iter(res['presets'].values())))
    within = max(abs(res['presets_44k'][n][s] - res['presets'][n][s])
                 for n in res['presets_44k'] if n != 'all off' for s in sigs)
    rows = [HEADER, '', '## The whole plug-in: the factory presets', '',
            f'48 kHz (44.1 kHz within {within:.1f} dB of these, except "all off"):', '',
            '| Preset | ' + ' | '.join(sigs) + ' |', '|---' * (len(sigs) + 1) + '|']
    for row, _, _ in PRESET_ROWS:
        rows.append(f'| {ROW_TITLES.get(row, row)} | ' + ' | '.join(cell(res['presets'][row][s]) for s in sigs) + ' |')
    q = res['quiet']
    rows += ['', QUIET_TEXT, '', '| Signal | default | drive colour a alone (hi-pass on) |', '|---|---|---|']
    for k, title in QUIET_TITLES.items():
        rows.append(f"| {title} | {q['default'][k]:.1f} | {q['drive alone'][k]:.1f} |")
    rows += ['', GRIT]
    m = res['modules']
    one = [v for n in ('eq 1k 6', 'eq 40 6', 'eq 100 6', 'eq 3k 6', 'eq 10k 6') for v in m[n].values()]
    comp = (f"| compression, mode b / a (the gain corrected by a learned model) | {span(m['comp b'].values(), 1)} / "
            f"{span(m['comp a'].values(), 1)} |")
    rows += ['', '## Module by module', '',
             "Each module alone (the others off with the reference's own power buttons), on the same four signals:", '',
             '| Module | Residual (dB) |', '|---|---|',
             f'| EQ, one band at +6 dB | {span(one)} |', f"| EQ, all bands at +4 dB | {span(m['eq all 4'].values())} |",
             MODULE_ROWS.format(compression=comp), '', NOTES, '']
    open(REPORT, 'w', encoding='utf-8', newline='\n').write('\n'.join(rows))
    print('wrote', REPORT)


def main():
    a = sys.argv[1:]
    if a[:1] == ['--report']:
        report(json.load(open(RESULTS)))
        return
    plugin = a[0] if a else 'model'
    if plugin not in ('model', 'ours'):
        sys.exit(__doc__)
    res = run(plugin)
    out = RESULTS if plugin == 'model' else RESULTS.replace('.json', '_vst3.json')
    json.dump(res, open(out, 'w'), indent=1)
    print('wrote', out)


if __name__ == '__main__':
    main()
