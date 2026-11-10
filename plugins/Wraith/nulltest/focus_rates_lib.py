"""Merges per-rate fits of fit_focus_hf.py (each run for one sample rate into its own file) into one file for
make_focus_eq.py: the shared sections and all-passes from the first file, each rate's sections and all-passes from
the file that fitted it.

    python focus_rates_lib.py out.json focus_eq2_rates.json:44100,48000 focus_eq2_rates_ap96.json:96000 ...
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, 'renders')
out = None
for arg in sys.argv[2:]:
    name, rates = arg.split(':')
    m = json.load(open(os.path.join(R, name)))
    if out is None: out = {k: v for k, v in m.items() if k not in ('rates', 'rate_allpass', 'rate_delay')}
    for fs in rates.split(','):
        out.setdefault('rates', {})[fs] = m['rates'][fs]
        if fs in m.get('rate_allpass', {}): out.setdefault('rate_allpass', {})[fs] = m['rate_allpass'][fs]
json.dump(out, open(os.path.join(R, sys.argv[1]), 'w'), indent=1)
print('wrote', sys.argv[1], 'rates', sorted(out['rates']), 'all-passes at', sorted(out.get('rate_allpass', {})))
