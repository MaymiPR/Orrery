"""Null tests of Scorpius: the three null scripts in order, the same numbers NULLTESTS.md publishes.

    python nulltest.py [model|ours]     # model: our processor through tools/ScRender (default); ours: the built VST3

null_chain.py (the whole plug-in on program material), null_modules.py (module by module; it takes no plug-in
argument) and null_quiet.py (quiet material, where the shared expander acts). NULLTESTS.md is assembled from their
tables.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    plugin = sys.argv[1] if len(sys.argv) > 1 else 'model'
    if plugin not in ('model', 'ours'):
        sys.exit('usage: python nulltest.py [model|ours]')
    failed = 0
    for script, args in (('null_chain.py', [plugin]), ('null_modules.py', []), ('null_quiet.py', [plugin])):
        print(f'== {script} {" ".join(args)}', flush=True)
        failed += subprocess.run([sys.executable, os.path.join(HERE, script), *args], cwd=HERE).returncode != 0
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
