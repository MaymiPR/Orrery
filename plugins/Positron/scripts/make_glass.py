"""Draws the visualiser's glass (resources/glass/glass_off.png and glass_lit.png) from the description in
glass_params.json next to this script. Every part is drawn here, with our own shading:

- the rim and sheen lines along the track: each a thin ridge at a measured radius and width, with a base level and a
  few soft highlights along the track (station, spread in stations, peak grey);
- the reflections: soft-edged bands between an inner and an outer edge. Each edge is one or more cubic curves r(s) over
  a station range, a Bezier whose control points sit a third and two thirds of the way along, so four radii describe a
  piece: [first station, last station, r0, r1, r2, r3]. Where the two edges start or end at the same radius the band
  closes to a tip; an "inner_cut" piece ends the band with a slanted cut that bounds it without changing its shading.
  Edge softness is set in field rows and counts a station as one row, so steep edges stay smooth. Our shading: a highlight across the band (its position from the inner edge to the outer, which is
  the shading direction, its spread, and a floor under it) times a profile along it (a quick rise from the start, a
  gentle quadratic fall, an optional fade before the end), in the band's measured peak colour;
- for the lit glass, the light of the sparks: coloured vertical streaks from our own seeded noise, fading outwards
  along an exponential falloff over a floor (half strength at the pill's edge) and held back by the reflections.

The positions, sizes and colours in glass_params.json are measurements rounded to tokens (radii to 0.5 px, stations to
0.5, colours to whole grey levels); the curves and the shading formulas are ours.

The layout is the plug-in's (Source/ui/Visualizer.cpp GlassField): x = station around the racetrack (25 per straight,
144 per curved end, 338 in all: the top straight from station 0, the right end from 25, the bottom straight from 169,
the left end from 194), y = radius 52 ... 114 design px in 0.5 px steps (125 rows), RGB.

    python plugins/Positron/scripts/make_glass.py
        writes both PNGs from glass_params.json
    python plugins/Positron/scripts/make_glass.py --measure off.png [lit.png]
        measuring only: prints, for a field image in the layout above, each bright region's start and end stations,
        its edges at a few stations, its peak colour and where its highlight sits, the lines' levels, and with a lit
        field the light's radial falloff; numbers to round into tokens by hand. It never writes glass_params.json or
        the PNGs."""
import json, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'resources', 'glass')
PARAMS = os.path.join(HERE, 'glass_params.json')
NS, NR, CELL = 338, 125, 0.5                            # stations, rows, px per row
ST = np.arange(NS) + 0.0
RAD = 52.0 + CELL * np.arange(NR)
S, R = np.meshgrid(ST, RAD)


