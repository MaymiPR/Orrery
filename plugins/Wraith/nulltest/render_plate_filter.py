"""The plate at several Filter settings (MEASUREMENTS.md "Reverb"): the reference plays its plate only
with its editor open, so each setting is recorded through tools/RefCapture record=1 as render_plate.py does it (the
plate state, every other stage off, Mix 1): an impulse at Filter 2 / 5.2 / 8 / 11.4 / 20 kHz, the 5.2 kHz impulse a
second time (is the plate the same from run to run), and noise at 11.4 kHz (do the impulses predict it). One capture at
a time. Writes reference/Wraith/plate_filter_<hz>.npy (the output per unit impulse) and plate_filter_noise_<hz>.npy.

    python render_plate_filter.py impulse 5206          one impulse capture at that Filter (Hz)
    python render_plate_filter.py noise 11425           the noise capture (its input: nulltest_lib.noise seed 31)
"""
import os, subprocess, sys
import numpy as np
import nulltest_lib as nl
import wr_ref as h
import render_plate as prc

FS = 48000
TAPER = [2000.0, 2230.2, 2466.24, 2708.34, 2956.74, 3211.69, 3473.46, 3742.32, 4018.55, 4302.48, 4594.42, 4894.72,
         5203.75, 5521.89, 5849.54, 6187.15, 6535.17, 6894.09, 7264.44, 7646.76, 8041.65, 8449.73, 8871.69, 9308.23,
         9760.14, 10228.2, 10713.4, 11216.6, 11738.8, 12281.2, 12844.9, 13431.2, 14041.5, 14677.3, 15340.3, 16032.2,
         16755.0, 17510.8, 18301.8, 19130.6, 20000.0]          # Source/Params.h reverbFilterTaper: the host's 0 ... 1 in 40 steps


def to_norm(hz):
    i = 0
    while i < 39 and TAPER[i + 1] < hz: i += 1
    return min(1.0, max(0.0, (i + (hz - TAPER[i]) / (TAPER[i + 1] - TAPER[i])) / 40.0))


def capture(x, hz, tag):
    lead = int(prc.LEAD * FS)
    xin = np.concatenate([np.zeros(lead, np.float32), np.asarray(x, np.float32)])
    fin = os.path.join(prc.REF, f'pfc_in_{tag}.f32'); xin.tofile(fin)
    out = os.path.join(prc.REF, f'pfc_{tag}')
    args = [prc.EXE, h.PLUGINS['ref'][0], h.PLUGINS['ref'][1], out, f'fs={FS}', 'record=1', f'in={fin}',
            f'state={os.path.join(prc.REF, "plate_clicked.state")}', 'Character State=0', 'EQ State=0', 'Doubler State=0',
            'Gain Rider State=0', 'Reverb State=1', 'Reverb Mix=1', f'Reverb Filter={to_norm(hz):.6f}']
    r = subprocess.run(args, capture_output=True, text=True, timeout=240)
    y = np.fromfile(out + '.pcm', np.float32).reshape(-1, 2).T
    os.remove(out + '.pcm'); os.remove(fin)
    return y[:, lead:], r.stdout[-300:]


def main():
    what, hz = sys.argv[1], float(sys.argv[2])
    if what == 'impulse':
        x = np.zeros(int(4.0 * FS), np.float32); x[0] = 0.5
        y, log = capture(x, hz, f'imp{int(hz)}')
        name = f'plate_filter_{int(hz)}' + ('_b' if os.path.exists(os.path.join(prc.REF, f'plate_filter_{int(hz)}.npy')) else '')
        np.save(os.path.join(prc.REF, name + '.npy'), y / 0.5)
    else:
        x = nl.noise(3.0, -18, seed=31); x = x[0] if np.ndim(x) == 2 else x
        y, log = capture(x, hz, f'noise{int(hz)}')
        name = f'plate_filter_noise_{int(hz)}'
        np.save(os.path.join(prc.REF, name + '.npy'), y)
    print(f'{name}: {y.shape[1] / FS:.2f} s, peak {20 * np.log10(np.max(np.abs(y)) + 1e-30):.1f} dBFS, rms {nl.rms_db(y):.1f} dBFS', flush=True)


if __name__ == '__main__':
    main()
