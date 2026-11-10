"""The Focus EQ's shared pieces for fit_focus_eq.py and fit_allpass.py: the rate, the RBJ biquad, and the measured
response of the character stage at Focus -50 ... 50 (renders/focus_eq.npz, made by probe_char.py eqshape where the
stage's dynamics hold a constant gain: Compression -50, noise at -38 dBFS)."""
import os
import numpy as np

FS = 48000
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'renders', 'focus_eq.npz')


def load():
    """the measured responses (f, and one complex response per Focus value), measured first when missing"""
    if not os.path.exists(DATA):
        import probe_char as pc
        pc.eqshape(save=DATA)
    return np.load(DATA)


def biquad(kind, f, q, g=0.0):
    A = 10 ** (g / 40); w0 = 2 * np.pi * f / FS; c = np.cos(w0); s = np.sin(w0); al = s / (2 * q)
    if kind == 'pk':
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    elif kind == 'hp':
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == 'lp':
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2]; a = [1 + al, -2 * c, 1 - al]
    else:
        k = 2 * np.sqrt(A) * al
        if kind == 'ls':
            b = [A * ((A + 1) - (A - 1) * c + k), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - k)]
            a = [(A + 1) + (A - 1) * c + k, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - k]
        else:
            b = [A * ((A + 1) + (A - 1) * c + k), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - k)]
            a = [(A + 1) - (A - 1) * c + k, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - k]
    return np.array(b) / a[0], np.array(a) / a[0]
