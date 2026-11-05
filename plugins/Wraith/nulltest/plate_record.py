"""The plate response, recorded with the reference's editor open (its script loads the plate; an offline host without
the editor keeps the room): tools/RefCapture record=1 with the plate state, an impulse in, every other stage off,
Mix 1 and Filter 20 kHz (MEASUREMENTS.md "Reverb"). Writes reference/Wraith/plate_<rate>.npy (2, n), the output
per unit impulse from the impulse on.

    python plate_record.py
"""
import os, subprocess
import numpy as np
import ts as h

REF = os.path.join(h.ROOT, 'reference', 'Wraith')
EXE = os.path.join(h.ROOT, 'build', 'RefCapture_artefacts', 'Release', 'RefCapture.exe')
LEAD = 6.0      # seconds of silence first: the plate loads asynchronously once the editor is open; three whole
                # periods of the doubler's 0.5 Hz modulation, so its voices start where an offline render's do


def record(fs, state, secs=3.5):
    AT = int(LEAD * fs)
    x = np.zeros(AT + int(fs * secs), np.float32); x[AT] = 0.5
    fin = os.path.join(REF, f'imp_{fs}.f32'); x.tofile(fin)
    out = os.path.join(REF, f'rec_{fs}')
    args = [EXE, h.PLUGINS['ref'][0], h.PLUGINS['ref'][1], out, f'fs={fs}', 'record=1', f'in={fin}', f'state={state}',
            'Character State=0', 'EQ State=0', 'Doubler State=0', 'Gain Rider State=0', 'Reverb State=1',
            'Reverb Mix=1', 'Reverb Filter=1']
    subprocess.run(args, capture_output=True, text=True, timeout=120)
    y = np.fromfile(out + '.pcm', np.float32).reshape(-1, 2).T
    os.remove(out + '.pcm'); os.remove(fin)
    return y[:, AT:] / 0.5


def db(a, b):
    return 20 * np.log10(np.sqrt(np.mean((a - b) ** 2)) / np.sqrt(np.mean(b ** 2)) + 1e-30)


def stable(fs, state, tries=5, secs=6.0):
    """records until two runs agree below -100 dB (the editor reloads responses at moments of its own)"""
    runs = []
    for _ in range(tries):
        y = record(fs, state, secs=secs)
        for r in runs:
            if db(y, r) < -100: return y, len(runs) + 1
        runs.append(y)
    return None, tries


if __name__ == '__main__':
    import probe_reverb as pr
    for fs in (44100, 48000, 88200, 96000):
        for name, st in (('room', os.path.join(REF, 'default.state')), ('plate', os.path.join(REF, 'plate_clicked.state'))):
            y, n = stable(fs, st, secs=2.6 if name == 'room' else 7.5)
            if y is None: print(fs, name, 'no two runs agreed'); continue
            nz = np.nonzero(np.abs(y).max(axis=0) > 1e-7)[0]
            msg = f'{fs} {name}: agreed after {n} runs, length {nz[-1] / fs:.3f} s, peak {np.abs(y).max():.4f}'
            if name == 'room':
                off = pr.render(fs, {'Reverb Mix': 1.0, 'Reverb Filter': 20000}, secs=6.5)[:, pr.AT:pr.AT + y.shape[1]]
                msg += f', against the offline render {db(y, off):.1f} dB'
            print(msg, flush=True)
            np.save(os.path.join(REF, f'{name}_rec_{fs}.npy'), y)
