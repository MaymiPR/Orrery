"""What limits the plate presets' nulls (MEASUREMENTS.md "Presets"). The reference plays its plate only
with its editor open (cached captures, nulltest.plate_ref), but with the reverb switched off a preset renders offline
from its saved state like any other: so the chain in front of the reverb is nulled on its own (the preset's state with
the reverb off, both sides), beside the whole preset; and each stage in front alone with the preset's values, to see
which of them sets the chain's null.

    python probe_plate_presets.py ["big cave" "wide and wet" ...]
"""
import os, sys
import numpy as np
import nulltest as nt, nulltest_lib as nl, wr_ref as h

FS = 48000


def main():
    names = sys.argv[1:] or ['big cave', 'wide and wet']
    cases = {c[0].split(': ', 1)[1]: c for c in nt.preset_cases()}
    for name in names:
        _, refset, ours, plate = cases[name]
        for sname in ('pink -18', 'drums -6', 'music -10'):
            mono = np.asarray(nt.SIGNALS[sname][0](FS), np.float32)
            mono = mono[0] if mono.ndim == 2 else mono
            x = nl.stereo(mono)
            out = []
            # the whole preset (the plate from its cached capture)
            ref = nt.plate_ref(mono, refset['state'], True, True)
            our = h.render_many([dict(x=x, **ours)], 'model')[0]
            out.append(f'whole {nl.residual_db(ref, our, nt.PRE):6.1f}' if ref is not None else 'whole  (no capture)')
            # the chain in front: the same state and values with the reverb off
            off = {'Reverb State': 0.0}
            r = h.render_many([dict(x=x, state=refset['state'], norm=off)], 'ref', cache=True)[0]
            o = h.render_many([dict(x=x, params=ours['params'], norm=dict(ours['norm'], **off))], 'model')[0]
            out.append(f'reverb off {nl.residual_db(r, o, nt.PRE):6.1f}')
            # each stage in front alone, with the preset's values
            for st in (('CHAR',), ('EQ',), ('DBL',), ('CHAR', 'DBL'), ('EQ', 'DBL'), ('CHAR', 'EQ')):
                norm = h.ONLY(*st)
                r = h.render_many([dict(x=x, state=refset['state'], norm=norm)], 'ref', cache=True)[0]
                o = h.render_many([dict(x=x, params=ours['params'], norm=dict(ours['norm'], **norm))], 'model')[0]
                out.append(f'{"+".join(s.lower() for s in st)} {nl.residual_db(r, o, nt.PRE):6.1f}')
            print(f'{name:13s} {sname:9s} ' + ' | '.join(out), flush=True)


if __name__ == '__main__':
    main()
