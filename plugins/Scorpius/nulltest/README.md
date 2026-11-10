# Scorpius: null-test and measurement scripts

The scripts that measure the original, fit and train Scorpius's models and null the two against each other. They
need Windows, Python 3.12 or newer with the root `requirements.txt` (`requirements-train.txt` adds PyTorch for the
learned blocks), the original installed and named in `local.yaml` (`Scorpius.ref_vst3`, `Scorpius.ref_name`), its
default saved state in `reference/scorpius/state_default.bin`, and the tools built (`-DORRERY_TOOLS=ON`). Renders and raw results stay
local (git-ignored); the published measurement data is in `measurements/Scorpius/`. [MEASUREMENTS.md](../MEASUREMENTS.md) names the script
behind each value; [NULLTESTS.md](../NULLTESTS.md) holds the results.

| Role | Scripts |
|---|---|
| Harness | `sc_ref.py` (renders through the original, our VST3 or ScRender; cache, settle, module switches, signals), `refstate_lib.py` (reads and edits the original's saved state through `scripts/nulltest/ref_state_lib.py`) |
| Null tests | `first_null.py` (the self-check of the harness, the hosts and the build; `nulltest_lib.py` its helpers), `nulltest.py` (runs the next three), `null_chain.py` (presets and settings, the chain table), `null_modules.py` (module by module), `null_quiet.py` (quiet material), `probe_autom.py` (automation) |
| Measurements | `probe_survey.py` (first look at every module), `probe_order.py` (signal order; the drum-like test signal), `measure_linear.py` (small-signal responses), `probe_comp.py`, `probe_comp_colour.py`, `measure_autom_curve.py`, `measure_harm_ramp.py`, `probe_switch_on.py` |
| Fits | `fit_exp.py`, `fit_comp.py`, `fit_comp_timing.py`, `fit_converters.py`, `fit_resample_high.py`, `fit_eq.py`, `fit_eqrbj.py`, `fit_eqbands.py`, `fit_eqlow.py`, `fit_eqfinal.py`, `fit_eqlaw.py`, `fit_eqsat.py`, `fit_eqnull.py`, `fit_harmlin.py`, `fit_harm.py`, `fit_grit.py`, `fit_loud.py`, `fit_loud_timing.py`, `fit_low_parallel.py`, `fit_sub_parallel.py`, `fit_linear_vf.py` with `vecfit_lib.py` (writes `Source/dsp/LinearFits.h`) |
| Learned blocks | `render_training.py` (training material), `train_comp_input.py`, `train_gru.py`, `train_wn.py`, `train_wh.py`, `train_gain.py` |
| Plug-in scripts (`../scripts/`) | `export_models.py` (writes `Source/dsp/LearnedModels.h`), `measure_ui.py` (the reference editor's geometry; `--text` for its words), `compare_ui.py`, `fit_fadercap.py`, `fit_stripe.py` |
