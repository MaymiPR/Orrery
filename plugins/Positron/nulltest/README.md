# Positron: null-test and measurement scripts

The scripts that measure the original, fit Positron's constants and null the two against each other. They need
Windows, Python 3.12 or newer with the root `requirements.txt`, the original installed and named in `local.yaml`
(`Positron.ref_vst3`, `Positron.ref_name`), and the tools built (`-DORRERY_TOOLS=ON`). Renders and raw results stay
local (git-ignored); the published measurement data is in `measurements/Positron/`. [MEASUREMENTS.md](../MEASUREMENTS.md) names the script behind each value;
[NULLTESTS.md](../NULLTESTS.md) holds the results.

| Role | Scripts |
|---|---|
| Harness and models | `po_ref.py` (renders through the original, our VST3 or PoRender; cache, stage isolation, signals), `charmodel_lib.py` (the character section in Python), `charsim_lib.py` (the band gain computer through `native/CharSim.cpp`, built by `scripts/build_native.py`), `ident_lib.py` and `ident_signals_lib.py` (band-signal identification), `limiter_lib.py` (the limiter in Python), `vst3state_lib.py` (wraps a state for the VST3 host), `film_lib.py` (RefCapture film frames), `plotstyle_lib.py` (plot style); the state reader is `scripts/nulltest/ref_state_lib.py` |
| Null tests | `first_null.py` (the self-check of the harness, the hosts and the build; `nulltest_lib.py` its helpers), `nulltest.py` (every case; `--vst3` for the built VST3; `--report` writes NULLTESTS.md), `null_stress.py` (the stress grid), `null_track.py` (a music file of one's own), `null_oversampling.py`, `null_sidechain.py`, `null_lim_max.py`, `check_reference.py` (repeatability of the reference renders), `probe_sensitivity.py`, `probe_sweep_residual.py` |
| Measurement battery | `measure_core.py`, `measure_eq.py`, `measure_char_static.py`, `measure_char_small.py`, `measure_char_dyn.py`, `measure_limiter.py`, `measure_smoothing.py`, `measure_oversampling.py`, `measure_os_rates.py`, `measure_meters.py`, `measure_sidechain.py`, `probe_lufs.py`, `probe_readout.py`, `read_char_plots.py` |
| Probes of the character section | `probe_crest.py`, `probe_det_edge.py`, `probe_det_spectrum.py`, `probe_gr_drop.py`, `compare_third_harmonic.py`, `measure_high_gain_probe.py`, `measure_high_gain_program.py`, `measure_high_gain_noise.py`, `measure_high_release.py`, `fit_high_static.py`, `probe_mid_det.py`, `probe_mid_det_spectrum.py`, `probe_mid_edge.py`, `measure_mid_release.py`, `measure_mid_release_speed.py`, `measure_mid_static.py`, `measure_mid_times.py`, `probe_nl_hear.py`, `compare_prediction.py`, `probe_shape_mid.py`, `probe_shape_side.py`, `measure_static_n.py`, `probe_cross.py`, `probe_band_path.py` |
| Probes of the limiter, smoothing and oversampling | `probe_limiter.py`, `probe_lim_interp.py`, `probe_lim_nl.py`, `probe_lim_pulse.py`, `null_lim_rate.py`, `null_steps.py`, `probe_os.py` |
| Fits | `fit_bands.py`, `measure_band_rates.py`, `fit_crossover.py`, `fit_bandlaw.py`, `fit_multistart.py`, `fit_music.py`, `fit_character.py`, `fit_width.py`, `fit_eq.py`, `fit_oversampling.py`, `fit_os_rates.py` |
| Editor and meters | `measure_dash_meter.py`, `measure_gr_meters.py`, `read_leds.py`, `read_readouts.py`, `measure_stair_gr.py` |
| Plug-in scripts (`../scripts/`) | `make_character_table.py` (writes `Source/dsp/CharacterTable.h` and `NlBandFilters.h`), `make_glass.py` (writes `resources/glass/`), `compare_ui.py` (the editor against the reference; `--zoom`, `--knobs` for the knobs' mouse behaviour), `fit_glass.py`, `fit_knobs.py`, `fit_knob_shadow.py` |
