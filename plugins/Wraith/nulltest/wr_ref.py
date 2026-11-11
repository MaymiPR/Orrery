"""Measurement / null-test harness for Wraith: renders numpy signals through the reference
or through our build with tools/RefRender (an offline JUCE VST3 host), or through our processor with
tools/WrRender (no plug-in loading, every DSP constant tunable). Renders stay local (nulltest/renders is
git-ignored). The pattern is Positron's harness, nulltest/po_ref.py.

    import wr_ref as h
    y = h.render(x)                                      # x: (2, n) or (n,) float, 48 kHz; reference, default settings
    ys = h.render_many([dict(x=x1, params={'Input Gain': -6}), dict(x=x2, norm={'Bypass': 1})])
    y = h.render(x, plugin='ours')                       # our built VST3 through RefRender
    y = h.render(x, plugin='model', tune={'smoothTauMs': 5})   # our processor through WrRender

Parameters by the names hosts show: params={'Input Gain': -6} uses the displayed value, norm={...} the normalised
value; auto=[('Input Gain', sample, norm), ...] changes a parameter while rendering (on block boundaries);
state=file loads a raw plug-in state first (the reference's own presets); sc=signal feeds the side-chain bus;
settle=ms lets a plug-in that applies parameters asynchronously catch up (Scorpius's reference needed 400); salt='...' goes into
the cache key for global state a job cannot carry (an oversampling setting on the reference's settings page).
Every job runs in a fresh instance (reset=False keeps the previous one). cache=True keeps reference renders in
renders/cache keyed on the exact input and settings (a state file by its contents); renders of our processor are
never cached.
"""
import hashlib, os, re, subprocess, uuid
import numpy as np

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # plugins/Wraith: sources and docs
ROOT = os.path.dirname(os.path.dirname(PLUGIN))                          # the repository: build/, reference/


def local(*keys):
    """The first non-empty value of keys in local.yaml at the repository root (flat 'key: value' lines, git-ignored;
    local.example.yaml lists the keys), or None."""
    path = os.path.join(ROOT, 'local.yaml')
    if not os.path.isfile(path):
        return None
    found = {}
    for line in open(path, encoding='utf-8'):
        m = re.match(r"\s*([\w.]+)\s*:\s*('(?:[^']|'')*'|\"[^\"]*\"|[^#]*?)\s*(?:#.*)?$", line)
        if m: found.setdefault(m.group(1), m.group(2)[1:-1].replace("''", "'") if m.group(2)[:1] in ('"', "'") else m.group(2))
    return next((found[k] for k in keys if found.get(k)), None)


# The reference: its VST3 and host name from local.yaml (<Id>.ref_vst3, <Id>.ref_name; local.example.yaml).
REF_VST3 = local('Wraith.ref_vst3')
REF_NAME = local('Wraith.ref_name')
EXE = os.path.join(ROOT, 'build', 'RefRender_artefacts', 'Release', 'RefRender.exe')
OURS_EXE = os.path.join(ROOT, 'build', 'WrRender_artefacts', 'Release', 'WrRender.exe')   # our processor, tunable ('model')
if os.environ.get('WR_RENDER') == 'dev':      # the second copy, for DSP changes while a fit runs on the first
    OURS_EXE = os.path.join(ROOT, 'build', 'WrRenderDev_artefacts', 'Release', 'WrRenderDev.exe')
PLUGINS = {
    'ref': (REF_VST3, REF_NAME),
    'ours': (os.path.join(ROOT, 'build', 'Wraith_artefacts', 'Release', 'VST3', 'Wraith.vst3'), 'Wraith'),
}
WORK = os.path.join(PLUGIN, 'nulltest', 'renders', 'tmp')
CACHE = os.path.join(PLUGIN, 'nulltest', 'renders', 'cache')
FS = 48000

# Stage isolation: the reference's own power buttons (the State parameters, 1 = on). The plug-in opens with the
# factory preset "lead"; ONLY('EQ') switches every other stage off and leaves the preset's values in place.
STATES = {'RIDER': 'Gain Rider State', 'CHAR': 'Character State', 'EQ': 'EQ State', 'DBL': 'Doubler State',
          'REV': 'Reverb State'}


def ONLY(*stages):
    """norm dict with the named stages on and every other stage off, e.g. ONLY('CHAR', 'EQ')"""
    return {name: 1.0 if key in stages else 0.0 for key, name in STATES.items()}


NONE = ONLY()
# The reverb loads its response asynchronously at 44.1 kHz only (MEASUREMENTS.md, Setup): renders there need a settle.
SETTLE = {44100: 1000}


def _stereo(x):
    x = np.asarray(x, np.float32)
    if x.ndim == 1: x = np.stack([x, x])
    return x


def _keyed(k, v):
    """a job's value as the cache key holds it: a state file by its bytes, so the key does not depend on where the
    repository is"""
    if k == 'state' and v:
        with open(v, 'rb') as f:
            return ('bytes', hashlib.sha1(f.read()).hexdigest())
    return v


