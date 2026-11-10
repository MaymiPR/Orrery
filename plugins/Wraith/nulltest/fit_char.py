"""Character stage, the dynamics (MEASUREMENTS.md "Character"): the expander and compressor constants of
Source/dsp/Character.h fitted with CMA-ES on the energy-weighted null against the reference (stage alone), on tones,
noise bursts, music and drums together; a held-out set is reported beside it. The whole population of a generation
renders in one WrRender run.

    python fit_char.py [--iters 120] [--out renders/char_fit.json] [--start renders/char_fit.json]
    python fit_char.py --eval [--start renders/char_fit.json]     the training and held-out nulls of a constant set
"""
import argparse, json, os, sys, time
import numpy as np
import nulltest_lib as nl
import wr_ref as h

FS = 48000
# name, start, low, high, log scale
PARAMS = [('expThresholdDb', -40.0, -70.0, -20.0, False), ('expRatio', 2.2, 1.0, 6.0, False), ('expKneeDb', 6.0, 0.0, 30.0, False),
          ('expAttackMs', 5.0, 0.05, 200.0, True), ('expReleaseMs', 50.0, 1.0, 2000.0, True),
          ('cmpThresholdDb', -16.0, -40.0, 0.0, False), ('cmpRatio', 16.0, 1.2, 100.0, True), ('cmpKneeDb', 8.0, 0.0, 30.0, False),
          ('cmpAttackMs', 1.5, 0.02, 50.0, True), ('cmpReleaseLowMs', 50.0, 1.0, 2000.0, True), ('cmpReleaseHighMs', 50.0, 1.0, 2000.0, True),
          ('cmpReleaseSwitchDb', 6.0, 0.0, 40.0, False), ('cmpMakeupDb', 0.0, -6.0, 6.0, False),
          ('clipDrive', 0.05, 0.01, 4.0, True)]
# a peak detector (noise is compressed ~5 dB harder than a tone of the same RMS); the Focus EQ's high-passes and its
# three lowest peaks after the dynamics (the 150 Hz ceiling sits 1.5 dB under 1 kHz's)
FIXED = {'detRmsMs': 0.0, 'charPostMask': float(1 | 2 | (1 << 11) | (1 << 13) | (1 << 14))}


def cases():
    lv = list(np.arange(-60.0, 1.0, 4.0))
    st = lambda f: nl.stereo(nl.steps(lv, 0.25, f=f)).astype(np.float32)
    bursts = np.concatenate([nl.noise(0.5, -40 if k % 2 == 0 else -12, seed=k) for k in range(6)])
    train = [('stairs 1k c-50', st(1000), -50, 0), ('stairs 1k c0', st(1000), 0, 0), ('stairs 1k c50', st(1000), 50, 0),
             ('stairs 150 c0', st(150), 0, 0), ('stairs 5k c0', st(5000), 0, 0),
             ('bursts c0', nl.stereo(bursts).astype(np.float32), 0, 0),
             ('music c0 f8', nl.stereo(nl.music(4.0, -10)).astype(np.float32), 0, 8),
             ('music c50', nl.stereo(nl.music(4.0, -16, seed=7)).astype(np.float32), 50, 0),
             ('drums c0', nl.stereo(nl.drums(3.0, -6)).astype(np.float32), 0, 0)]
    held = [('music c25 f-30', nl.stereo(nl.music(4.0, -12, seed=11)).astype(np.float32), 25, -30),
            ('pink c-25', nl.stereo(nl.pink(3.0, -20, seed=4)).astype(np.float32), -25, 0),
            ('drums c50 f20', nl.stereo(nl.drums(3.0, -10, seed=9)).astype(np.float32), 50, 20)]
    return train, held


def jobs_of(cs):
    return [dict(x=x, norm=h.ONLY('CHAR'), params={'Compression': c, 'Focus': fo}) for _, x, c, fo in cs]


def to_tune(z, params=None, fixed=None):
    params = params or PARAMS
    t = dict(FIXED if fixed is None else fixed)
    for (name, _, lo, hi, lg), v in zip(params, z):
        v = float(np.clip(v, 0, 1))
        t[name] = float(np.exp(np.log(lo) + v * (np.log(hi) - np.log(lo)))) if lg else lo + v * (hi - lo)
    return t


def from_tune(t, params=None):
    z = []
    for name, start, lo, hi, lg in params or PARAMS:
        v = t.get(name, start)
        z.append((np.log(v) - np.log(lo)) / (np.log(hi) - np.log(lo)) if lg else (v - lo) / (hi - lo))
    return np.array(z)


def score(refs, outs):
    """half the energy-weighted null, half the mean of the 50 ms windows' nulls (so quiet passages count too)"""
    skip, w = int(0.05 * FS), int(0.05 * FS)
    out = []
    for r, o in zip(refs, outs):
        r, o = r[:, skip:], o[:, skip:]
        win = [nl.residual_db(r[:, i:i + w], o[:, i:i + w]) for i in range(0, r.shape[1] - w, w)
               if np.sqrt(np.mean(r[:, i:i + w] ** 2)) > 1e-5]
        out.append(0.5 * nl.residual_db_weighted(r, o) + 0.5 * float(np.mean(np.minimum(win, 0))))
    return out


