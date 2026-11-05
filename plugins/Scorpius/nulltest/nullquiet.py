"""Nulls on quiet material, where the shared expander acts (MEASUREMENTS.md 3): the default preset and the drive alone
(colour a, hi-pass on) on the track, the drums and pink noise far below their usual levels. The table "Quiet
material" of NULLTESTS.md.
    python nullquiet.py [model|ours]"""
import sys
import harness as o
import nullmod as N

if __name__ == '__main__':
    plugin = sys.argv[1] if len(sys.argv) > 1 else 'model'
    sig = N.signals()
    X = {'track -60': sig['track'] * 10 ** (-60 / 20), 'track -66': sig['track'] * 10 ** (-66 / 20),
         'drums -62': sig['drums'] * 10 ** (-62 / 20), 'drums -70': sig['drums'] * 10 ** (-70 / 20),
         'pink -72': o.noise(6.0, -72, seed=5, pink=True), 'pink -78': o.noise(6.0, -78, seed=5, pink=True)}
    for name, spec in (('default', {}), ('drive alone', dict(params=o.ONLY('drive', hipass=1)))):
        jobs = [dict(x=x, **spec) for x in X.values()]
        ref = o.render_many(jobs, cache=True)
        ours = o.render_many(jobs, plugin=plugin)
        print(f'{name:12s}', '  '.join(f'{k} {o.null_db(r, m):6.1f}' for k, r, m in zip(X, ref, ours)), flush=True)