def _key(j, plugin, fs, block, vary=False):
    h = hashlib.sha1(_stereo(j['x']).tobytes())
    for k in ('params', 'norm', 'auto', 'raw', 'reset', 'state', 'settle'): h.update(repr((k, _keyed(k, j.get(k)))).encode())
    if j.get('salt'): h.update(repr(('salt', j['salt'])).encode())
    if j.get('sc') is not None: h.update(_stereo(j['sc']).tobytes())
    h.update(repr((plugin, fs, block) + (('vary',) if vary else ())).encode())
    return h.hexdigest()


def render_many(jobs, plugin='ref', fs=FS, block=512, cache=False, tuning=None, vary=False):
    """jobs: dicts with x, and optional params / norm / auto / raw / sc / state / reset / settle / tune / salt.
    Returns a list of (2, n) float32 arrays, latency-compensated by the plug-in's reported latency (raw=True: not).
    vary=True (reference and VST3 only): irregular blocks of 1 ... block samples, as FL Studio delivers them."""
    if cache and plugin != 'model':          # our processor changes with every build / tuning: never cached
        os.makedirs(CACHE, exist_ok=True)
        keys = [None if any(j.get('reset') is False for j in jobs) else _key(j, plugin, fs, block, vary) for j in jobs]
        have = {i: np.load(os.path.join(CACHE, k + '.npy')) for i, k in enumerate(keys) if k and os.path.exists(os.path.join(CACHE, k + '.npy'))}
        todo = [i for i in range(len(jobs)) if i not in have]
        new = render_many([jobs[i] for i in todo], plugin, fs, block, vary=vary) if todo else []
        for i, y in zip(todo, new):
            have[i] = y
            if keys[i]: np.save(os.path.join(CACHE, keys[i] + '.npy'), y)
        return [have[i] for i in range(len(jobs))]
    os.makedirs(WORK, exist_ok=True)
    tag = uuid.uuid4().hex[:8]
    lines, outs = [], []
    for i, j in enumerate(jobs):
        x = _stereo(j['x'])
        fin = os.path.join(WORK, f'{tag}_{i}_in.f32'); fout = os.path.join(WORK, f'{tag}_{i}_out.f32')
        x.T.astype(np.float32).tofile(fin)
        parts = [f'"{fin}"', f'"{fout}"']
        for k, v in (j.get('params') or {}).items(): parts.append(f'"param:{k}={v}"')
        for k, v in (j.get('norm') or {}).items(): parts.append(f'"norm:{k}={v}"')
        for k, s, v in (j.get('auto') or []): parts.append(f'"auto:{k}@{int(s)}={v}"')
        if j.get('raw'): parts.append('raw=1')
        if j.get('reset') is False: parts.append('reset=0')
        if j.get('settle'): parts.append(f'settle={int(j["settle"])}')
        if j.get('state'): parts.append(f'"state={j["state"]}"')
        for k, v in (j.get('tune') or {}).items(): parts.append(f'"tune:{k}={float(v)!r}"')
        if j.get('sc') is not None:
            fsc = os.path.join(WORK, f'{tag}_{i}_sc.f32'); _stereo(j['sc']).T.astype(np.float32).tofile(fsc); parts.append(f'"sc={fsc}"')
        lines.append(' '.join(parts)); outs.append((fin, fout, x.shape[1]))
    jobfile = os.path.join(WORK, f'{tag}_jobs.txt')
    open(jobfile, 'w').write('\n'.join(lines) + '\n')
    if plugin == 'model':
        cmd = [OURS_EXE, jobfile, f'fs={fs}', f'block={block}'] + ([f'tuning={tuning}'] if tuning else [])
    else:
        path, name = PLUGINS[plugin]
        cmd = [EXE, path, name, jobfile, f'fs={fs}', f'block={block}'] + (['vary=1'] if vary else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if 'no parameter' in r.stdout or 'unknown tuning' in r.stdout: raise RuntimeError(r.stdout)
    res = []
    for fin, fout, n in outs:
        if not os.path.exists(fout): raise RuntimeError('render failed:\n' + ' '.join(cmd) + '\n' + r.stdout + r.stderr)
        y = np.fromfile(fout, np.float32).reshape(-1, 2).T.copy()
        res.append(y)
        os.remove(fin); os.remove(fout)
    os.remove(jobfile)
    return res


def render(x, plugin='ref', **kw):
    fs = kw.pop('fs', FS); block = kw.pop('block', 512)
    return render_many([dict(x=x, **kw)], plugin, fs, block)[0]


def latency(plugin='ref', fs=FS):
    """the latency the plug-in reports at fs (RefRender prints it when loading)"""
    r = subprocess.run([EXE, PLUGINS[plugin][0], PLUGINS[plugin][1], os.devnull, f'fs={fs}'], capture_output=True, text=True)
    if 'latency ' not in r.stdout: raise RuntimeError(r.stdout + r.stderr)
    return int(r.stdout.split('latency ')[1].split()[0])
