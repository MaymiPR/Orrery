# Scorpius: null-test and measurement scripts

The scripts that measure the original, fit and train Scorpius's models and null the two against each other. They
need Windows, Python 3.12 or newer with the root `requirements.txt` (`requirements-train.txt` adds PyTorch for the
learned blocks), the original installed and named in `local.yaml` (`Scorpius.ref_vst3`, `Scorpius.ref_name`), its
default saved state in `reference/orion/state_default.bin`, and the tools built (`-DORRERY_TOOLS=ON`). Renders,
results and measurement data stay local (git-ignored). [MEASUREMENTS.md](../MEASUREMENTS.md) names the script
behind each value; [NULLTESTS.md](../NULLTESTS.md) holds the results.

| Role | Scripts |
|---|---|
| Harness | `harness.py` (renders through the original, our VST3 or ScRender; cache, settle, module switches, signals), `refstate.py` (reads and edits the original's saved state through `tools/tgpstate.py`) |
| Null tests | `nullchain.py` (presets and settings, the chain table), `nullmod.py` (module by module), `nullquiet.py` (quiet material), `autom_probe.py` (automation) |
| Measurements | `survey.py` (first look at every module), `order.py` (signal order; the drum-like test signal), `linear.py` (small-signal responses), `comp.py`, `comp_colour.py`, `autom_curve.py`, `harm_ramp.py`, `switch_on.py` |
| Fits | `fit_exp.py`, `fit_comp.py`, `fit_comp_timing.py`, `fit_converters.py`, `fit_resample_high.py`, `fit_eq.py`, `fit_eqrbj.py`, `fit_eqbands.py`, `fit_eqlow.py`, `fit_eqfinal.py`, `fit_eqlaw.py`, `fit_eqsat.py`, `fit_eqnull.py`, `fit_harmlin.py`, `fit_harm.py`, `fit_grit.py`, `fit_loud.py`, `fit_loud_timing.py`, `fit_low2.py`, `fit_sub3.py`, `fit_linear_vf.py` with `vecfit.py` (writes `Source/dsp/LinearFits.h`) |
| Learned blocks | `capture_nn.py` (training material), `prep_comp.py`, `train_gru.py`, `train_wn.py`, `train_wh.py`, `train_gain.py`, `export_models.py` (writes `Source/dsp/LearnedModels.h`) |
