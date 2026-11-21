"""The parameters of the built plug-in against the reference's, by the texts a host shows: every parameter of
paramdump.txt (the reference's parameters at 41 positions, in this folder) must exist in our VST3 under the same
name, and at each position our value must be the reference's to within one unit of the last decimal the reference
shows, or ten parts in a million of the value where that is more (a table taper keeps fewer decimals). A stepped
parameter that lands one step apart exactly half-way between two steps is a tie, listed and not counted: the two
sides round a tie differently. Texts that are no numbers (a switch that reads Off / On on one side) are compared by their order instead:
the positions where the text changes must be the same. Needs the tools and the VST3 built; the reference is not
loaded.

    python check_tapers.py [--tol 1.0] [--verbose]

Exit codes: 0 every parameter agrees; 1 a parameter is missing or a value differs; 2 the dump tool or the VST3 is not
built, or paramdump.txt is missing."""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(PLUGIN))
ID = os.path.basename(PLUGIN)
TOOL = os.path.join(ROOT, 'build', 'ParamDump_artefacts', 'Release', 'ParamDump' + ('.exe' if os.name == 'nt' else ''))
VST3 = os.path.join(ROOT, 'build', f'{ID}_artefacts', 'Release', 'VST3', f'{ID}.vst3')
HEAD = re.compile(r"^\[\d+\] id=\S+ name='(.*?)' label='.*?' steps=(\d+)")
POINT = re.compile(r"^\s+([0-9.]+) -> '(.*)'\s*$")
NUMBER = re.compile(r'^\s*([-+]?\d+(?:\.\d+)?)\s*(k?)')


def parse(text):
    """({name: [(position, text), ...]}, {name: steps}) of a dump"""
    out, steps, name = {}, {}, None
    for line in text.splitlines():
        m = HEAD.match(line)
        if m:
            name = m.group(1)
            out[name] = []
            steps[name] = int(m.group(2))
            continue
        m = POINT.match(line)
        if m and name is not None:
            out[name].append((float(m.group(1)), m.group(2)))
    return out, steps


def number(text):
    """(value, one unit of its last decimal), or None for a text that is no number"""
    m = NUMBER.match(text)
    if not m:
        return None
    scale = 1000.0 if m.group(2) else 1.0
    digits = len(m.group(1).split('.')[1]) if '.' in m.group(1) else 0
    return float(m.group(1)) * scale, scale * 10.0 ** -digits


def changes(points):
    """the positions at which the text changes"""
    return [p for (p, t), (_, before) in zip(points[1:], points[:-1]) if t != before]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--tol', type=float, default=1.0, help='units of the last decimal the reference shows (default 1)')
    ap.add_argument('--verbose', action='store_true', help='also list the parameters that agree')
    a = ap.parse_args()
    dump = os.path.join(HERE, 'paramdump.txt')
    for what, path in (('paramdump.txt', dump), ('ParamDump', TOOL), ('the VST3', VST3)):
        if not os.path.exists(path):
            print(f'{what} is not there ({os.path.relpath(path, ROOT)}): nothing compared')
            return 2
    ref, steps = parse(open(dump, encoding='utf-8').read())
    r = subprocess.run([TOOL, VST3, ID, 'points=41'], capture_output=True, text=True)
    ours, _ = parse(r.stdout)
    if r.returncode != 0 or not ours:
        print(f'ParamDump failed on {os.path.relpath(VST3, ROOT)} (exit code {r.returncode}): nothing compared')
        return 2
    bad = 0
    for name, points in ref.items():
        if name not in ours:
            print(f'MISSING  {name}: the reference has it, ours does not')
            bad += 1
            continue
        mine = dict(ours[name])
        worst, where, kind, ties = 0.0, None, 'values', 0
        n = steps.get(name, 0)
        step = (number(points[-1][1])[0] - number(points[0][1])[0]) / (n - 1) if 2 <= n <= 100000 and number(points[0][1]) and number(points[-1][1]) else 0.0
        for pos, text in points:
            if pos not in mine:
                worst, where = float('inf'), (pos, text, 'no such position')
                break
            a_, b_ = number(text), number(mine[pos])
            if a_ is None or b_ is None:
                kind = 'texts'
                continue
            err = abs(a_[0] - b_[0]) / max(a_[1], 1.0e-5 * abs(a_[0]))
            if step and abs(abs(a_[0] - b_[0]) - abs(step)) < 1.0e-6 and abs((pos * (n - 1)) % 1.0 - 0.5) < 1.0e-6:
                ties += 1
                continue
            if err > worst:
                worst, where = err, (pos, text, mine[pos])
        if kind == 'texts':
            same = changes(points) == changes(ours[name])
            if not same:
                print(f'DIFFERS  {name}: the text changes at {changes(points)} in the reference and at {changes(ours[name])} in ours')
                bad += 1
            elif a.verbose:
                print(f'same     {name}: texts change at the same positions')
            continue
        if worst > a.tol:
            print(f"DIFFERS  {name}: at {where[0]:.4f} the reference shows '{where[1]}', ours '{where[2]}' ({worst:.1f} units)")
            bad += 1
        elif ties:
            print(f'tie      {name}: one step apart at {ties} positions half-way between two steps, the same elsewhere')
        elif a.verbose:
            print(f'same     {name}: within {worst:.2f} units at {len(points)} positions')
    extra = [n for n in ours if n not in ref]
    print(f'{ID}: {len(ref)} parameters of the reference, {len(ref) - bad} agree, {bad} differ'
          + (f'; ours alone: {", ".join(extra)}' if extra else ''))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
