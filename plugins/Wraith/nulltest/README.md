# Wraith: null-test and measurement scripts

The scripts that measure the original, fit Wraith's constants, make its reverb responses and null the two against
each other. They need Windows, Python 3.12 or newer with the root `requirements.txt`, the original installed and
named in `local.yaml` (`Wraith.ref_vst3`, `Wraith.ref_name`), and the tools built (`-DORRERY_TOOLS=ON`). Renders and raw results stay
local (git-ignored); the published measurement data is in `measurements/Wraith/`. [MEASUREMENTS.md](../MEASUREMENTS.md) names the script behind
each value; [NULLTESTS.md](../NULLTESTS.md) holds the results.

| Role | Scripts |
|---|---|
| Harness | `wr_ref.py` (renders through the original, our VST3 or WrRender; cache, stage isolation, signals), `nulltest_lib.py` (numpy helpers: signals, residuals, transfer functions) |
| Null tests | `first_null.py` (the self-check of the harness, the hosts and the build), `nulltest.py` (every case; `--vst3`, the built VST3 against the renderer; `--ours vst3` for the built VST3; `--report` writes NULLTESTS.md), `null_auto.py` (automation), `null_plate.py` (the plate), `measure_doubler.py` (the doubler's behaviour metric), `null_stress.py` (the stress grid: settings, levels, signals, automation, rates and block sizes), `null_track.py` (a demo track, local only) |
| Probes | `probe_smoothing.py`, `probe_block_smoothing.py`, `probe_reverb_toggle.py`, `probe_rider.py`, `probe_char.py`, `probe_side.py`, `probe_static.py`, `probe_steps.py`, `probe_det_weight.py`, `probe_bass_gain.py`, `probe_doubler.py`, `probe_voices.py`, `probe_dbl_rate.py`, `probe_dbl_residue.py`, `probe_dbl_voicegain.py`, `probe_dbl_voiceresp.py`, `probe_dbl_voice_cancel.py`, `probe_reverb.py`, `probe_plate_filter.py`, `probe_plate_presets.py`, `read_presets.py` (the factory presets from the original's saved states, through `scripts/nulltest/ref_state_lib.py`) |
| Fits | `fit_eq.py`, `fit_eq_motion.py`, `fit_rider.py`, `fit_char.py`, `fit_char_gain.py`, `fit_expander.py`, `fit_curve.py`, `fit_overshoot.py`, `fit_focus_eq.py` and `focus_eq_lib.py`, `fit_allpass.py`, `fit_focus_hf.py`, `focus_rates_lib.py` (merges the per-rate fits), `fit_voice_filter.py`, `fit_dbl_voice.py` |
| Reverb responses | `render_plate.py`, `render_plate_filter.py` |
| The standard's files | `paramdump.txt` (the original's parameters, each at 41 positions), `params.md` (the table made from it), `tapers.json` (the taper fitted to each continuous parameter; `Source/Params.h` keeps its own ranges, written before this file), `check_tapers.py` (the built VST3's parameter texts against `paramdump.txt` at its 41 positions), `classification.md` (one row per stage: its class, what decided it, its target and its state), `targets/wraith.json` (the target file of the standard's one-command null tools: `{orrery}` is the checkout, `{wraith_ref_vst3}` and `{wraith_ref_name}` the original's file and host name, each read from the environment or the tools' `local.yaml`), `history/` (one record per DSP change) |
| Plug-in scripts (`../scripts/`) | `make_focus_eq.py` (writes `Source/dsp/FocusEq.h`), `pack_reverb.py` (writes `resources/ir/reverb_<rate>.bin`) |
