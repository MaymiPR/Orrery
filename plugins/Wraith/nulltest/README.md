# Wraith: null-test and measurement scripts

The scripts that measure the original, fit Wraith's constants, make its reverb responses and null the two against
each other. They need Windows, Python 3.12 or newer with the root `requirements.txt`, the original installed and
named in `local.yaml` (`Wraith.ref_vst3`, `Wraith.ref_name`), and the tools built (`-DORRERY_TOOLS=ON`). Renders,
results and measurement data stay local (git-ignored). [MEASUREMENTS.md](../MEASUREMENTS.md) names the script behind
each value; [NULLTESTS.md](../NULLTESTS.md) holds the results.

| Role | Scripts |
|---|---|
| Harness | `ts.py` (renders through the original, our VST3 or WrRender; cache, stage isolation, signals), `nulltest_lib.py` (numpy helpers: signals, residuals, transfer functions) |
| Null tests | `first_null.py` (the self-check of the harness, the hosts and the build), `nulltest.py` (every case; `--vst3` for the built VST3; `--report` writes NULLTESTS.md with `nulltests_notes.md` as its prose), `null_auto.py` (automation), `null_plate.py` (the plate), `doubler_metric.py` (the doubler's behaviour metric) |
| Probes | `probe_smoothing.py`, `probe_rider.py`, `probe_char.py`, `probe_side.py`, `probe_static.py`, `probe_steps.py`, `probe_det_weight.py`, `probe_bass_gain.py`, `probe_doubler.py`, `probe_voices.py`, `probe_dbl_rate.py`, `probe_dbl_residue.py`, `probe_dbl_voicegain.py`, `probe_dbl_voiceresp.py`, `probe_dbl_voices2.py`, `probe_reverb.py`, `probe_plate_filter.py`, `probe_plate_presets.py`, `read_presets.py` (the factory presets from the original's saved states, through `tools/tgpstate.py`) |
| Fits | `fit_eq.py`, `fit_eq_motion.py`, `fit_rider.py`, `fit_char.py`, `fit_char_gain.py`, `fit_expander.py`, `fit_curve.py`, `fit_overshoot.py`, `fit_focus_eq.py`, `fit_focus_eq2.py`, `fit_allpass.py`, `fit_focus_hf.py`, `merge_focus_rates.py`, `gen_focus_eq.py` (writes `Source/dsp/FocusEq.h`), `fit_voice_filter.py`, `fit_dbl_voice.py` |
| Reverb responses | `plate_record.py`, `plate_filter_capture.py`, `pack_reverb.py` (writes `ir/reverb_<rate>.bin`) |
