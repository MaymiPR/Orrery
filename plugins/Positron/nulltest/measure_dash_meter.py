"""The limiter's dash meter, read from RefCapture films: a 1 kHz tone through the limiter alone (12 dB input gain)
rising in steps; per step the lit cells of the left channel's 31 dash cells (4 px pitch from y 90, x 744) against
how far the limiter's input goes above 0 dBFS, and after the last step how the cells fall back.

    python measure_dash_meter.py write [coarse|fine]     renders/tmp/dash_probe[2].f32 (mono float32 48 kHz) and .json
    RefCapture "<reference.vst3>" "<reference name>" film.raw "Character Bypass=1" "EQ Bypass=1" "Limiter Input Gain=1"
               in=<that file> rows=0.0,0.62
    python measure_dash_meter.py read film.raw [coarse|fine]"""
import json, os, sys
import numpy as np
import po_ref
from film_lib import Film

FS = po_ref.FS
GAIN = 12.0
CX = 744


def probe(kind):
    levels, hold = (np.arange(-14.0, 0.01, 0.5), 1.0) if kind == 'coarse' else (np.round(np.arange(-12.0, -9.99, 0.1), 2), 0.6)
    n = int(hold * FS); t = np.arange(len(levels) * n) / FS
    x = np.concatenate([np.zeros(FS), np.repeat(10 ** (levels / 20), n) * np.sin(2 * np.pi * 1000 * t), np.zeros(3 * FS)])
    return x.astype(np.float32), dict(levels=levels.tolist(), start=1.0, hold=hold)


def cells(frame):
    col = frame.max(axis=2)[:, CX - 4:CX + 5].max(axis=1)
    return [k for k in range(31) if col[89 + 4 * k:92 + 4 * k].max() > 100]


if __name__ == '__main__':
    kind = sys.argv[-1] if sys.argv[-1] in ('coarse', 'fine') else 'coarse'
    base = os.path.join(po_ref.WORK, 'dash_probe' + ('' if kind == 'coarse' else '2'))
    if sys.argv[1] == 'write':
        x, meta = probe(kind); os.makedirs(po_ref.WORK, exist_ok=True)
        x.tofile(base + '.f32'); json.dump(meta, open(base + '.json', 'w')); print(base + '.f32', len(x) / FS, 's')
        raise SystemExit
    f = Film(sys.argv[2]); meta = json.load(open(base + '.json'))
    for i, lv in enumerate(meta['levels']):
        t0 = meta['start'] + i * meta['hold']
        print(f'{lv + GAIN:5.1f} dB over 0 dBFS: cells {cells(f.at(t0 + 0.8 * meta["hold"]))}')
    end, prev = meta['start'] + len(meta['levels']) * meta['hold'], None
    for i in range(f.n):
        if f.t[i] < end - 0.1: continue
        c = cells(f.frame(i))
        if c != prev: print(f'{f.t[i] - end:+5.2f} s after the last step: cells {c}'); prev = c
