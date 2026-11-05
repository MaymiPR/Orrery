# Positron: null-test and measurement scripts

The scripts that measure the original, fit Positron's constants and null the two against each other. They need
Windows, Python 3.12 or newer with the root `requirements.txt`, the original installed and named in `local.yaml`
(`Positron.ref_vst3`, `Positron.ref_name`), and the tools built (`-DORRERY_TOOLS=ON`). Renders, results and
measurement data stay local (git-ignored). [MEASUREMENTS.md](../MEASUREMENTS.md) names the script behind each value;
[NULLTESTS.md](../NULLTESTS.md) holds the results.

| Role | Scripts |
|---|---|
| Harness and models | `tgp.py` (renders through the original, our VST3 or PoRender; cache, stage isolation, signals), `charmodel.py` (the character section in Python), `charsim.py` (the band gain computer through `tools/charsim.cpp`), `ident.py` and `ident_signals.py` (band-signal identification), `limpy.py` (the limiter in Python), `vst3state.py` (wraps a state for the VST3 host), `filmtools.py` (RefCapture film frames), `plotstyle.py` (plot style); the state reader is `tools/tgpstate.py` |
| Null tests | `nulltest.py` (every case; `--vst3` for the built VST3; `--report` writes NULLTESTS.md), `stress.py` (the stress grid), `track.py` (a music file of one's own), `null_oversampling.py`, `null_sidechain.py`, `limmax.py`, `refcheck.py` (repeatability of the reference renders), `sensitivity.py`, `sweepres.py` |
| Measurement battery | `measure_core.py`, `measure_eq.py`, `measure_char_static.py`, `measure_char_small.py`, `measure_char_dyn.py`, `measure_limiter.py`, `measure_smoothing.py`, `measure_oversampling.py`, `measure_os_rates.py`, `measure_meters.py`, `measure_sidechain.py`, `lufs_probe.py`, `readout_probe.py`, `plot_char.py` |
| Probes of the character section | `crest.py`, `detedge.py`, `detspec.py`, `grdrop.py`, `h3cmp.py`, `hightrace.py`, `hightrace2.py`, `hightrace3.py`, `hirel.py`, `histatic.py`, `middet.py`, `middetspec.py`, `midedge.py`, `midrel.py`, `midrel2.py`, `midstatic.py`, `midtimes.py`, `nlhear.py`, `predict.py`, `shapemid.py`, `shapeside.py`, `staticn.py`, `xprobe.py`, `xprobe2.py` |
| Probes of the limiter, smoothing and oversampling | `lim_probe.py`, `limident.py`, `limnl.py`, `limpulse.py`, `limrate.py`, `steps.py`, `os_probe.py` |
| Fits | `fit_bands.py`, `ident_rate.py`, `fit_crossover.py`, `fit_bandlaw.py`, `fit_multistart.py`, `fit_music.py`, `fit_character.py`, `fit_width.py`, `make_table.py` (writes `Source/dsp/CharacterTable.h`), `fit_eq.py`, `fit_oversampling.py`, `os_rates_fit.py` |
| Editor and meters | `dashmeter.py`, `grtarget.py`, `ledread.py`, `readouts.py`, `stairgr.py`, `uiknobs.py` |
