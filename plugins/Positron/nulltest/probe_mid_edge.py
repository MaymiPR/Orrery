"""The mid band's nonlinear stage, as the reference applies it (probe_band_path.py mid / midlo, taken while ours had the plain
Linkwitz-Riley edge of ident.nl_firs): the complex ratio of the reference's path to ours, saved for ident.nl_firs.
With --null: the character-only nulls through charmodel_lib.py (the plug-in's laws) with the plain edge, the measured
upper side (ident.nl_firs) and both sides (the low side from xprobe_midlo.npz too, smoothed over five probes).

    python probe_mid_edge.py --save             measurements/Positron/character/mid_ratio.npz from xprobe_mid_plain.npz
(probe_band_path.py mid's output while the plug-in had the plain edge, renamed: with the measured path in the plug-in a new
probe_band_path.py run reads a ratio of 1)
    python probe_mid_edge.py --null"""
import os, sys
import numpy as np
import po_ref, ident_lib as I

D = os.path.join(po_ref.ROOT, 'measurements', 'Positron', 'character')


def probe_ratio(name):
    z = np.load(os.path.join(D, name))
    cr, co = z['ref_change'] / z['probe'], z['ours_change'] / z['probe']
    return z['f'], cr / co


if __name__ == '__main__':
    if '--save' in sys.argv:
        fh, rh = probe_ratio('xprobe_mid_plain.npz')
        np.savez(I.MID_RATIO, fh=fh, rh=rh / rh[0])
        print('saved', I.MID_RATIO)
    if '--null' in sys.argv:
        import nulltest as N, charmodel_lib as CM
        from measure_high_gain_noise import header_laws
        plain = I.nl_firs(ratio=False)[1]
        upper = I.nl_firs()[1]
        nf = 1 << 16; f = np.fft.rfftfreq(nf, 1 / po_ref.FS)
        fl, rl = probe_ratio('xprobe_midlo.npz'); rl = rl / rl[-1]
        sm = lambda v: np.convolve(np.pad(v, 2, mode='edge'), np.ones(5) / 5, 'valid')
        lm, lph = sm(20 * np.log10(np.abs(rl))), sm(np.unwrap(np.angle(rl)))
        lo = f <= fl[-1]; R = np.ones(len(f), complex)
        R[lo] = 10 ** (np.interp(np.log(np.maximum(f[lo], 1)), np.log(fl), lm - lm[-1]) / 20) * np.exp(1j * np.interp(np.log(np.maximum(f[lo], 1)), np.log(fl), lph - lph[-1]))
        R[0] = abs(R[0])
        both = np.fft.irfft(np.fft.rfft(upper, nf) * R, nf)[:1024]
        cases = [c for c in N.CASES if c[0].startswith('char')]
        sigs = {k: fn() for k, fn in N.SIGNALS.items()}
        pad = lambda x: np.concatenate([np.zeros((2, N.PRE) if x.ndim == 2 else N.PRE, np.float32), x], axis=-1)
        st = lambda x: np.vstack([x, x]) if x.ndim == 1 else x
        print(f'{"":45s} {"plain":>8s} {"upper":>8s} {"both":>8s}')
        for name, s, nm, pm in cases:
            amt = nm.get('Character', 0.5)
            x = st(pad(sigs[s])); ref = po_ref.render_many([dict(x=pad(sigs[s]), norm=nm, params=pm, raw=True)], 'ref', cache=True)[0]
            laws = header_laws(int(round(amt * 16)))
            row = []
            for h in (plain, upper, both):
                I.NL_IRS[1] = h
                row.append(N.residual_db(ref, CM.render(x, amt * 8, laws)))
            print(f'{name:45s} ' + ' '.join(f'{v:8.2f}' for v in row))
