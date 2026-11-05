"""Gain Rider (MEASUREMENTS.md "Rider"): the rider alone.

    python probe_rider.py static     steady gain of a 1 kHz tone against level, per Amount and Floor
    python probe_rider.py timing     the gain after level steps, per Speed
"""
import sys
import numpy as np
import nulltest_lib as nl
import ts as h

FS = 48000


def static():
    levels = list(np.arange(-60.0, 1.0, 3.0))
    x = nl.stereo(nl.steps(levels, 1.0, f=1000.0)).astype(np.float32)
    settings = [(0.7, -30), (1.0, -30), (0.35, -30), (1.0, -50), (1.0, -18)]
    ys = h.render_many([dict(x=x, norm=h.ONLY('RIDER'), params={'Gain Rider Amount': a, 'Gain Rider Floor': fl})
                        for a, fl in settings], cache=True)
    seg = FS
    print('in (peak dBFS) | gain dB at (Amount, Floor) ' + '  '.join(str(s) for s in settings))
    for k, lv in enumerate(levels):
        a, b = k * seg + seg // 2, (k + 1) * seg
        g = [20 * np.log10(np.sqrt(np.mean(y[0, a:b] ** 2)) / np.sqrt(np.mean(x[0, a:b] ** 2))) for y in ys]
        print(f'{lv:6.0f} | ' + ' '.join(f'{v:+8.2f}' for v in g))


def timing():
    x = nl.stereo(nl.steps([-30, -10, -30, -20, -40, -20], 1.5, f=1000.0)).astype(np.float32)
    speeds = (0.001, 0.003, 0.006, 0.01)
    ys = h.render_many([dict(x=x, norm=h.ONLY('RIDER'), params={'Gain Rider Amount': 1.0, 'Gain Rider Floor': -50,
                                                                  'Gain Rider Speed': s}) for s in speeds], cache=True)
    w = 240
    def g(y, i): return 20 * np.log10(np.sqrt(np.mean(y[0, i:i + w] ** 2)) / np.sqrt(np.mean(x[0, i:i + w] ** 2)))
    for step in range(1, 6):
        at = int(step * 1.5 * FS)
        print(f'step {step}: ' + '  '.join(f'speed {s}: ' + ' '.join(f'{g(y, at + int(ms * 48)):+6.1f}' for ms in (0, 5, 10, 20, 50, 100, 200, 400, 800, 1400))
                                        for s, y in zip(speeds, ys)))


if __name__ == '__main__':
    {'static': static, 'timing': timing}[sys.argv[1]]()
