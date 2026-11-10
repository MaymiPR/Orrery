"""How the EQ moves when a gain jumps (MEASUREMENTS.md "Smoothing"): the reference with a shelf gain automated at a
block boundary, against simulations of candidate filter structures (direct form I, transposed direct form II, the
state-variable filter) and ramps (linear in dB or in amplitude, over L ms). The steady states are identical; only the
first milliseconds after the jump tell the structures apart.

    python fit_eq_motion.py
"""
import numpy as np
import nulltest_lib as nl
import wr_ref as h

FS = 48000
AT = 47 * 512
START = AT - 12000          # simulate from here (the filters have long settled)
STOP = AT + 4800


def rbj(f0, q, g, low):
    A = 10 ** (g / 40); w0 = 2 * np.pi * f0 / FS; c = np.cos(w0); k = 2 * np.sqrt(A) * np.sin(w0) / (2 * q)
    if low:
        b = [A * ((A + 1) - (A - 1) * c + k), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - k)]
        a = [(A + 1) + (A - 1) * c + k, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - k]
    else:
        b = [A * ((A + 1) + (A - 1) * c + k), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - k)]
        a = [(A + 1) - (A - 1) * c + k, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - k]
    return [v / a[0] for v in b], [1.0, a[1] / a[0], a[2] / a[0]]


def svf_coefs(f0, q, g, low):
    A = 10 ** (g / 40); k = 1 / q
    gg = np.tan(np.pi * f0 / FS) / np.sqrt(A) if low else np.tan(np.pi * f0 / FS) * np.sqrt(A)
    a1 = 1 / (1 + gg * (gg + k)); a2 = gg * a1; a3 = gg * a2
    m = (1.0, k * (A - 1), A * A - 1) if low else (A * A, k * (1 - A) * A, 1 - A * A)
    return a1, a2, a3, m


def run(x, gains, f0, q, low, structure):
    y = np.zeros_like(x)
    if structure == 'svf':
        ic1 = ic2 = 0.0
        for i in range(len(x)):
            a1, a2, a3, m = svf_coefs(f0, q, gains[i], low)
            v3 = x[i] - ic2; v1 = a1 * ic1 + a2 * v3; v2 = ic2 + a2 * ic1 + a3 * v3
            ic1 = 2 * v1 - ic1; ic2 = 2 * v2 - ic2
            y[i] = m[0] * x[i] + m[1] * v1 + m[2] * v2
        return y
    x1 = x2 = y1 = y2 = z1 = z2 = 0.0
    last = None
    for i in range(len(x)):
        if gains[i] != last: b, a = rbj(f0, q, gains[i], low); last = gains[i]
        if structure == 'df2':
            w = x[i] - a[1] * x1 - a[2] * x2          # x1, x2 hold the canonical form's state
            out = b[0] * w + b[1] * x1 + b[2] * x2
            x2, x1 = x1, w
        elif structure == 'df1':
            out = b[0] * x[i] + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
            x2, x1, y2, y1 = x1, x[i], y1, out
        else:
            out = b[0] * x[i] + z1; z1 = b[1] * x[i] - a[1] * out + z2; z2 = b[2] * x[i] - a[2] * out
        y[i] = out
    return y


def ramp(g0, g1, ms, domain):
    n = STOP - START; out = np.full(n, float(g1))
    L = max(1, int(round(ms * FS / 1000)))
    j = np.arange(1, L + 1) / L
    k0 = AT - START
    out[:k0] = g0
    if domain == 'db':
        seg = g0 + (g1 - g0) * j
    else:
        a0, a1 = 10 ** (g0 / 40), 10 ** (g1 / 40); seg = 40 * np.log10(a0 + (a1 - a0) * j)
    out[k0:k0 + L] = seg[:max(0, min(L, n - k0))]
    return out


def main():
    x = nl.stereo(nl.noise(1.5, -18.0)).astype(np.float32)
    for label, pname, to_norm, g0, g1, f0, low in (('low 4.0975 -> -12', 'EQ Low Gain', 0.0, 4.0975, -12.0, 200.0, True),
                                                  ('high 0.0336 -> +12', 'EQ High Gain', 1.0, 0.0336, 12.0, 5000.0, False)):
        ref = h.render_many([dict(x=x, norm=h.ONLY('EQ'), auto=[(pname, AT, to_norm)])], 'ref', cache=True)[0]
        # the other shelf keeps the preset value: take it out of the reference by its exact inverse is not needed,
        # since both run in series and are linear: simulate both
        other_f0, other_g, other_low = (5000.0, 0.0336, False) if low else (200.0, 4.0975, True)
        xs = x[0, START:STOP].astype(np.float64)
        pre = run(xs, np.full(len(xs), other_g), other_f0, 0.7, other_low, 'tdf2')
        target = ref[0, START:STOP]
        print(label)
        for structure in ('tdf2', 'df1', 'df2', 'svf'):
            for domain in ('db', 'amp'):
                best = None
                for ms in (0.0, 1.0, 2.0, 2.667, 3.0, 4.0, 5.0, 5.333, 6.0, 8.0, 10.0):
                    y = run(pre, ramp(g0, g1, ms, domain), f0, 0.7, low, structure)
                    r = nl.residual_db(target[AT - START:], y[AT - START:])
                    if best is None or r < best[0]: best = (r, ms)
                print(f'   {structure:5s} {domain:4s}: best {best[0]:7.1f} dB at {best[1]} ms')


if __name__ == '__main__':
    main()