def evaluate(tunes, jobs, refs):
    alljobs = [dict(j, tune=t) for t in tunes for j in jobs]
    outs = h.render_many(alljobs, 'model')
    n = len(jobs)
    return [score(refs, outs[k * n:(k + 1) * n]) for k in range(len(tunes))]


def run_cma(z0, tj, tref, iters, sigma, out, params=None, fixed=None):
    """CMA-ES over normalised parameters (0 ... 1); writes the best tuning to out after every improvement"""
    params = params or PARAMS
    n = len(z0); lam = 4 + int(3 * np.log(n)) + 4; mu = lam // 2
    w = np.log(mu + 0.5) - np.log(np.arange(1, mu + 1)); w /= w.sum(); mueff = 1 / np.sum(w ** 2)
    cc = (4 + mueff / n) / (n + 4 + 2 * mueff / n); cs = (mueff + 2) / (n + mueff + 5)
    c1 = 2 / ((n + 1.3) ** 2 + mueff); cmu = min(1 - c1, 2 * (mueff - 2 + 1 / mueff) / ((n + 2) ** 2 + mueff))
    ds = 1 + 2 * max(0, np.sqrt((mueff - 1) / (n + 1)) - 1) + cs; chiN = np.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n))
    m = np.clip(z0, 0, 1); s = sigma; C = np.eye(n); pc = np.zeros(n); ps = np.zeros(n)
    rng = np.random.default_rng(0)
    best = (None, np.inf)
    t0 = time.time()
    print(f'{n} parameters, population {lam}', flush=True)
    for g in range(iters):
        D, B = np.linalg.eigh(C); D = np.sqrt(np.maximum(D, 1e-20))
        ys = rng.standard_normal((lam, n)) * D @ B.T; xs = np.clip(m + s * ys, 0, 1); ys = (xs - m) / s
        res = evaluate([to_tune(x, params, fixed) for x in xs], tj, tref)
        fs = np.array([np.mean(r) for r in res]); idx = np.argsort(fs)
        if fs[idx[0]] < best[1]:
            best = (xs[idx[0]].copy(), fs[idx[0]])
            json.dump(to_tune(best[0], params, fixed), open(out, 'w'), indent=1)
        ym = w @ ys[idx[:mu]]; m = m + s * ym
        Ci = B @ np.diag(1 / D) @ B.T
        ps = (1 - cs) * ps + np.sqrt(cs * (2 - cs) * mueff) * (Ci @ ym)
        hs = np.linalg.norm(ps) / np.sqrt(1 - (1 - cs) ** (2 * (g + 1))) / chiN < 1.4 + 2 / (n + 1)
        pc = (1 - cc) * pc + hs * np.sqrt(cc * (2 - cc) * mueff) * ym
        C = (1 - c1 - cmu) * C + c1 * (np.outer(pc, pc) + (1 - hs) * cc * (2 - cc) * C) + cmu * sum(wi * np.outer(y, y) for wi, y in zip(w, ys[idx[:mu]]))
        s *= np.exp((cs / ds) * (np.linalg.norm(ps) / chiN - 1))
        print(f'gen {g + 1:3d}: best {best[1]:7.2f} dB  this gen {fs[idx[0]]:7.2f}  sigma {s:.4f}  {time.time() - t0:5.0f} s', flush=True)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--iters', type=int, default=120)
    ap.add_argument('--out', default=os.path.join(h.PLUGIN, 'nulltest', 'renders', 'char_fit.json'))
    ap.add_argument('--start', default=None)
    ap.add_argument('--eval', action='store_true')
    ap.add_argument('--sigma', type=float, default=0.15)
    a = ap.parse_args()
    train, held = cases()
    tj, hj = jobs_of(train), jobs_of(held)
    tref = h.render_many(tj, 'ref', cache=True); href = h.render_many(hj, 'ref', cache=True)
    start = json.load(open(a.start)) if a.start else {}
    if a.eval:
        t = {k: start.get(k, s) for k, s, *_ in PARAMS}
        for label, cs, jb, rf in (('train', train, tj, tref), ('held-out', held, hj, href)):
            res = evaluate([t], jb, rf)[0]
            for (name, *_), r in zip(cs, res): print(f'{label:8s} {name:18s} {r:7.1f} dB')
        return
    best = run_cma(from_tune(start), tj, tref, a.iters, a.sigma, a.out)
    t = to_tune(best[0])
    print(json.dumps(t, indent=1))
    hres = evaluate([t], hj, href)[0]
    for (name, *_), r in zip(held, hres): print(f'held-out {name:18s} {r:7.1f} dB')


if __name__ == '__main__':
    main()
