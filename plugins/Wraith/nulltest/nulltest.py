"""Null tests: the same signals and settings through the reference (Cradle The Spirit) and through Wraith; the
residual (reference - ours) in dB re the reference's output. Both renders are latency-compensated by each plug-in's
reported latency (both report 0).

    python nulltest.py                 # every case, our processor via WrRender (fast)
    python nulltest.py --vst3          # our built VST3 through RefRender (the shipped binary)
    python nulltest.py --only preset   # cases whose name contains 'preset'
    python nulltest.py --report        # write NULLTESTS.md from results.json (never hand-edit that file)
    python nulltest.py --no-plate      # skip the plate presets whose capture is not cached yet (no real-time capture)
    python nulltest.py --out results_x.json   # the results under another name (a baseline beside the current run)
    python nulltest.py --tune renders/x.json  # our processor with a fit's constants (a tuning file, before shipping it)

Stages are isolated with the reference's own power buttons (ts.ONLY). Presets are rendered on the reference from its
own saved states (reference/Wraith/presets, read_presets.py) and on ours from the values those states hold. The
reference plays its plate only with its editor open, so the presets that use the plate are rendered on its side through
tools/RefCapture record=1 (null_plate.py), with mono signals; those captures are cached in renders/cache like the
offline renders (the capture is deterministic: two runs agree below -100 dB), so only the first run captures in real time.
"""
import argparse, json, os
import numpy as np
import ts as h
import nulltest_lib as nl

FS = h.FS
PRE = FS // 10                  # skipped: the first 0.1 s (renders start from silence on both sides)
SECS = 4
HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results.json')
REPORT = os.path.join(os.path.dirname(HERE), 'NULLTESTS.md')
REF = os.path.join(h.ROOT, 'reference', 'Wraith')

SIGNALS = {
    'pink -18': (lambda fs: nl.noise(SECS, -18.0, fs=fs, pink=True, seed=11), 'pink noise, -18 dBFS RMS'),
    'sweep -12': (lambda fs: nl.sweep(SECS, -12.0, fs=fs), 'log sine sweep 20 Hz - 20 kHz, -12 dBFS'),
    'drums -6': (lambda fs: nl.drums(SECS, -6.0, fs=fs), 'synthetic drum loop (kick, snare, hats), peaks -6 dBFS'),
    'music -10': (lambda fs: nl.music(SECS, -10.0, fs=fs), 'synthetic mix (bass, chords, noise bed, drums), peaks -10 dBFS'),
}

HOST = {'inputGain': 'Input Gain', 'outputGain': 'Output Gain', 'riderOn': 'Gain Rider State', 'riderAmount': 'Gain Rider Amount',
        'riderSpeed': 'Gain Rider Speed', 'riderFloor': 'Gain Rider Floor', 'compression': 'Compression', 'focus': 'Focus',
        'characterOn': 'Character State', 'eqOn': 'EQ State', 'eqLow': 'EQ Low Gain', 'eqHigh': 'EQ High Gain',
        'doublerOn': 'Doubler State', 'doublerMix': 'Doubler Mix', 'doublerStereo': 'Doubler Stereo', 'reverbOn': 'Reverb State',
        'reverbMix': 'Reverb Mix', 'reverbFilter': 'Reverb Filter', 'reverbType': 'Reverb Type'}


def stage(name, stages, **params):
    return (name, dict(norm=h.ONLY(*stages), params=params))


CASES = [
    stage('path: every stage off', ()),
    stage('gains: in -6, out +4', (), **{'Input Gain': -6, 'Output Gain': 4}),
    stage('eq: start-up values', ('EQ',)),
    stage('eq: low -7.5, high +9', ('EQ',), **{'EQ Low Gain': -7.5, 'EQ High Gain': 9}),
    stage('rider: start-up values', ('RIDER',)),
    stage('rider: amount 1, floor -50, speed 0.01', ('RIDER',), **{'Gain Rider Amount': 1.0, 'Gain Rider Floor': -50, 'Gain Rider Speed': 0.01}),
    stage('character: start-up (compression 0, focus +8)', ('CHAR',)),
    stage('character: compression +50, focus -30', ('CHAR',), **{'Compression': 50, 'Focus': -30}),
    stage('character: compression -50, focus +50', ('CHAR',), **{'Compression': -50, 'Focus': 50}),
    stage('doubler: mix 0.1, stereo 1', ('DBL',)),
    stage('doubler: mix 1, stereo 0.5', ('DBL',), **{'Doubler Mix': 1.0, 'Doubler Stereo': 0.5}),
    stage('reverb: room, start-up values', ('REV',)),
    stage('reverb: room, mix 1, filter 3.5 kHz', ('REV',), **{'Reverb Mix': 1.0, 'Reverb Filter': 3500}),
    ('full chain: start-up ("lead")', {}),
]
RATES = [(44100, '44.1 kHz'), (96000, '96 kHz')]


