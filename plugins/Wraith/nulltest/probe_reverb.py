"""Reverb stage (MEASUREMENTS.md "Reverb"): the dry / wet law against Mix, the wet response's shape, and what the
filter does, from impulses through the reverb alone.

    python probe_reverb.py mix        dry and wet gains at several Mix values (room, 48 kHz)
    python probe_reverb.py filter     the wet response at several Filter values against 20 kHz
    python probe_reverb.py shape      length, onset, decay per octave and stereo of room and plate per rate
    python probe_reverb.py lp         the filter alone: with an edited state whose response does not load, the wet path
                                      is the filter's impulse response; fitted with RBJ low-passes per rate
"""
import os, sys
import numpy as np
import ts as h

REF = os.path.join(h.ROOT, 'reference', 'Wraith')
PLATE = os.path.join(REF, 'plate.state')      # the default state with the plate selected (tools/tgpstate.py edit)
AT = 1000


def impulse(fs, secs=4.0, ch=None):
    x = np.zeros((2, int(fs * secs)), np.float32)
    if ch is None: x[:, AT] = 0.5
    else: x[ch, AT] = 0.5
    return x


def render(fs, params, state=None, ch=None, secs=4.0):
    j = dict(x=impulse(fs, secs, ch), norm=h.ONLY('REV'), params=params)
    if state: j['state'] = state
    if fs in h.SETTLE: j['settle'] = h.SETTLE[fs]
    return h.render_many([j], fs=fs, cache=True)[0] / 0.5


def mix():
    fs = 48000
    wet = render(fs, {'Reverb Mix': 1.0, 'Reverb Filter': 20000})
    print('Mix 1: sample at the impulse', wet[:, AT], ' energy after', 10 * np.log10(np.sum(wet[:, AT + 1:] ** 2, axis=1)))
    for m in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0):
        y = render(fs, {'Reverb Mix': m, 'Reverb Filter': 20000})
        # y = d * delta + w * wet_part: d from the impulse sample (less the wet's own value there), w by projection
        tail = slice(AT + 1, None)
        w = np.sum(y[:, tail] * wet[:, tail]) / np.sum(wet[:, tail] ** 2)
        d = (y[0, AT] - w * wet[0, AT])
        res = y[:, tail] - w * wet[:, tail]
        print(f'Mix {m:4.2f}: dry {d:.6f}  wet {w:.6f}  (d^2 + w^2 {d * d + w * w:.4f}, d + w {d + w:.4f})  '
              f'fit residual {10 * np.log10(np.sum(res ** 2) / np.sum(y[:, tail] ** 2) + 1e-30):6.1f} dB')


def filt():
    fs = 48000
    ref = render(fs, {'Reverb Mix': 1.0, 'Reverb Filter': 20000})
    R = np.fft.rfft(ref[0, AT:AT + fs])
    f = np.fft.rfftfreq(fs, 1 / fs)
    for fc in (2000, 5000, 9845.186, 15000):
        y = render(fs, {'Reverb Mix': 1.0, 'Reverb Filter': fc})
        Y = np.fft.rfft(y[0, AT:AT + fs])
        H = Y / (R + 1e-12)
        pts = [500, 1000, fc / 2, fc, 2 * fc, 16000, 20000]
        idx = [int(p) for p in pts if p < fs / 2]
        def sm(i): return 20 * np.log10(np.abs(np.median(np.abs(H[max(1, i - 20): i + 20]))))
        print(f'Filter {fc:8.1f}: ' + '  '.join(f'{p:.0f} Hz {sm(i):+6.2f}' for p, i in zip(pts, idx)))


def shape():
    for fs in (44100, 48000, 88200, 96000):
        for name, st in (('room', None), ('plate', PLATE)):
            w = render(fs, {'Reverb Mix': 1.0, 'Reverb Filter': 20000}, state=st)
            e = np.cumsum((w[:, ::-1] ** 2).sum(axis=0))[::-1]
            edc = 10 * np.log10(e / e[AT] + 1e-30)
            t60 = (np.argmax(edc < -60) - AT) / fs if np.any(edc < -60) else None
            onset = np.argmax(np.abs(w[0]) > 1e-4 * np.max(np.abs(w[0]))) - AT
            last = np.nonzero(np.abs(w).max(axis=0) > 1e-7)[0][-1] - AT
            lr = np.corrcoef(w[0, AT:], w[1, AT:])[0, 1]
            print(f'{fs:6d} {name:5s}: onset {onset} samples, energy-decay -60 dB at {t60} s, last sample above -140 dB '
                  f'at {last / fs:.3f} s, L/R correlation {lr:.3f}, peak {np.max(np.abs(w)):.4f}')


def rbj_lp(fs, f0, q, warp=False):
    w0 = 2 * np.arctan(np.pi * f0 / fs) if warp else 2 * np.pi * f0 / fs
    c, al = np.cos(w0), np.sin(w0) / (2 * q)
    b = np.array([(1 - c) / 2, 1 - c, (1 - c) / 2]); a = np.array([1 + al, -2 * c, 1 - al])
    return b / a[0], a / a[0]


def lp():
    from scipy.optimize import least_squares
    from scipy.signal import lfilter
    for fs in (44100, 48000, 96000):
        for fc in (2000, 9845.186, 20000):
            w = render(fs, {'Reverb Mix': 1.0, 'Reverb Filter': fc}, state=PLATE, secs=0.2)[0, AT:AT + 4096]
            imp = np.zeros(4096); imp[0] = 1
            best = None
            for warp in (False, True):
                r = least_squares(lambda p: lfilter(*rbj_lp(fs, p[0], p[1], warp), imp) - w, [fc * 0.9, 0.7],
                                  bounds=([100, 0.1], [fs / 2 * 0.999, 5]))
                e = lfilter(*rbj_lp(fs, r.x[0], r.x[1], warp), imp) - w
                null = 10 * np.log10(np.sum(e ** 2) / np.sum(w ** 2))
                if best is None or null < best[0]: best = (null, r.x, warp)
            print(f'{fs:6d} Filter {fc:9.3f}: f0 {best[1][0]:10.3f}  Q {best[1][1]:.6f}  warp {best[2]}  null {best[0]:7.1f} dB')


if __name__ == '__main__':
    {'mix': mix, 'filter': filt, 'shape': shape, 'lp': lp}[sys.argv[1]]()
