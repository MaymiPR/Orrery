"""The reference's factory presets from its own saved states (reference/Wraith/presets/p<n>.state, saved after each
click on its next-preset arrow by tools/RefCapture savestates=, and default.state for "lead"): name, exact values,
reverb. Prints them and writes renders/presets.json (MEASUREMENTS.md "Presets").

    python read_presets.py
"""
import json, os, re, sys
import wr_ref as h
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'scripts', 'nulltest'))   # scripts/nulltest/ref_state_lib.py
import ref_state_lib as rs

REF = os.path.join(h.ROOT, 'reference', 'Wraith')
# our names (Source/Presets.cpp) for the states in the order the next-preset arrow steps through them from the start-up
# preset: default.state, then p1 ... p10 (p11 is the start-up preset again)
NAMES = ['lead', 'up front', 'wide image', 'short phase', 'wide and wet', 'wide lead', 'backing stack', 'big cave',
         'doubler alone', 'soft room', 'hard squeeze']


def num(block, key):
    m = re.search(r'\b' + key + r'\s*=\s*([-0-9.e]+)', block)
    return float(m.group(1)) if m else None


def section(text, name):
    i = text.find(name + ' = {')
    if i < 0: return ''
    depth, j = 0, text.index('{', i)
    for k in range(j, len(text)):
        depth += text[k] == '{'; depth -= text[k] == '}'
        if depth == 0: return text[j:k + 1]
    return ''


def read(path):
    s = open(path, 'rb').read()
    text = rs.split(s)[1].decode('latin1')
    pre = text[text.index('Script state'):]
    rider, chorus, eq, rev = section(pre, 'gainRider'), section(pre, 'chorus'), section(pre, 'eq'), section(pre, 'reverb')
    sel = re.search(r'onOff = \{\s*select = (\d)', pre)
    gain = lambda key: float(re.search(key + r' = \{\s*gain = ([-0-9.e]+)', pre).group(1))
    v = {'inputGain': gain('input'), 'outputGain': gain('output'),
         'riderOn': num(rider, 'onOff'), 'riderAmount': num(rider, 'amount'), 'riderSpeed': num(rider, 'attackTime'),
         'riderFloor': num(rider, 'noiseFloor'), 'compression': num(section(pre, 'compressorsDriverGain'), 'offset'),
         'focus': num(section(pre, 'eqScale'), 'offset'), 'characterOn': float(sel.group(1)) if sel else None,
         'eqOn': num(eq, 'onOff'), 'eqLow': num(eq, 'warmthEQGain'), 'eqHigh': num(eq, 'airEQGain'),
         'doublerOn': num(chorus, 'onOff'), 'doublerMix': num(chorus, 'mix'), 'doublerStereo': num(chorus, 'stereo'),
         'reverbOn': num(rev, 'onOff'), 'reverbMix': num(rev, 'mix'), 'reverbFilter': num(rev, 'filter'),
         'reverbType': 1.0 if 'plate.flac' in rev else 0.0}
    return v


if __name__ == '__main__':
    out = {}
    files = [os.path.join(REF, 'default.state')] + [os.path.join(REF, 'presets', f'p{k}.state') for k in range(1, len(NAMES))]
    for name, p in zip(NAMES, files):
        v = read(p)
        out[name] = dict(v, state=os.path.relpath(p, REF))
        print(f'{name:18s} ' + ' '.join(f'{k}={v[k]}' for k in v))
    json.dump(out, open(os.path.join(h.PLUGIN, 'nulltest', 'renders', 'presets.json'), 'w'), indent=1)
    # the factory table for Source/Presets.cpp: every value that differs from the host default
    defaults = {'inputGain': 0, 'outputGain': 0, 'riderOn': 0, 'riderAmount': 0.7, 'riderSpeed': 0.003, 'riderFloor': -30,
                'compression': 0, 'focus': 0, 'characterOn': 0, 'eqOn': 0, 'eqLow': 0, 'eqHigh': 0, 'doublerOn': 0,
                'doublerMix': 0.1, 'doublerStereo': 0.5, 'reverbOn': 0, 'reverbMix': 0.1, 'reverbFilter': 20000, 'reverbType': 0}
    for name, v in out.items():
        items = [f'{{ id::{k}, {float(f"{v[k]:.9g}")!r}f }}' for k in defaults if abs(v[k] - defaults[k]) > 1e-9]
        print(f'        {{ "{name}", {{ ' + ', '.join(items) + ' } },')