def preset_cases():
    ps = json.load(open(os.path.join(HERE, 'renders', 'presets.json')))
    out = []
    for name, v in ps.items():
        ours = {HOST[k]: v[k] for k in HOST if v.get(k) is not None and k != 'reverbType'}
        plate = v['reverbOn'] and v['reverbType'] > 0.5
        # Reverb Type is a choice: set it normalised (its display text is "room" / "plate")
        out.append((f'preset: {name}', dict(state=os.path.join(REF, v['state'])), dict(params=ours, norm={'Reverb Type': v['reverbType']}), plate))
    return out


def ours_job(x, settings):
    j = dict(x=x)
    if 'norm' in settings: j['norm'] = settings['norm']
    if 'params' in settings: j['params'] = settings['params']
    return j


def measure(ref, our):
    r = nl.residual_db(ref, our, PRE)
    w, sec = nl.worst_second(ref, our, PRE, fs=FS)
    return round(float(r), 2), round(float(w), 2), int(sec)


def plate_ref(mono, state, cache, no_plate):
    """the reference's plate preset render, from the cache when it holds it; None when it does not and no_plate"""
    import hashlib
    import null_plate
    k = hashlib.sha1(np.asarray(mono, np.float32).tobytes() + repr(('plate', os.path.basename(state), FS)).encode()).hexdigest()
    path = os.path.join(h.CACHE, 'plate_' + k + '.npy')
    if cache and os.path.exists(path): return np.load(path)
    if no_plate: return None
    y = null_plate.ref_plate(mono, FS, {}, state=state)
    if cache:
        os.makedirs(h.CACHE, exist_ok=True); np.save(path, y)
    return y


def run(vst3=False, only=None, cache=True, no_plate=False, tune=None):
    results = {}
    ours = 'ours' if vst3 else 'model'
    def our_render(jobs, **kw):          # a tuning file's constants on every job of our processor (--tune)
        return h.render_many([dict(j, tune=tune) if tune else j for j in jobs], ours, **kw)
    def keep(name, signal, ref, our, renderer):
        r, w, sec = measure(ref, our)
        results[f'{name} / {signal}'] = {'case': name, 'signal': signal, 'residual_db': r, 'worst_second_db': w,
                                         'worst_at_s': sec, 'renderer': renderer}
        print(f'{name + " / " + signal:62s} {r:7.1f} dB   worst second {w:7.1f} dB at {sec} s', flush=True)
    for sname, (make, _) in SIGNALS.items():
        x = nl.stereo(make(FS))
        for cname, settings in CASES:
            if only and only not in f'{cname} / {sname}': continue
            ref = h.render_many([dict(x=x, **settings)], 'ref', cache=cache)[0]
            our = our_render([ours_job(x, settings)])[0]
            keep(cname, sname, ref, our, ours)
        for fs, label in RATES:
            cname = f'full chain: start-up, {label}'
            if only and only not in f'{cname} / {sname}': continue
            xr = nl.stereo(make(fs))
            ref = h.render_many([dict(x=xr, settle=h.SETTLE.get(fs, 0))], 'ref', fs=fs, cache=cache)[0]
            our = our_render([dict(x=xr)], fs=fs)[0]
            keep(cname, sname, ref, our, ours)
    for cname, refset, oursettings, plate in preset_cases():
        for sname in ('pink -18', 'drums -6', 'music -10'):
            if only and only not in f'{cname} / {sname}': continue
            mono = np.asarray(SIGNALS[sname][0](FS), np.float32)
            mono = mono[0] if mono.ndim == 2 else mono
            x = nl.stereo(mono)
            if plate:
                ref = plate_ref(mono, refset['state'], cache, no_plate)
                if ref is None:
                    print(f'{cname + " / " + sname:62s} not measured (plate capture not cached; --no-plate)', flush=True)
                    continue
            else:
                ref = h.render_many([dict(x=x, **refset)], 'ref', cache=cache)[0]
            if plate:       # the capture plays plate_record.LEAD s of silence first (the plate loads): ours plays the
                            # same, so the doubler's modulation (0.503 Hz, not 0.5) is at the same phase when the signal
                            # starts
                import plate_record
                lead = int(plate_record.LEAD * FS)
                our = our_render([dict(x=nl.stereo(np.concatenate([np.zeros(lead, np.float32), mono])), **oursettings)])[0][:, lead:]
            else:
                our = our_render([dict(x=x, **oursettings)])[0]
            keep(cname, sname, ref, our, ours)
    return results


