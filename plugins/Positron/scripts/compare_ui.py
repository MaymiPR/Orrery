"""Positron's editor against the reference: a measuring tool, it writes no shipped file.

    python compare_ui.py reference.png ours.png out.png [x0 y0 x1 y1]
        both 200 %: reference / ours / |difference| x3 stacked; prints the mean absolute difference, overall and per area
    python compare_ui.py --zoom reference.png ours.png out.png [zoom]
        side-by-side zooms (reference | ours) of named regions of two 200 % screenshots
    python compare_ui.py --knobs
        knob mouse behaviour through RefCapture drag scripts: the parameter value after plain, Ctrl, Shift (velocity)
        and overshoot drags, and whether a knob's caption shows its value with the mouse at points in and around its
        cell (hover); run from PowerShell (the Bash tool cuts GUI processes short)
"""
import os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))

AREAS = {'top bar': (0, 0, 1776, 61), 'input': (0, 61, 178, 531), 'eq': (178, 61, 352, 531), 'centre': (352, 61, 1118, 531),
         'gain red.': (1118, 61, 1422, 531), 'limiter': (1422, 61, 1596, 531), 'output': (1596, 61, 1776, 531), 'plate': (0, 531, 1776, 719)}
REGIONS = {  # 200 % pixel boxes
    'logo + preset': (0, 0, 470, 60), 'arrows + save': (740, 0, 940, 60), 'sidechain': (990, 0, 1300, 60),
    'ui scale + gear': (1480, 0, 1776, 60), 'input meter': (0, 60, 180, 280), 'eq': (180, 60, 354, 530),
    'gr top': (1118, 60, 1424, 290), 'gr bottom': (1118, 290, 1424, 530), 'limiter': (1422, 60, 1598, 280),
    'output': (1596, 60, 1776, 280), 'plate left': (0, 528, 360, 719), 'plate right': (1120, 528, 1776, 719),
    'letters': (340, 680, 1130, 719)}


def difference(args):
    ref = np.asarray(Image.open(args[0]).convert('RGB')).astype(float)
    our = np.asarray(Image.open(args[1]).convert('RGB')).astype(float)
    h, w = min(ref.shape[0], our.shape[0]), min(ref.shape[1], our.shape[1])
    ref, our = ref[:h, :w], our[:h, :w]
    box = len(args) >= 7
    if box:
        x0, y0, x1, y1 = map(int, args[3:7])
        ref, our = ref[y0:y1, x0:x1], our[y0:y1, x0:x1]
    d = np.abs(ref - our)
    print(f'mean |diff| {d.mean():.2f}')
    if not box:
        for k, (a, b, c, e) in AREAS.items():
            print(f'  {k:10s} {d[b:e, a:c].mean():6.2f}')
    out = np.concatenate([ref, our, np.clip(d * 3, 0, 255)], 0).astype(np.uint8)
    Image.fromarray(out).save(args[2])


def zoom(args):
    ref, our = Image.open(args[0]).convert('RGB'), Image.open(args[1]).convert('RGB')
    z = float(args[3]) if len(args) > 3 else 2.0
    tiles = []
    for name, box in REGIONS.items():
        w, h = box[2] - box[0], box[3] - box[1]
        t = Image.new('RGB', (int(2 * w * z) + 12, int(h * z) + 18), (60, 0, 0))
        t.paste(ref.crop(box).resize((int(w * z), int(h * z)), Image.NEAREST), (0, 18))
        t.paste(our.crop(box).resize((int(w * z), int(h * z)), Image.NEAREST), (int(w * z) + 12, 18))
        ImageDraw.Draw(t).text((4, 3), name + '   (reference | ours)', fill=(255, 255, 0))
        tiles.append(t)
    W = max(t.width for t in tiles); H = sum(t.height for t in tiles)
    out = Image.new('RGB', (W, H)); y = 0
    for t in tiles:
        out.paste(t, (0, y)); y += t.height
    out.save(args[2])


OUT = '841.74,300'
DRAGS = [f'{OUT},0,10,,100', f'{OUT},0,10,ctrl,100', f'{OUT},0,30,ctrl+mid,30', f'{OUT},0,-80,back,80']
DRAGS += [f'{OUT},0,{d},shift,{n}' for d, n in ((20, 10), (20, 5), (16, 2), (20, 2), (12, 1), (20, 1), (40, 1), (60, 1), (100, 1), (200, 1))]
HOVER = ['45.755,262', '45.755,268', '45.755,313', '45.755,358', '1,313', '3,313', '88,313', '90,313',
         '133.375,69', '133.375,71', '133.375,134', '133.375,137', '92,90', '176,90']


def knobs():
    sys.path.insert(0, os.path.join(HERE, '..', 'nulltest'))
    import po_ref
    cap = os.path.join(po_ref.ROOT, 'build', 'RefCapture_artefacts', 'Release', 'RefCapture.exe')
    shots = os.path.join(po_ref.ROOT, 'reference', 'shots')

    def run(who, args, tag):
        path, name = po_ref.PLUGINS[who]
        r = subprocess.run([cap, path, name, os.path.join(shots, f'{tag}.png'), 'design=888'] + args, capture_output=True, text=True, timeout=600)
        return r.stdout

    def drags(who):
        args = []
        for d in DRAGS: args += [f'drag={d}', f'drag={OUT},0,0,dbl']
        out = run(who, args, f'uik_{who}')
        vals = re.findall(r'^after: .*?\[Output Gain=([-\d.]+)\]', out, re.M)
        return [float(v) for v in vals[0::2]]

    def hover(who):
        args = []
        for q in HOVER: args += ['drag=450,150,0,0,hover', f'drag={q},0,0,hover']
        run(who, args, f'uih_{who}')
        res = []
        for i, q in enumerate(HOVER):
            box = (5, 268, 88, 284) if float(q.split(',')[1]) > 200 else (95, 113, 172, 129)
            cut = lambda n: np.asarray(Image.open(os.path.join(shots, f'uih_{who}_{n}_hover.png')).convert('L')).astype(float)[box[1]:box[3], box[0]:box[2]]
            res.append(np.abs(cut(2 * i + 2) - cut(2 * i + 1)).mean() > 2.0)      # differs from the neutral caption
        return res

    r, o = drags('ref'), drags('ours')
    print('drag (output knob from 0 dB)            ref      ours')
    for d, a, b in zip(DRAGS, r, o):
        print(f'  {d:34s} {a:8.3f} {b:8.3f}' + ('' if abs(a - b) < 0.0015 else '   <-- differs'))
    hr, ho = hover('ref'), hover('ours')
    print('hover point            ref      ours')
    for q, a, b in zip(HOVER, hr, ho):
        print(f'  {q:18s} {"value" if a else "caption":8s} {"value" if b else "caption":8s}' + ('' if a == b else '   <-- differs'))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['--zoom']:
        zoom(a[1:])
    elif a[:1] == ['--knobs']:
        knobs()
    elif len(a) >= 3:
        difference(a)
    else:
        sys.exit(__doc__)
