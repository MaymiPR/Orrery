# Contributing to Orrery

Bug reports and null-test findings go to the [issues](https://github.com/MaymiPR/Orrery/issues/new/choose). This page
covers changing the code: how it is built, tested and checked, how a change reaches `main`, and how a release is
made. [STANDARDS.md](STANDARDS.md) holds the rules in full.

## The one rule

Each plug-in follows its original, and the original is the reference for every behaviour. A change that affects the
sound is measured against the original's own render of the same settings ([Null tests](#null-tests)), and what was
measured goes into the plug-in's MEASUREMENTS.md and NULLTESTS.md. Nothing of the originals (renders, files, art,
presets) enters the repository; a decision is recorded as the rule it produced, with the date of its approval, and
nobody's words are quoted in a file, a commit message, a tag or release notes.

One exception, approved on 2026-11-01 and listed in `.provenance`: Wraith's room and plate reverb responses
(`plugins/Wraith/resources/ir/`) are measured from The Spirit's output with impulses and run by convolution, because its reverbs
are recordings that a model cannot null. They are measurements of its output, not its files;
`plugins/Wraith/nulltest/render_plate.py` and `plugins/Wraith/scripts/pack_reverb.py` make them.

## Build

Requirements and the commands per platform are in the [build guide](docs/BUILDING.md), the Windows installer
included. The default configuration (`-DORRERY_TOOLS=ON`) also builds the hosts for the reference plug-ins
(`tools/`), each plug-in's offline renderer (PoRender, ScRender, WrRender) and its editor snapshot tool, under
`build/<tool>_artefacts/Release/`. `python scripts/build_native.py` builds the null tests' native helpers
(`plugins/<Id>/nulltest/native/`, Positron's band gain computer for the fits) into `build/native/<Id>/`.
`-DORRERY_DEV_COPY=ON` (the default) also copies each VST3 to `build/plugins/<Product name>.vst3`, the folder a DAW's
plug-in junction points at. The code in `shared/` is built once, as the static library `OrreryShared`, which every
plug-in, test, snapshot and renderer links.

## Tests

| Test | What it does | Command |
|---|---|---|
| `PositronTests` | Positron's DSP and processor: filters, the FIR crossover, latency, bypass, the limiter's ceiling, oversampling, state, extreme input | `ctest --test-dir build -C Release --output-on-failure` |
| `ScorpiusTests` | Scorpius's DSP and processor: the modules, presets, A / B, the side-chain, state; `bench` times the learned models | the same |
| `WraithTests` | Wraith's DSP and processor: layout, every stage off passes the input, gains, bypass, state, the start-up preset, tapers, extreme input, A / B, I/O LINK, the side-chain without a bus | the same |
| `PositronHostTest`, `ScorpiusHostTest`, `WraithHostTest` | the built VST3 hosted as a DAW hosts it (`tools/HostTest.cpp`): parameters, save and reload into a new instance, the editor, a sample-rate change, offline rendering, and every saved state in `plugins/<Id>/tests/data/state-<x.y.z>.bin` loading with the same parameter texts | the same |
| Render regression | `tests/regress/<Id>/jobs.txt` through PoRender, ScRender and WrRender against the committed goldens; our output does not change unless intended (`--update` after an intended DSP change, committed with it) | `python scripts/render_regress.py --build build` |
| Null tests | the same signals through the original and through ours; the residual in dB | per plug-in, [Null tests](#null-tests) |
| Repository checks | absolute paths, old names, attribution forms, document style, whitespace | `python scripts/check_repo.py` |

Each command returns non-zero on a failure.

## The local check

`scripts/check.ps1` (Windows) or `scripts/check.sh` (Linux, macOS) is the one command before any build is handed
over and the proof on a private repository, where no workflow runs. It closes a running host, runs
`check_repo.py` and the lint tools it finds on the PATH (a missing tool is reported, never installed), configures
when `build/CMakeCache.txt` is missing, builds `ci_targets` into a log, counts warnings by the same rule as the
workflows and fails above zero, asserts the VST3 is newer than the build start, runs `ctest` and the render
regression, and prints one `CHECK` line with the counts. Switches: `-SkipBuild`, `-SkipTests`, `-KeepFl`.

## Changing the code

1. Branch `fix/<slug>`, `feature/<slug>` or `chore/<slug>` from `main`.
2. Make the change. A DSP change is recorded with the null regression; a case worse by more than 0.5 dB blocks it.
3. `scripts/check.ps1` (or `check.sh`) passes.
4. Open a pull request; Lint and CI run on a public repository, the local check stands in on a private one.
5. Squash merge; the branch is deleted on both sides at merge.
6. Add the line to `CHANGELOG.md` under `## Unreleased` (New, Improved, Fixed or Known issues, with before and
   after numbers in dB for a sound change).

## Making a release

[.github/RELEASE_CHECKLIST.md](.github/RELEASE_CHECKLIST.md) is the one list; the release workflow opens it as an
issue for a `release/x.y.z` branch or by hand. In short:

1. `## Unreleased` in [CHANGELOG.md](CHANGELOG.md) holds everything user-facing.
2. Optional: branch `release/x.y.z`; the checklist issue opens.
3. The local check passes with zero warnings; on a public repository Lint and CI are green on `main`.
4. `python scripts/bump_version.py x.y.z`: the version in CMakeLists.txt, the dated CHANGELOG section, the commit
   `Release x.y.z`. Push `main`.
5. When packaging changed, run Build and release by hand once and check the artifacts.
6. On approval: `python scripts/bump_version.py x.y.z --tag` and `git push origin vx.y.z`. The workflow builds
   Windows, macOS (universal) and Linux, validates every plug-in with pluginval at strictness 10 (and `auval` on
   macOS), signs and notarizes when the repository has the secrets, and publishes the three installers with
   `SHA256SUMS.txt`, attestations and the notes from CHANGELOG.md. A tag with a hyphen publishes a pre-release.
7. Check the release page, download one file on another machine, close the checklist issue.
8. A release that fails after the tag is fixed on `main` and shipped as the next patch version.

The signing secrets are named in `.github/workflows/release.yml`; without them the workflow publishes the same files
unsigned and the notes say so.

## Repository layout

| Path | What it holds |
|---|---|
| `plugins/<Id>/` | one plug-in: `Source/`, `resources/` (Positron's glass, Wraith's measured reverb responses), `tests/` (with `data/`, the saved-state fixtures), `tools/` (its renderer; Scorpius's and Wraith's own snapshot tools), `scripts/` (the scripts that write its resources and measure its editor), `nulltest/` (the harness, with `native/` for its C++ helpers; needs the original installed), README, RESEARCH, MEASUREMENTS, NULLTESTS |
| `shared/` | the static library `OrreryShared`: the UI library (theme, controls, metal knob, the host-keys hand-back `HostFocus`), the I/O level meter, the plug-ins' FFT and the deterministic math (`dsp/Fft.h`, `dsp/Math.h`), the Instrument Sans font |
| `tools/` | hosts for the reference plug-ins: offline renders (RefRender), editor films and screenshots (RefCapture), parameter lists (ParamDump), the keyboard-focus check (FocusCheck); the host test (`HostTest.cpp`) and the editor snapshot tool (`Snapshot.cpp`), built per plug-in |
| `tests/regress/` | the render regression's cases and golden renders |
| `scripts/` | `bump_version.py`, `release_notes.py`, `render_regress.py`, `make_site.py`, `check_repo.py`, `check.ps1`, `check.sh`, `build_native.py` (the null tests' native helpers); `nulltest/ref_state_lib.py`, the reader of the originals' saved state that the harnesses import |
| `measurements/` | the published measurement data per plug-in (`measurements/<Id>/`) |
| `packaging/` | the installers; `plugins.txt` lists the plug-ins they hold |
| `docs/` | the build guide, `branding/` (banners, icon, social preview, `colours.json`), `screenshots/` |
| `.github/` | `workflows/` (Lint, CI, Build and release, Release checklist, Landing page), the issue forms, the pull request template, `RELEASE_CHECKLIST.md`, `dependabot.yml`, CODEOWNERS |
| `local.example.yaml` | the keys of `local.yaml` (git-ignored): the references' VST3 files and names, the interpreters, the tool folders |
| `requirements.txt`, `requirements-train.txt` | the Python packages of the scripts; the second adds PyTorch for Scorpius's learned blocks |

`measurements/<Id>/` holds each plug-in's published measurement data: measured responses, fitted values and the
null tests' results as JSON, with the approval recorded in `.provenance` and in each MEASUREMENTS.md (2026-11-09).
Reference renders, plots, logs, raw captures and anything taken from the original plug-ins stay out of the
repository (`.gitignore`).

## Null tests

Each plug-in's `nulltest/` folder renders the same signals through the original and through ours and reports the
residual; its README lists the scripts by role. It needs Windows, Python 3.12 or newer with the packages in
`requirements.txt` (`requirements-train.txt` adds torch for the learned blocks), the original plug-in installed and
named in `local.yaml` (`<Id>.ref_vst3` and `<Id>.ref_name` per plug-in), and the tools built (`-DORRERY_TOOLS=ON`). Each
harness is `nulltest/<ab>_ref.py` (`po_ref.py`, `sc_ref.py`, `wr_ref.py`); helper modules end in `_lib.py`, and the
scripts that write under `Source/` or `resources/` sit in `plugins/<Id>/scripts/`.

| Plug-in | Entry points |
|---|---|
| Positron | `first_null.py` (the self-check of the harness, the hosts and the build), `nulltest.py` (every case; `--vst3` for the built binary; `--report` writes NULLTESTS.md), `null_stress.py` (the stress grid), `null_track.py` (a music file of one's own) |
| Scorpius | `first_null.py` (the self-check), `nulltest.py` (every case of `null_chain.py`, `null_quiet.py` and `null_modules.py`; `ours` for the built binary; `--report` writes NULLTESTS.md), `probe_autom.py` (automation) |
| Wraith | `first_null.py` (the self-check of the harness, the hosts and the build), `nulltest.py` (every case; `--vst3`; `--report` writes NULLTESTS.md) |

The results are in each plug-in's NULLTESTS.md.

## Screenshots

`docs/screenshots/` holds the committed set. Each file comes from a plug-in's Snapshot tool
(`build/<Id>Snapshot_artefacts/Release/<Id>Snapshot`) with these options:

| File | How it is made |
|---|---|
| `positron.png`, `positron-classic-style.png` | `PositronSnapshot <file> --scale=1 --levels=-10,-9 --audio`, with `--anti` (Positron's own particle style, the default) or `--classic` |
| `scorpius.png`, `scorpius-classic-style.png` | `ScorpiusSnapshot <file> --levels=-14,-12 --audio`, with `--style=scorpius` (its own style, the default) or `--style=classic` |
| `wraith.png` | `WraithSnapshot <file> --scale=1 --levels=-12,-14`, at its start-up preset (lead) |
| `hero.png` | `positron.png`, `scorpius.png` and `wraith.png` side by side, 24 px apart, each centred in height, transparent between, scaled to 1800 px wide |
| `orrery-top-bar.png` | the shared top bar: the top 62 px of Scorpius at `--scale=2` |
| `orrery-particle-styles.png` | Positron's glass in both styles, then Scorpius's stripe in both. Each glass is cut from a `--scale=1.7` render (`--anti` or `--classic`, `--levels=-10,-9 --audio`) at design x 179.5 to 556.5, y 34.5 to 262.5, centred in its half of a 1317 x 515 frame; each stripe is cut from a `--scale=1.5` render at x 8 to 1325 (Scorpius style y 402 to 459, pasted at y 398; classic style y 400 to 459, pasted at y 456) |

When an editor changes, render its shots again and compare them with the committed files (an unchanged editor
renders the same, or within a few meter pixels); rebuild `hero.png`, `orrery-top-bar.png` and `orrery-particle-styles.png` from the
new renders.

## Versions

One version for the suite (`project(... VERSION ...)` in `CMakeLists.txt`). A new plug-in raises the middle number
(1.1.0 added Scorpius, 1.2.0 Wraith), a fix the last. Tags are `vx.y.z`; `vx.y.z-rc.N` publishes a pre-release.
`scripts/bump_version.py` writes every version.

## Frozen identity

What saved projects, presets and installs depend on, never changed once a release has shipped. These items keep the
suite's first name, Orrery Suite, which the suite carried until it took the repository's name, Orrery (2026-11-09):

| Item | Value |
|---|---|
| Manufacturer code | `Orry` |
| Plug-in codes | Positron `Pstn`, Scorpius `Scrp`, Wraith `Wrth` (`packaging/plugins.txt`) |
| Bundle and CLAP IDs | `com.orrerysuite.positron`, `com.orrerysuite.scorpius`, `com.orrerysuite.wraith` |
| Parameter IDs | each plug-in's `Source/Params.h` |
| Company name | `Orrery Suite` (`COMPANY_NAME` in each `plugin.cmake`) |
| Installer AppId | `CFCB62BB-FB41-4B4B-AB2C-4ED7523FCF0F` (`packaging/Orrery.iss`) |
| Install folders | Windows `VST3\Orrery Suite`, `CLAP\Orrery Suite` and `Program Files\Orrery Suite` (`packaging/Orrery.iss`); macOS `Orrery Suite` (`SUBFOLDER` in `release.yml`); Linux `~/.vst3/Orrery Suite` and `~/.clap/Orrery Suite` (`packaging/install-linux.sh`) |

## Deviations from the standard

None.
