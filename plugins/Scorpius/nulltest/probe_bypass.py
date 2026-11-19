"""What the reference does around its bypass (MEASUREMENTS.md 2 and 12): the drum loop through the default preset,
bypassed at 1 s and back on at 2 s.
- While bypassed: the residual of the output against the input delayed by the reported latency (is the bypass the
  delayed input?), for the reference and for ours, at 48 and 44.1 kHz.
- After the switch back on, in windows: the reference and ours against three stand-ins of themselves rendered without
  the bypass: steady (never bypassed), silence (the input silent before the switch on: a start from silence) and
  paused (the bypassed second cut out: a state carried over). And ours against the reference.

    python probe_bypass.py [--fs 48000]
"""
import argparse
import numpy as np
import scipy.signal as sg
import sc_ref as o
from probe_order import drums

EDGES = [0, 480, 1920, 4800, 9600, 19200]


def db(a, b):
    return 10 * np.log10(float(np.sum(np.asarray(a, np.float64) ** 2)) / (float(np.sum(np.asarray(b, np.float64) ** 2)) + 1e-30) + 1e-30)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fs', type=int, default=48000)
    a = ap.parse_args()
    fs = a.fs
    x = np.asarray(drums(), np.float64)
    x = (x if x.ndim == 2 else np.tile(x, (2, 1)))[:, :int(3.2 * 48000)] * 10 ** (-12 / 20)
    if fs != 48000:
        x = sg.resample_poly(x, fs, 48000, axis=-1)
    x = x.astype(np.float32)
    t1, t2 = fs // 512 * 512, 2 * fs // 512 * 512
    jobs = {'bypassed': dict(x=x, auto=[('Bypass', t1, 1.0), ('Bypass', t2, 0.0)]),
            'steady': dict(x=x),
            'silence': dict(x=np.concatenate([np.zeros_like(x[:, :t2]), x[:, t2:]], axis=1)),
            'paused': dict(x=np.concatenate([x[:, :t1], x[:, t2:]], axis=1))}
    out = {}
    for plugin in ('ref', 'model'):
        ys = o.render_many(list(jobs.values()), plugin, fs=fs, cache=plugin == 'ref')
        out[plugin] = dict(zip(jobs, ys))
        lat = o.latency('ref' if plugin == 'ref' else 'ours', fs) if plugin == 'ref' else None
    lat = o.latency('ref', fs)
    print(f'{fs} Hz, bypass on at {t1}, off at {t2}; the reference reports {lat} samples of latency')
    for plugin in ('ref', 'model'):
        y = out[plugin]['bypassed']
        s, e = t1 + 4800, t2 - 480
        best = min(range(0, lat + 13), key=lambda d: db(y[:, s:e] - x[:, s - d:e - d], x[:, s - d:e - d]))
        print(f'{plugin:6s} while bypassed (the harness has taken the reported latency off), against the input: {db(y[:, s:e] - x[:, s:e], x[:, s:e]):7.1f} dB'
              f'   (best whole-sample delay {best}: {db(y[:, s:e] - x[:, s - best:e - best], x[:, s - best:e - best]):7.1f} dB)')
    print('after the switch back on, residual in dB per window (samples after it):', EDGES)
    for plugin in ('ref', 'model'):
        y = out[plugin]['bypassed']
        stand = {'steady': out[plugin]['steady'], 'silence': out[plugin]['silence'],
                 'paused': np.concatenate([np.zeros_like(x[:, :t2 - t1]), out[plugin]['paused']], axis=1)}
        for k, z in stand.items():
            row = [db(y[:, t2 + a0:t2 + b0] - z[:, t2 + a0:t2 + b0], z[:, t2 + a0:t2 + b0]) for a0, b0 in zip(EDGES, EDGES[1:])]
            print(f'{plugin:6s} against its own {k:8s}', '  '.join(f'{v:7.1f}' for v in row))
    r, y = out['ref']['bypassed'], out['model']['bypassed']
    print('ours against the reference   ', '  '.join(f'{db(y[:, t2 + a0:t2 + b0] - r[:, t2 + a0:t2 + b0], r[:, t2 + a0:t2 + b0]):7.1f}'
                                                     for a0, b0 in zip(EDGES, EDGES[1:])),
          f'   steady, the same windows a second later: ',
          '  '.join(f'{db(out["model"]["steady"][:, t2 + fs + a0:t2 + fs + b0] - out["ref"]["steady"][:, t2 + fs + a0:t2 + fs + b0], out["ref"]["steady"][:, t2 + fs + a0:t2 + fs + b0]):7.1f}'
                    for a0, b0 in zip(EDGES, EDGES[1:])))


if __name__ == '__main__':
    main()
