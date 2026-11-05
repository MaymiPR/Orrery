"""The plate against the reference (MEASUREMENTS.md "Reverb"): the reference only plays the plate with its editor open,
so its side is recorded through tools/RefCapture record=1 (plate_record.py); ours through WrRender.

    python null_plate.py
"""
import os, subprocess
import numpy as np
import nulltest_lib as nl
import ts as h
import plate_record as prc


def ref_plate(x, fs, params, state=None):
    """x (mono) through the reference with its editor open; state: a saved state (default: the plate selected)"""
    lead = int(prc.LEAD * fs)
    x = x[0] if x.ndim == 2 else x
    xin = np.concatenate([np.zeros(lead, np.float32), x.astype(np.float32)])
    fin = os.path.join(prc.REF, f'in_{fs}.f32'); xin.tofile(fin)
    out = os.path.join(prc.REF, f'np_{fs}')
    args = [prc.EXE, h.PLUGINS['ref'][0], h.PLUGINS['ref'][1], out, f'fs={fs}', 'record=1', f'in={fin}',
            f'state={state or os.path.join(prc.REF, "plate_clicked.state")}']
    if state is None:
        args += ['Character State=0', 'EQ State=0', 'Doubler State=0', 'Gain Rider State=0', 'Reverb State=1']
    args += [f'{k}={v}' for k, v in params.items()]
    subprocess.run(args, capture_output=True, text=True, timeout=180)
    y = np.fromfile(out + '.pcm', np.float32).reshape(-1, 2).T
    os.remove(out + '.pcm'); os.remove(fin)
    return y[:, lead:]


if __name__ == '__main__':
    fs = 48000
    for label, x, norm in (('noise, mix 1, filter 20k', nl.noise(3.0, -18), {'Reverb Mix': 1.0, 'Reverb Filter': 1.0}),
                           ('music, mix 0.31 (n), filter 0.5 (n)', nl.music(3.0, -12), {'Reverb Mix': 0.3077, 'Reverb Filter': 0.5})):
        r = ref_plate(x, fs, norm)
        x = x[0] if x.ndim == 2 else x
        o = h.render(nl.stereo(x), 'model', fs=fs, norm=dict(h.ONLY('REV'), **norm, **{'Reverb Type': 1.0}))
        print(f'{label:40s} {nl.residual_db(r[:, fs // 10:], o[:, fs // 10:]):7.1f} dB')
