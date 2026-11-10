"""Doubler behaviour metric (MEASUREMENTS.md "Doubler"; a behaviour-metric stage): its wet signal
is not sample-exact (the voices hold more than a filtered, delayed copy of the input), so it is compared by what it does:
the long-term spectrum per third octave, the correlation between left and right, and the level, on pink noise and music
at full wet, for several Stereo settings. Writes renders/doubler_metric.json for NULLTESTS.md.

    python measure_doubler.py [tuning.json]      (a tuning file: constants to try on our processor)
"""
import json, os, sys
import numpy as np
import nulltest_lib as nl
import wr_ref as h

FS = 48000
THIRDS = 1000 * 2.0 ** (np.arange(-15, 14) / 3.0)        # 31.5 Hz ... 20 kHz


def bands(y):
    f = np.fft.rfftfreq(y.shape[-1], 1 / FS); P = np.abs(np.fft.rfft(y, axis=-1)) ** 2
    return np.array([10 * np.log10(P[..., (f >= c / 2 ** (1 / 6)) & (f < c * 2 ** (1 / 6))].sum() + 1e-30) for c in THIRDS])


def main():
    tune = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else None
    out = {}
    for sname, x in (('pink -18', nl.noise(6.0, -18, pink=True, seed=2)), ('music -10', nl.music(6.0, -10)[0])):
        for stereo in (0.0, 0.5, 1.0):
            j = dict(x=nl.stereo(np.asarray(x, np.float32)), norm=h.ONLY('DBL'), params={'Doubler Mix': 1.0, 'Doubler Stereo': stereo})
            r = h.render_many([j], 'ref', cache=True)[0][:, FS:]
            o = h.render_many([dict(j, tune=tune) if tune else j], 'model')[0][:, FS:]
            d = bands(o.sum(0)) - bands(r.sum(0))
            corr = lambda y: float(np.corrcoef(y[0], y[1])[0, 1])
            lev = lambda y: 10 * np.log10(np.mean(y ** 2))
            key = f'{sname}, Stereo {stereo:g}'
            out[key] = {'spectrum_max_db': round(float(np.max(np.abs(d))), 2), 'spectrum_rms_db': round(float(np.sqrt(np.mean(d ** 2))), 2),
                        'corr_ref': round(corr(r), 3), 'corr_ours': round(corr(o), 3), 'level_diff_db': round(float(lev(o) - lev(r)), 2)}
            print(key, out[key])
    if tune: return
    json.dump(out, open(os.path.join(h.PLUGIN, 'nulltest', 'renders', 'doubler_metric.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