def smooth(x):
    """0 ... 1 over x = -1 ... 1 (smoothstep)"""
    t = np.clip(0.5 + 0.5 * x, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def edge(pieces, s):
    """an edge's radius and its slope (px per station) at stations s, from cubic Bernstein pieces
    [s0, s1, r0, r1, r2, r3]; held at the end values beyond the edge's stations"""
    r_out, d_out = np.zeros(np.shape(s)), np.zeros(np.shape(s))
    for i, (s0, s1, *rk) in enumerate(pieces):
        t = np.clip((s - s0) / (s1 - s0), 0, 1)
        r = (1 - t) ** 3 * rk[0] + 3 * (1 - t) ** 2 * t * rk[1] + 3 * (1 - t) * t ** 2 * rk[2] + t ** 3 * rk[3]
        d = 3 * ((1 - t) ** 2 * (rk[1] - rk[0]) + 2 * (1 - t) * t * (rk[2] - rk[1]) + t ** 2 * (rk[3] - rk[2])) / (s1 - s0)
        on = s >= s0 if i else np.ones(np.shape(s), bool)
        r_out, d_out = np.where(on, r, r_out), np.where(on, d, d_out)
    return r_out, d_out


def span(pieces):
    return min(p[0] for p in pieces), max(p[1] for p in pieces)


def band(sh):
    """a reflection's coverage (0 ... 1, soft edges) and its colour"""
    soft = sh['soft']; soft_along = sh.get('soft_along', soft)     # edge softness in rows of px: across, at the ends
    inner_all = sh['inner'] + sh.get('inner_cut', [])
    lo = max(span(inner_all)[0], span(sh['outer'])[0]); hi = min(span(inner_all)[1], span(sh['outer'])[1])
    (rin, din), (rout, dout) = edge(sh['inner'], ST[None, :]), edge(sh['outer'], ST[None, :])
    # the inner edge's end cut (if any) bounds the band but leaves its shading alone
    (rcut, dcut) = edge(inner_all, ST[None, :])
    # distances square to each edge, measured in field cells (a station counts as one 0.5 px row), so a steep edge is
    # as soft across the stations as a flat one is across the rows and stays smooth when the plug-in interpolates it
    tilt_in, tilt_out = np.sqrt(1 + (dcut / CELL) ** 2), np.sqrt(1 + (dout / CELL) ** 2)
    cov = (smooth((R - rcut) / tilt_in / soft) * smooth((rout - R) / tilt_out / soft)
           * smooth((S - lo) * CELL / soft_along) * smooth((hi - S) * CELL / soft_along))
    # our shading: across the band a highlight over a floor, along it a rise, a quadratic fall and a fade at the end
    sd = sh['shade']
    u = np.clip((R - rin) / np.maximum(rout - rin, 1e-6), 0, 1)
    across = sd['floor'] + (1 - sd['floor']) * np.exp(-0.5 * ((u - sd['highlight']) / sd['spread']) ** 2)
    def along(v):
        a = (1 - np.exp(-v / sd['rise'])) if sd['rise'] > 0 else np.ones_like(v)
        a = a * (1 - sd['fall'] * v * v)
        if sd['fade'] > 0: a = a * (1 - np.exp(-(1 - v) / sd['fade']))
        return a
    v = np.clip((S - lo) / (hi - lo), 0, 1)
    shade = along(v) / along(np.linspace(0, 1, 1001)).max()
    col = (across * shade)[..., None] * np.asarray(sh['colour'], float)
    return cov, col


def line_profile(ln):
    p = np.full(NS, float(ln['level']))
    for c, w, peak in ln['highlights']:
        d = (ST - c + NS / 2) % NS - NS / 2                   # around the track: the profile wraps
        p += peak * np.exp(-0.5 * (d / w) ** 2)
    return p


def falloff(L):
    """the sparks' light against radius: an exponential over a floor, eased in from `edge` of its strength at the pill's
    edge (r0) over `ramp` px"""
    f = L['falloff']
    ramp = f['edge'] + (1 - f['edge']) * smooth((R - f['r0']) / f['ramp'] * 2 - 1)
    return ramp * (f['floor'] + f['amp'] * np.exp(-(R - f['r0'] - f['ramp']) / f['length']))


def draw(P, lit=False, seed=7):
    img = np.zeros((NR, NS, 3)) + np.asarray(P['base'], float)
    for ln in P['lines']:
        ridge = np.exp(-0.5 * ((R - ln['r']) / ln['width']) ** 2)
        img += (ridge * line_profile(ln)[None, :])[..., None]
    hold = np.zeros(S.shape)
    for sh in P['reflections']:
        cov, col = band(sh)
        img = img * (1 - cov[..., None]) + col * cov[..., None]
        hold = np.maximum(hold, cov * sh['hold'])
    if lit:
        L = P['light']
        rng = np.random.default_rng(seed)
        def smooth_noise(widths, count):                 # zero-mean, unit-sd periodic noise made of soft bumps
            v = np.zeros(NS)
            for _ in range(count):
                c = rng.uniform(0, NS); w = rng.uniform(*widths)
                v += rng.normal() * np.exp(-0.5 * (((ST - c + NS / 2) % NS - NS / 2) / w) ** 2)
            v -= v.mean(); return v / v.std()
        bright = 1 + L['contrast'] * smooth_noise(L['widths'], 160) + L['fine'] * smooth_noise(L['fine_widths'], 400)
        hue = np.stack([L['colour'] * smooth_noise(L['widths'], 160) for _ in range(3)], 1)
        hue -= hue.mean(1, keepdims=True)                # colour shifts that leave the brightness alone
        streak = np.asarray(L['tint'])[None, :] * (bright[:, None] + hue)
        img += (falloff(L) * (1 - hold))[..., None] * streak[None, :, :]
    return np.clip(img, 0, 255)


# where --measure looks for each bright region: stations, radii
WINDOWS = {'stroke': ((112, 172), (79, 101)), 'lower': ((192, 292), (88.6, 108)), 'upper': ((226, 276), (79, 92.2)),
           'cap': ((229, 276), (71.6, 76.0))}


def measure(off_path, lit_path=None):
    A = np.asarray(Image.open(off_path).convert('RGB')).astype(float); g = A.mean(2)
    for name, ((s0, s1), (ra, rb)) in WINDOWS.items():
        rows = np.where((RAD >= ra) & (RAD <= rb))[0]
        top = max(g[rows, s].max() for s in range(s0, s1 + 1))
        found = []
        for s in range(s0, s1 + 1):
            col = g[rows, s]; j = int(np.argmax(col)); half = 0.5 * col[j]
            if col[j] < 0.1 * top: continue
            a, b = j, j
            while a > 0 and col[a - 1] >= half: a -= 1
            while b < len(col) - 1 and col[b + 1] >= half: b += 1
            found.append((s, RAD[rows[a]], RAD[rows[b]], RAD[rows[j]], A[rows[j], s]))
        st = [f[0] for f in found]
        print(f'{name}: stations {st[0]} ... {st[-1]}, peak colour {np.round(max(found, key=lambda f: f[4].mean())[4]).astype(int).tolist()}')
        for f in found[::max(1, len(found) // 6)]:
            u = (f[3] - f[1]) / max(f[2] - f[1], 1e-6)
            print(f'   station {f[0]}: half-maximum edges r {f[1]:.1f} ... {f[2]:.1f}, highlight at {u:.2f} across')
    busy = np.zeros(g.shape, bool)
    for (s0, s1), (ra, rb) in WINDOWS.values():
        busy |= (S >= s0) & (S <= s1) & (R >= ra) & (R <= rb)
    for r0 in (71.5, 73.3, 74.6, 75.6, 76.5, 77.6, 78.6, 111.9):
        j = int(np.argmin(np.abs(RAD - r0))); prof = np.where(busy[j], np.nan, g[j])
        print(f'line r {r0}: level {np.nanmedian(prof):.1f}, brightest {np.nanmax(prof):.0f} at station {int(np.nanargmax(prof))}')
    if lit_path:
        B = np.asarray(Image.open(lit_path).convert('RGB')).astype(float)
        d = (B - A).mean(2)
        print('light against radius (lit - unlit, median per 4 px):',
              ' '.join(f'{float(np.median(d[np.abs(RAD - r) <= 1.0][:, :190])):.0f}' for r in np.arange(52, 114.1, 4)))


def save_png(img, path):
    Image.fromarray(np.round(img).astype(np.uint8)).save(path)


if __name__ == '__main__':
    if '--measure' in sys.argv:
        i = sys.argv.index('--measure'); args = sys.argv[i + 1:]
        measure(args[0], args[1] if len(args) > 1 else None)
        sys.exit(0)
    P = json.load(open(PARAMS))
    os.makedirs(OUT, exist_ok=True)
    save_png(draw(P), os.path.join(OUT, 'glass_off.png'))
    save_png(draw(P, lit=True), os.path.join(OUT, 'glass_lit.png'))
    print('wrote', os.path.normpath(os.path.join(OUT, 'glass_off.png')), 'and glass_lit.png')
