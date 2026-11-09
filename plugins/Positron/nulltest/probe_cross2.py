"""What a band's gain is applied to: quiet probe tones (-50 dBFS, too quiet to move any detector) under a loud masker
inside the band. The masker lowers the band's gain (and the shaper's slope) for everything that passes the band's
nonlinear stage, so the probes' complex change, masked minus alone, traces the response of that stage's path:
  change(f) = c * A(f),  c from the band's middle.
Ours applies it through ident.nl_firs (MEASUREMENTS.md 3.11); the reference's A(f) is read here.

    python probe_cross2.py mid [amount 0..1] [masker dBFS] [--fs 44100]
writes measurements/Positron/character/xprobe_<setup>[_<fs>].npz"""
import os, sys
import numpy as np
from scipy.signal import butter, sosfiltfilt
import tgp, ident as I

FS = tgp.FS; PRE = 2 * FS; SECS = 4
# per probe: the band whose gain the masker lowers, the masker's band, the probe frequencies, the probe to normalise at
SETUPS = {'mid': ('mid', (250.0, 700.0), np.geomspace(900, 18000, 60), 0),         # the mid band's upper side
          'midlo': ('mid', (900.0, 2000.0), np.geomspace(30, 700, 48), -1),         # its lower side
          'high': ('high', (6000.0, 12000.0), np.geomspace(300, 5000, 48), -1),     # the high band's lower side
          'low': ('low', (30.0, 70.0), np.geomspace(90, 3000, 48), 0)}              # the low band's upper side


def lockin(y, f, a, b):
    t = np.arange(a, b) / FS      # FS: the render rate (--fs)
    return 2 * np.mean(y[a:b] * np.exp(-2j * np.pi * f * t))


def response(h, f):
    """frequency response of an FIR at f (Hz)"""
    return np.array([np.sum(h * np.exp(-2j * np.pi * fi * np.arange(len(h)) / FS)) for fi in f])


if __name__ == '__main__':
    if '--fs' in sys.argv:
        i = sys.argv.index('--fs'); FS = int(sys.argv[i + 1]); PRE = 2 * FS; del sys.argv[i:i + 2]
    setup = sys.argv[1]; band, mask, fr, k0 = SETUPS[setup]; amt = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    L = float(sys.argv[3]) if len(sys.argv) > 3 else -6.0
    n = PRE + SECS * FS; t = np.arange(n) / FS
    m = sosfiltfilt(butter(6, mask, 'band', fs=FS, output='sos'), tgp.noise(n / FS, 0, fs=FS, seed=7, pink=True))
    m *= 10 ** (L / 20) / np.sqrt(np.mean(m ** 2))
    groups = [fr[i::6] for i in range(6)]
    phases = np.random.default_rng(1).uniform(0, 2 * np.pi, len(fr))
    # the masker alone too: its own components and harmonics at the probe frequencies are taken off
    jobs = [dict(x=m.astype(np.float32), norm={**tgp.CHAR_ONLY, 'Character': amt}, raw=True)]
    for g in groups:
        p = sum(10 ** (-50 / 20) * np.sin(2 * np.pi * f * t + phases[list(fr).index(f)]) for f in g)
        for withm in (0, 1):
            jobs.append(dict(x=(p + withm * m).astype(np.float32), norm={**tgp.CHAR_ONLY, 'Character': amt}, raw=True))
    r = tgp.render_many(jobs, 'ref', fs=FS, cache=True); o = tgp.render_many(jobs, 'model', fs=FS)
    a, b = PRE + FS // 2, n
    out = {}
    for who, ys in (('ref', r), ('ours', o)):
        ch, al = np.zeros(len(fr), complex), np.zeros(len(fr), complex)
        for gi, g in enumerate(groups):
            for f in g:
                i = list(fr).index(f)
                al[i] = lockin(ys[1 + 2 * gi][0], f, a, b)
                ch[i] = lockin(ys[2 + 2 * gi][0] - ys[0][0], f, a, b) - al[i]
        out[who] = (al, ch)
    bi = ['low', 'mid', 'high'].index(band)
    Hnl = response(I.NL_IRS[bi], fr) if FS == 48000 else np.ones(len(fr))
    pr = 10 ** (-50 / 20) * np.exp(1j * (phases - np.pi / 2))      # the probe's own phasor (sin)
    np.savez(os.path.join(tgp.ROOT, 'measurements', 'Positron', 'character', f'xprobe_{setup}' + ('' if FS == 48000 else f'_{FS}') + ('' if amt == 0.5 else f'_a{amt}') + '.npz'), f=fr, ref_alone=out['ref'][0], ref_change=out['ref'][1],
             ours_alone=out['ours'][0], ours_change=out['ours'][1], probe=pr, Hnl=Hnl)
    # the change re the probe, normalised by the ours-path at the first probe
    cr, co = out['ref'][1] / pr, out['ours'][1] / pr
    sr, so = cr / (Hnl[k0] * cr[k0] / Hnl[k0]) * Hnl[k0], co / co[k0] * Hnl[k0]
    print(f'{setup} {amt * 200:.0f}% masker {L:+.0f} dBFS: change re probe, scaled so ours = nl path at {fr[k0]:.0f} Hz')
    print('    Hz     |nl| dB   ours dB   ref dB    ref-ours dB   ref phase-ours (deg)')
    for i, f in enumerate(fr):
        print(f'{f:8.0f}  {20 * np.log10(abs(Hnl[i])):8.2f}  {20 * np.log10(abs(so[i])):8.2f}  {20 * np.log10(abs(sr[i]) + 1e-12):8.2f}  '
              f'{20 * np.log10(abs(sr[i]) / abs(so[i]) + 1e-12):8.2f}   {np.degrees(np.angle(sr[i] / so[i])):8.1f}')