def report(results):
    sig_desc = '; '.join(f'**{k}**: {d}' for k, (_, d) in SIGNALS.items())
    rows = ['# Null tests', '',
            'The same signal and settings through the reference (Cradle The Spirit 1.0.3, VST3) and through Wraith.',
            'The residual is reference minus ours, in dB re the reference\'s output energy. Lower is better: -20 dB means the',
            'difference is a tenth of the signal\'s amplitude, -60 dB is inaudible in practice. Both plug-ins report no latency.',
            f'48 kHz unless the case says otherwise, block 512, the first {PRE / FS:.1f} s skipped. Stages are isolated with the',
            'reference\'s own power buttons. Presets are loaded on the reference from its own saved states.', '',
            'Reproduce: `python nulltest/nulltest.py` (our processor through tools/WrRender) and',
            '`python nulltest/nulltest.py --vst3` (the built VST3 through tools/RefRender). The reference renders stay local.', '',
            '| Case | Signal | Residual (dB) | Worst second (dB) |', '|---|---|---|---|']
    for r in results.values():
        rows.append(f"| {r['case']} | {r['signal']} | {r['residual_db']:.1f} | {r['worst_second_db']:.1f} |")
    vals = [r['residual_db'] for r in results.values()]
    worst = max(results, key=lambda k: results[k]['residual_db'])
    rows += ['', f'Signals: {sig_desc}.', '',
             f'Median {np.median(vals):.1f} dB over {len(vals)} cases; worst {max(vals):.1f} dB ({worst}).', '']
    by = {}
    for r in results.values():
        by.setdefault(r['case'].split(':')[0], []).append(r['residual_db'])
    rows += ['| Part | Cases | Median (dB) | Best (dB) | Worst (dB) |', '|---|---|---|---|---|']
    for part, v in by.items():
        rows.append(f'| {part} | {len(v)} | {np.median(v):.1f} | {min(v):.1f} | {max(v):.1f} |')
    notes = open(os.path.join(HERE, 'nulltests_notes.md'), encoding='utf-8').read().strip()
    if '{doubler_metric}' in notes:             # the behaviour table, from doubler_metric.py's results
        dm = json.load(open(os.path.join(HERE, 'renders', 'doubler_metric.json')))
        t = ['  | Signal, setting | Spectrum error, rms (dB, third octaves) | Spectrum error, worst (dB) | L / R correlation, original | ours | Level, ours less original (dB) |',
             '  |---|---|---|---|---|---|']
        t += [f"  | {k} | {v['spectrum_rms_db']:.2f} | {v['spectrum_max_db']:.2f} | {v['corr_ref']:.3f} | {v['corr_ours']:.3f} | {v['level_diff_db']:.2f} |" for k, v in dm.items()]
        notes = notes.replace('{doubler_metric}', chr(10).join(t))
    rows += ['', '## What the numbers say', '', notes, '']
    open(REPORT, 'w', encoding='utf-8', newline='\n').write('\n'.join(rows))
    print('wrote', REPORT)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--vst3', action='store_true')
    ap.add_argument('--only', default=None)
    ap.add_argument('--report', action='store_true', help='write NULLTESTS.md from results.json without rendering')
    ap.add_argument('--no-cache', action='store_true')
    ap.add_argument('--no-plate', action='store_true', help='skip plate presets that need a real-time capture')
    ap.add_argument('--tune', default=None, help='a tuning file (JSON, constants by name) for our processor')
    ap.add_argument('--out', default=None, help='results file name in nulltest/ (default results.json / results_vst3.json)')
    a = ap.parse_args()
    if a.report:
        report(json.load(open(RESULTS)))
    else:
        res = run(a.vst3, a.only, not a.no_cache, a.no_plate, json.load(open(a.tune)) if a.tune else None)
        out = os.path.join(HERE, a.out) if a.out else RESULTS if not a.vst3 else RESULTS.replace('.json', '_vst3.json')
        if a.only and os.path.exists(out):       # a partial run updates its cases in the full results
            res = dict(json.load(open(out)), **res)
        json.dump(res, open(out, 'w'), indent=1)
        nl.summarize({k: v['residual_db'] for k, v in res.items()})
