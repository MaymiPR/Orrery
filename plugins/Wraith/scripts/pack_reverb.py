"""The reverb's responses, packed for the plug-in (the reference's measured responses through zero-latency
convolution, shipped on recorded approval). The reference's reverb is linear and time-invariant,
its left and right paths independent (no cross-feed), and its wet path is the response followed by an RBJ low-pass that
stays in even at the 20 kHz setting (MEASUREMENTS.md "Reverb"). So each response is captured with Mix at 1 and Filter at
20 kHz, the 20 kHz low-pass (fitted per rate from the filter-only path) is taken out by regularised deconvolution, and
the result is stored per rate as 16-bit floats. Both responses come from render_plate.py (recorded with the
reference's editor open, since its script loads the plate).

Writes plugins/Wraith/resources/ir/reverb_<rate>.bin: per reverb (room, plate): uint32 length, then length x 2 float16
(L, R interleaved per sample).

    python pack_reverb.py
"""
import os, struct
import numpy as np
from scipy.optimize import least_squares
from scipy.signal import lfilter
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'nulltest'))   # the harness
import wr_ref as h
import probe_reverb as pr

OUT = os.path.join(h.PLUGIN, 'resources', 'ir')
RATES = (44100, 48000, 88200, 96000)
FILTER_ONLY = os.path.join(pr.REF, 'filteronly.state')    # a state whose response does not load: the filter alone
TYPES = ('room', 'plate')
CUT_DB = -80.0          # each response ends where its decay energy has fallen this far, faded over the last 30 ms


def lp20k(fs):
    """the 20 kHz setting's low-pass at this rate, fitted to the filter-only path"""
    w = pr.render(fs, {'Reverb Mix': 1.0, 'Reverb Filter': 20000}, state=FILTER_ONLY, secs=0.2)[0, pr.AT:pr.AT + 4096]
    imp = np.zeros(4096); imp[0] = 1
    r = least_squares(lambda p: lfilter(*pr.rbj_lp(fs, p[0], p[1]), imp) - w, [19900, 0.7], bounds=([15000, 0.5], [fs / 2 * 0.999, 1]))
    return r.x


def main():
    os.makedirs(OUT, exist_ok=True)
    for fs in RATES:
        f0, q = lp20k(fs)
        blob = b''
        for name in TYPES:
            # recorded with the editor open (render_plate.py): the plate only loads there; the room recorded this way
            # equals the offline render to -132 dB and better
            y = np.load(os.path.join(pr.REF, f'{name}_rec_{fs}.npy')).astype(float)
            e = np.cumsum((y[:, ::-1] ** 2).sum(0))[::-1]
            n = int(np.argmax(10 * np.log10(e / e[0] + 1e-300) < CUT_DB)) or y.shape[1]
            N = 1 << int(np.ceil(np.log2(len(y[0]) * 2)))
            b, a = pr.rbj_lp(fs, f0, q)
            H = np.fft.rfft(b, N) / np.fft.rfft(a, N)
            Y = np.fft.rfft(y, N, axis=1)
            eps = 1e-6
            ir = np.fft.irfft(Y * np.conj(H) / (np.abs(H) ** 2 + eps), N, axis=1)[:, :n]
            fade = int(0.03 * fs)
            ir[:, -fade:] *= np.linspace(1, 0, fade)
            # check: the captured wet path against the response refiltered
            back = lfilter(b, a, ir, axis=1)
            err = 10 * np.log10(np.sum((back - y[:, :n]) ** 2) / np.sum(y[:, :n] ** 2))
            q16 = ir.astype(np.float16)
            e16 = 10 * np.log10(np.sum((q16.astype(float) - ir) ** 2) / np.sum(ir ** 2))
            print(f'{fs:6d} {name:5s}: {n / fs:.2f} s, low-pass {f0:.1f} Hz Q {q:.4f}, refiltered null {err:.1f} dB, float16 {e16:.1f} dB')
            blob += struct.pack('<I', n) + q16.T.astype('<f2').tobytes()
        path = os.path.join(OUT, f'reverb_{fs}.bin')
        open(path, 'wb').write(blob)
        print(f'  {os.path.basename(path)}: {len(blob) / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
