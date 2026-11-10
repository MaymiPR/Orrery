# Positron: measurements

The original's audio behaviour, measured from its output, and the values Positron's DSP takes from it. The null
results are in [NULLTESTS.md](NULLTESTS.md), cited here by case name; the controls and the editor are in
[RESEARCH.md](RESEARCH.md).

## Setup

| Item | Value |
|---|---|
| Reference | Cradle The God Particle 1.2.4, VST3, Windows |
| Offline host | `tools/RefRender.cpp`: a JUCE VST3 host; renders float32 files at a fixed rate and block size, sets parameters by displayed or normalised value, automates one at a block boundary, loads a saved state, feeds a stereo side-chain (the bus is kept active for jobs with side-chain audio); a fresh instance per job; `raw=1` skips latency compensation |
| Editor host | `tools/RefCapture.cpp`: opens the editor and plays audio in real time; films it (a frame about every 27 ms) or clicks and drags in it; used for the meters and to switch the global oversampling setting |
| Harness | `nulltest/po_ref.py`: `render_many(jobs)`, stage presets (`EQ_ONLY`, `CHAR_ONLY`, `LIM_ONLY`, `NONE`), test signals, an on-disk render cache |
| Scripts | one per topic (`nulltest/measure_*.py`, `fit_*.py`, `read_char_plots.py` and the probes each section names), writing JSON and plots to `measurements/<topic>/` |
| Rate, block | 48 kHz, block 512 (64 for the smoothing probes) |
| Oversampling | 1x, the original's default, unless a section says otherwise |
| Pre-roll | 2 s: after loading, the original's internal delay ramps from 54 to 152 samples over about 0.25 s |
| Stage isolation | the other stages bypassed with their own power buttons |
| Gain | the level of the test tone's fundamental (lock-in, Hann window) at the output re the input |
| Repeatability | every null-suite case rendered fresh twice differs from its cached render by less than -430 dB (`check_reference.py`) |

`measurements/` and `nulltest/renders/` are git-ignored. This file is the published record; every number in it is
reproduced by the script its section names.

## 1. Signal path and latency

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Order | input gain → EQ → character → limiter → output gain; the EQ and the character section run inside the oversampled block | stage isolation | exact |
| Reported latency, 1x | 179 / 189 / 357 samples at 44.1 / 48 / 96 kHz | host report | exact |
| Reported latency at 48 kHz, 1x / 2x / 4x / 8x | 189 / 212 / 217 / 219 samples | host report | exact |
| Core path, every stage bypassed | a fixed 3.1505 ms delay: an integer delay plus a first-order Thiran all-pass for the fraction (151 samples + a = 0.5636 at 48 kHz, 151.279 samples); the same time at 44.1, 88.2, 96 and 192 kHz; flat magnitude | `measure_core.py` | exact; NULLTESTS.md "path: all stages bypassed" |
| Core path, step | rings at Nyquist and overshoots by 24 % (1.226) before settling | `measure_core.py` | exact |
| Character on | no extra delay: its FIR crossover carries the core delay (3.1) | click | exact |
| EQ on | no extra delay | click | exact |
| Limiter on | adds 38 samples, its look-ahead: 190 samples raw | click | exact |
| Limiter bypassed | the output is 37 to 38 samples earlier than the reported latency; the report does not change with the limiter bypass | click | exact |
| Small-signal gain at the defaults, 1 kHz | +8.44 dB (character +3.54 dB, limiter +4.90 dB) | tone | measured |

## 2. EQ

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Bands | three RBJ-cookbook biquads at the processing rate: low shelf 180 Hz, Q 0.7; peaking 637 Hz, Q 0.5; high shelf 10 000 Hz, Q 0.7 | impulse responses, `fit_eq.py` | exact at 1x: magnitude error ≤ 0.0004 dB, phase matching |
| Gain law | the gain in dB equals the knob value (±6 dB, linear) | `measure_eq.py` | exact |
| Level dependence | none: impulses at -40 and -12 dBFS agree | `measure_eq.py` | exact |
| With oversampling | the filters are designed at the higher rate, so the top octave differs: high shelf +6 dB at 15 kHz reads 5.56 (1x), 5.09 (2x), 4.98 (4x), 4.95 dB (8x) | `measure_eq.py` | measured |
| Filter structure while gains move | state-variable filters, the gain gliding in linear amplitude (5.1) | `null_steps.py` | matches the glide; direct forms do not |

NULLTESTS.md: "eq: low +6 mid -4 high +3", "eq: sweep, low -6 high +6".

## 3. Character section

The section splits the signal into three bands; each band runs a parallel compressor whose wet gain feeds a shaper,
and a side gain per band follows the shaper. NULLTESTS.md: the "char:" cases, the stress groups "amount" and
"amount char-only", and the mastered track.

### 3.1 Bands: an FIR crossover (`measure_char_*.py`, `fit_crossover.py`, `fit_bands.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Split | three bands with the magnitudes of a Linkwitz-Riley 4th-order crossover at 157 Hz and 2.68 kHz: low = LP(fc1) · AP(fc2), mid = HP(fc1) · LP(fc2), high = HP(fc1) · HP(fc2) | masker test: a -3 dBFS masker over a comb of 44 probe tones at -60 dBFS (`bands_masker.png`), seven maskers fitted together | median error 0.02 dB; LR2 fits ten times worse |
| Filter type | FIR, 661 taps at 48 kHz, main peak at 151: the core delay, kept when the section is bypassed | small-signal impulse responses at the nine amount settings | exact |
| Rank | the nine responses span exactly three fixed filters (the fourth singular value is 2e-8 of the first); three IRs rebuild all nine to within 3e-8 | SVD | exact |
| Choice of split | not unique from these data; the split closest to linear-phase LR4 magnitudes at 157 / 2676 Hz, which matches the masker test | `fit_bands.py` | |
| Passband phase | near zero relative to the delay | | exact |
| 0 % response | the sum of the three bands, not exactly the bypassed path: up to -0.08 dB of ripple at 280 Hz and +2° of phase near 120 Hz | | exact |

The plug-in uses these IRs at 48 kHz and the original's own filters at the other rates (3.12).

### 3.2 Small-signal gain against the amount

Method: an impulse at -60 dBFS, below every threshold. One real gain per band with the crossover of 3.1 fits the
measured complex response within ±0.11 dB from 30 Hz to 16 kHz; the section is flat at 0 %.

| amount | 0 % | 25 % | 50 % | 75 % | 100 % | 125 % | 150 % | 175 % | 200 % |
|---|---|---|---|---|---|---|---|---|---|
| low dB | 0.00 | 0.74 | 1.47 | 2.16 | 2.83 | 3.17 | 3.49 | 3.81 | 4.11 |
| mid dB | 0.00 | 1.07 | 1.99 | 2.79 | 3.49 | 4.20 | 4.85 | 5.45 | 6.02 |
| high dB | 0.00 | 0.38 | 0.67 | 0.87 | 0.99 | 1.53 | 2.03 | 2.51 | 2.96 |

- With the FIR bands of 3.1 the gains belong to that split: mid 3.60 dB and high 0.91 dB at 100 %
  (`Source/dsp/BandFilters.h`).
- The 0 to 100 % and 100 to 200 % halves follow different curves; above 100 % each band rises by roughly a fixed
  step per 25 %.

### 3.3 Static curves

Method: sine staircases from -80 to +4 dBFS, 1.2 s per step, read over the last 0.4 s of each step (`static_<f>hz.png`).
Below a band's threshold the gain is constant; above it the gain falls, crosses 0 dB at about -11 dBFS (mid and high)
and keeps falling. "Knee" is the first level where the gain is 0.1 dB under its small-signal value.

| Band (tone) | Knee at 50 / 100 / 200 % | Gain at -20 / -11 / -2 / +4 dBFS, 100 % |
|---|---|---|
| low (40, 100 Hz) | -17 / -20 / -20 … -23 dBFS | 2.80 / 2.09 / -0.20 / -5.1 (100 Hz) |
| mid (300 Hz, 1 kHz) | -32 / -35 / -35 dBFS | 1.85 / 0.02 / -2.77 / -6.3 (1 kHz) |
| crossover region (3 kHz) | -20 / -20 / -23 dBFS | 1.75 / 1.25 / -1.60 / -3.9 |
| high (8, 15 kHz) | -11 / -14 / -17 dBFS, a hard knee | 0.98 / -0.02 / -4.08 / -7.4 (8 kHz) |

- The high band behaves like a hard-knee compressor: ratio about 1.8 : 1 at 100 % and 3.7 : 1 at 200 % (0.45 and
  0.73 dB of gain reduction per dB above the knee).
- The low and mid bands have a very soft knee, spread over 30 dB or more.

### 3.4 Harmonics

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Kind | odd only: H2 and H4 stay at the analysis floor; H3 dominates (`h3_vs_level.png`) | tone staircases | measured |
| H3 at 1 kHz, 100 % | -56 dBc at -20 dBFS, -41 at -11, -22 at +1; about 1.7 dB per dB | tone staircases | measured |
| H5 | above about -8 dBFS | | measured |
| Where | the low and mid bands; the 3 kHz H3 is 10 to 15 dB lower; the high band adds nothing measurable | | measured |

A symmetric (odd) shaper sits in the low and mid bands (3.9).

### 3.5 Time behaviour

Method: bursts at -40 dBFS stepped to -20 / -6 / 0 dBFS and back, the fundamental's gain tracked over time
(`envelope_<f>hz.png`). Each band has an instant part (the shaper) and a slow part (the compressor):

| Band | Attack | Release | Instant part at 0 dBFS |
|---|---|---|---|
| mid (1 kHz) | slow part τ ≈ 100 to 150 ms | after a +1.9 dB instant jump, an S-shaped recovery: 50 % at ≈ 190 ms, done by 800 ms | ≈ 5.9 of 7.2 dB |
| low (100 Hz) | fast | a fast partial recovery in ~20 ms, then a very slow tail (2.0 of 4.0 dB back after 3 s; the GR meter falls ≈ 0.36 dB/s) | most of it |
| high (8 kHz) | ≈ 1 to 2 ms (63 % at 1.3 ms) | a small instant jump, then linear in dB at ≈ 50 dB/s of detector level | 0.5 to 1.2 dB |

The staircases agree: only the low band reads lower when the levels are stepped downwards, because its slow release
has not finished. The detectors' laws are in 3.9, 3.13, 3.16 and 3.17.

### 3.6 Detector and stereo, first readings

| Quantity | Value | Method |
|---|---|---|
| Peak sensitivity | against one sine, two tones of the same RMS (3 dB more peak) get 1.0 dB more reduction in the high band at -10 dBFS RMS and 0.1 to 0.6 dB more in the low and mid bands: no detector is a plain RMS detector | `measure_char_*.py` |
| Linking | the bands are linked: a loud L channel moves a quiet probe on R by -3.0 dB; L-only input gets the same gain on both channels (the leak into R at -52 dBFS) | `measure_char_*.py` |
| What the detectors hear | mostly the mid: L only at -10 dBFS acts like mono at about -15 dBFS, pure side at -10 dBFS like mono at about -30 dBFS | `measure_char_*.py` |
| Side gain | side signals get 0.06 dB more small-signal gain than mid signals (broadband) | `measure_char_*.py` |

The exact stereo law is in 3.10, the high band's detector in 3.13 and 3.17.

### 3.7 Side-chain EXT (`nulltest/null_sidechain.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| EXT | the main signal leaves the character section's detectors: -20 dBFS at 1 kHz is no longer compressed | a saved state with EXT set | exact |
| Side-chain filtering | heard through the input's own band split: fed the main signal on the side-chain, the original in EXT is bit-identical to INT (same filters, same delay); ours runs a second copy of the FIR split, and with the main signal on the side-chain is bit-identical to INT at 1x, 2x and 4x | `null_sidechain.py` | exact |
| Oversampling | the side-chain is upsampled by the same filters as the input | `null_sidechain.py` | exact |
| Band reduction under a loud side-chain tone in the band | a quiet main tone under a side-chain tone in the same band (-12 and -6 dBFS): within 0.004 dB (low), 0.012 dB (mid) and 0.016 to 0.034 dB (high) of the original's | `null_sidechain.py` | measured |
| Limiter | not driven by the side-chain | RESEARCH.md W8 | documented |

NULLTESTS.md, "External side-chain". Loud pink noise on the main input nulls in EXT as it does in INT (character only,
-10 dBFS, 100 %: -54.5 dB). The cost is in the CPU table.

### 3.8 Per-band structure: a parallel compressor before the shaper

Each band b, with x its band signal:

    u = x · n(t),   n = (1 - mix) + mix · g(t),   y = M · F(u)

with mix the wet share, g the wet path's gain from the compressor, M the band's small-signal gain (3.2) and F the
shaper (3.9). What shows it:

- For a steady 750 Hz tone, a cubic F(u) = u - c · u³ fitted from the H3/H1 ratio and the fundamental gives the same
  c at every level (0.96 … 0.82 from -30 to +4 dBFS; c 0.95 for mid at 100 %, 1.7 at 200 %; mix 0.72 for mid at
  100 %). 3.9 shows the series is that of a sine.
- With that c, the wet-path reduction it implies equals the GR meter's reading: 6.85 dB against 7.1 shown at
  -6 dBFS, 9.4 dB against 9.9 at 0 dBFS. The meters show the wet path's reduction, which is why they read more than
  the change heard.
- Converted to wet-path reduction, the mid band's attack and release look like a mean-square detector with a very
  soft knee: a log-like attack and an S-shaped release.
- The shaper is not clipped: past about +3 dBFS the output folds over (it falls as the input rises), as the original
  does at 60 Hz.

`fit_character.py` fits mix, the shaper, threshold, ratio, knee, attack and release per band and amount node to
tone staircases and bursts; `charsim.dll` (built from BandDynamics.h) is the gain computer the fits call.

### 3.9 The shaper is a sine; the band laws (`nulltest/ident_lib.py`, `fit_bandlaw.py`, `fit_music.py`)

The crossover is known exactly, so the three band signals the original processes can be computed for any input, and
a band's own output is the original's output less the other two bands.

**Shaper.** The output regressed on powers of the band signal, one cycle at a time, gives u - c · u³ + 0.3 · c² · u⁵
…, the series of a sine. A fully driven shaper is blended with the dry band by the amount:

    y = M · (d · u + (1 - d) · sin(k · u) / k)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Memory | none: the harmonics' phases are within 0.1° of the sine's at 300 and 700 Hz | `ident_lib.py` | exact |
| Rate | the processing rate, no oversampling: a 7 kHz tone aliases the same way in both plug-ins (its 5th harmonic at 13 kHz, -81 dB) | tone | exact |
| Mid drive k at 100 % | 2.46 at every level, read on a mid-band tone with L and R in anti-phase (not compressed, so the shaper alone); past k · u = π/2 the output folds over | anti-phase tone | measured |
| Dry share d | 1 - amount / 100 % in the low and mid bands (low 0.73 / 0.47 / 0.23 / 0, mid 0.76 / 0.50 / 0.22 / 0 at 25 / 50 / 75 / 100 %); the drive rises only slowly below 100 % and faster above | `fit_bandlaw.py --shapedry` | at 50 % the low band's H5 is -41 dBc at +4 dBFS where a sine of the fitted drive gives -49; against H3 squared it is 0.62 to 0.73 where a pure sine gives 0.3 |
| Probe fits with d free | low band at 25 %: -64 dB; mid at 25 %: -88 dB (d fixed at 0: -42 / -52 dB) | `fit_bandlaw.py` | |

**Band laws from probes** (`fit_bandlaw.py`): a tone staircase (-40 … +4 dBFS, 3 s steps) and bursts (20 ms, 0.2 s
and 2 s at -24 / -12 / 0 dBFS over a -50 dBFS bed) at 70 Hz, 700 Hz and 8 kHz; free: k, mix, threshold, knee,
ratio, attack, release; the other two bands subtracted through their own fitted laws (at 70 Hz the mid band still
passes the tone at -21 dB and compresses it: treated as linear, the low band fits to -31 dB, with the mid band's law
subtracted to -52 dB); `fit_multistart.py` starts each fit from several detector times and both detector types
(the fits have local minima).

| Band | Detector | Attack / release | Static law | Changes with the amount | Fit |
|---|---|---|---|---|---|
| Low | mean-square | ≈ 1 ms / ≈ 2 s | threshold ≈ -10 dB, knee ≈ 28 dB, ratio ≈ 1.3 | k 2.2 … 2.6, mix | -50 to -56 dB per band and node |
| Mid | mean-square | ≈ 300 ms / 89 ms | threshold ≈ -19.5 dB, knee ≈ 45 dB, ratio ≈ 2.3 | k 0.8 … 3.4, mix 0.27 … 1.0; the other constants stay put | -50 to -56 dB |
| High | mean-square | ≈ 1 ms / ≈ 91 ms | threshold ≈ -10 dB, hard knee, ratio ≈ 3 | k, mix | -50 to -56 dB |

The laws hold away from the probe frequency: the mid law fitted at 700 Hz predicts a 300 Hz staircase to -55 … -74 dB
per step (`compare_prediction.py`), so the detectors hear the same FIR band signals as the audio.

**Band laws from program material** (`fit_music.py`): each band and node fitted against the original on music,
drums, a bass-heavy mix, pink noise and the probes at once, through a Python model of the whole section
(`charmodel_lib.py`, identical to the plug-in to -120 dB). Every start converges to the same law, and the laws come out
the same at every amount:

| Band | Threshold | Knee | Ratio | Attack / release | What moves with the amount |
|---|---|---|---|---|---|
| Low | -9.4 dB | 29.7 dB | 1.33 | 1.0 ms / 2.0 s | drive 1.89 … 2.59, mix 0.19 … 1.0, d |
| Mid | -19 … -20 dB | 44 … 47 dB | 2.3 … 2.7 (2.28 at 100 %, mix 0.716) | 310 … 325 ms / 86 … 88 ms | drive 1.75 … 3.42, mix 0.25 … 1.0, d |

- Between the nodes the laws are interpolated: 37.5 % nulls at -71 dB that way, against -34 dB with laws fitted
  directly at the half nodes.
- The mid laws are refitted with loud signals and two 6 s excerpts of a mastered track (30 s and 44 s) in the set,
  each signal weighed equally in dB (`fit_music.py mid N --loud --track --relative --fixed`); the 200 % node again on
  the path of 3.15.
- The high band's laws are fitted around its measured shaper (3.14) and detector (3.17).
- The fitted laws are in `measurements/Positron/character/bandlaw_final_v13.json`, compiled into the plug-in's band tables.

### 3.10 Stereo: mid-only detectors and a side gain after the shaper (`fit_width.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Detectors | hear the mid only: a tone in anti-phase (pure side) is not compressed at any level; a left-only tone is compressed exactly as a mono tone of half the amplitude (fitted detector scale 0.998) | anti-phase and one-sided tones | exact |
| Shaping | per channel: with a left-only input the right output carries no harmonics | one-sided tone | exact |
| Side gain | applied after the shaper, per band (table below): low-level noise in the left channel only gives both the mid and the side gain of every band | least squares over the exact band signals | -96 dB |
| Position | after the shaper: a left-only tone at 200 % fits to -45 dB that way, -32 dB with the boost before it | `fit_width.py` | measured |

Side gain relative to the mid, in dB:

| Band | 0 | 25 | 50 | 75 | 100 | 125 | 150 | 175 | 200 % |
|---|---|---|---|---|---|---|---|---|---|
| Low | 0 | 0.000 | -0.001 | -0.001 | -0.001 | -0.001 | -0.004 | -0.008 | -0.012 |
| Mid | 0 | 0.004 | 0.008 | 0.011 | 0.014 | 0.015 | 0.339 | 0.801 | 1.240 |
| High | 0 | 0.895 | 1.711 | 2.462 | 3.157 | 3.549 | 3.740 | 3.836 | 3.929 |

At 100 % a left-only signal above 5 kHz leaks into the right channel at -15 dB.

### 3.11 What the nonlinear stages hear (`nulltest/probe_nl_hear.py`)

The FIR bands have shallow stopbands: the mid band passes 8 kHz at -29.5 dB and stays at -28 dB up to 20 kHz (the
complementary remainder of a split whose high band sits 0.3 dB low). Part of each band bypasses its nonlinear stage.

Probe: a quiet tone in the band (-30 dBFS) under a loud interferer (-2 dBFS) stepped across frequency; for each step
the interferer level at the nonlinear stage's input that reproduces the original's probe gain is solved for, the
other bands running through their own laws. Mid band (probe at 700 Hz), in dB re the interferer:

| Interferer | 30 | 70 | 130 | 200 Hz | 1.6 | 2.7 | 3.5 | 5 | 6.5 | 8 | 10 to 16 kHz |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Nonlinear stage hears | -26.6 | -23.0 | -11.0 | -3.2 | -1.4 | -7.4 | -13.8 | -25.4 | -34.4 | -40.5 | ≈ -43 (the method's limit) |
| FIR band passes | -25.5 | -22.0 | -10.5 | -3.1 | -1.3 | -7.0 | -12.6 | -21.8 | -29.9 | -29.5 | -28 |

- Below its band the mid stage hears its FIR band; above the 2.68 kHz crossover it hears a steep Linkwitz-Riley slope.
  Under a loud 8 kHz tone the original changes the probe by 0.06 dB (a mid stage hearing the whole FIR band: 0.6 dB).
- The low band's stage hears its FIR band as far as this probe can tell (to about 300 Hz).

Model: each band's nonlinear stage works on s_b, the FIR band with Linkwitz-Riley edges beyond its band
(NlBandFilters.h, `ident.nl_firs`; the low band uses its FIR band as it is), and the rest of the band passes linearly:

    y_b = M_b · (x_b - s_b + sin(k · n(s_b) · s_b) / k)

The small-signal response is unchanged and exact. Only the mid band's upper edge is steep: a steep low edge for the
high band's stage made the broadband nulls worse, and one for the low band would need more pre-ringing than the
151 samples the delay allows.

### 3.12 Other sample rates (`nulltest/measure_band_rates.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Rank | at 44.1, 88.2, 96 and 192 kHz the nine small-signal IRs again span exactly three filters, with the per-band gains of 48 kHz | rank-3 fit | error below 1e-7 |
| Design | per rate, not resampled: 608 taps at 44.1 kHz, 1216 at 88.2, 1323 at 96, 2647 at 192 kHz | `measure_band_rates.py` | exact |
| Top | at 88.2 kHz and above all bands fall away above about 22.5 kHz | | exact |
| Ours | the original's own filters at those rates (BandFiltersRates.h) | | -89 … -123 dB per band |

With oversampling the 48 kHz filters are redrawn at the processing rate (7).

### 3.13 The high band's detector reads sample peaks (`nulltest/probe_crest.py`, `measure_static_n.py`)

A sine, two tones and band noise at the same RMS through each band:

| | Mean-square detector | Peak-sensitive detector |
|---|---|---|
| Prediction | the same gain for all three | more compression for peakier signals |
| Mid band | observed: ours matches within 0.02 dB | |
| High band | | observed: at 100 % and -10 dB, -1.500 (sine), -2.522 (two tones), -3.235 dB (noise) |

- A single tone cannot tell the two kinds apart, so laws fitted to an 8 kHz tone miss on broadband material.
- The detector reads the sample peaks, not the true peak (read through the measured shaper of 3.14): a steady 12 kHz
  tone is 4 samples per cycle, so its sampled peak depends on its phase. At -9 dBFS the original reduces it by
  1.41 dB at one phase and 1.63 dB at the other (0.89 and 0.93 of the amplitude sampled).
- Ours, a mean square of the samples with a fast attack (about 1 ms) and a slow release (3.17), reacts to peaks the
  same way: -1.502 / -2.522 / -3.241 dB on the crest test at -10 dB.
- The frequency acts on the detector's level only: steady staircases at 6 to 16 kHz are pure shifts of the 8 kHz
  curve (shape error under 0.01 dB). Against the original, ours hears 4 kHz 0.44 dB louder, 4.5 kHz 0.26, 5 kHz 0.09,
  and 6 to 16 kHz 0.11 to 0.18 dB quieter: the original's detector has a steeper low edge than its shaper, about
  0.6 dB at 4 kHz. Not modelled (Declined changes).

### 3.14 The shapers read directly (`nulltest/probe_shape_side.py`, `compare_third_harmonic.py`, `probe_shape_mid.py`)

A tone with L and R in anti-phase is not compressed (3.10), so a band's side output is its shaper alone: plotted
sample by sample against the band signal, it is the shaper's curve. Tones sit where the plug-in reads back its own
settings exactly: 9 kHz (high band), 800 Hz (mid), 25 Hz (low).

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| High band form | with a dry share, d · u + (1 - d) · sin(k · u) / k | side output against the band signal | -92 … -124 dB at every amount (a pure sine: -46 … -57 dB) |
| High band k | rises linearly with the amount: 1.40 at 12.5 %, 1.865 at 100 %, then more slowly to 2.34 at 200 % | `probe_shape_side.py` | measured |
| High band d | falls smoothly from 0.89 at 12.5 % to -0.037 at 100 % and stays near -0.04 above | `probe_shape_side.py` | measured |
| Mid and low bands | below 100 % the program-fitted laws match (k within 1 to 2 %, d within 0.01); above 100 % the mid k reads 3 to 4 % lower than the fitted one, with d = -0.01; the fitted values are kept (Declined changes) | `probe_shape_side.py` | measured |
| Mid and side shaping (γ) | the shaper's distortion, (1 - d) · (sin(k · u) / k - u), reaches the output's mid 1 + γ times as strong as its side; γ grows by 0.0019 per 12.5 % step to 0.0153 at 100 %, peaks at 0.0177 at 137.5 % and is 0.0142 at 200 % | `compare_third_harmonic.py`, `probe_shape_mid.py`; BandParam `shapeMid` | in the mid band the in/anti ratio matches to 0.1 to 0.4 % |

What shows γ: below the threshold a high-band tone in phase has a 3rd harmonic 1.53 % stronger than the same tone in
anti-phase (100 %), at every level from -30 to -15 dBFS, with the same fundamental; a left-only tone splits the
difference exactly (the mid part of its harmonic at the in-phase strength, the side part at the anti-phase one).
NULLTESTS.md: "defaults, bright -8".

**The high band's compressor around the measured shaper** (`fit_music.py high N --shaper --loud --track`): with the
shaper fixed, only the gain computer is fitted, on a program set that includes loud material where the high band
works hardest (drums peaking at -1 dBFS, pink noise at -6 dBFS RMS, music at 0 dBFS, "bright -8", and the two track
excerpts). From 100 % up each signal is weighed equally in dB (`--relative`); below, the plain energy objective
fits better.

- The steady curve matches: read through the shaper on steady staircases (tone, two tones, band noise, -18 … 0 dBFS
  in 1 dB steps, `measure_static_n.py`, `fit_music.py --static`), with γ included, the laws follow the original's curve to
  0.003 dB rms at 12.5 %, 0.019 at 100 %, 0.023 at 87.5 % (0.05 dB after the refits). The remaining high-band
  difference on loud material is in the detector's timing, not in the curve.
- On the mastered track (70 s, 44.1 kHz, about -10 dBFS RMS) the band's gain is right on average (±0.1 dB per 20 ms
  frame); the difference is in how fast the detector moves, at 44.1 and 48 kHz alike and with the irregular host
  blocks FL Studio sends. The band holds most of the section's residual there (84 %, -34 dB relative to the band,
  before the refits of 3.15 and 3.17).
- The gain trace on loud drums (`measure_high_gain_program.py`) is the check for the start and depth of compression through each hit.

### 3.15 What the mid band's gain acts on above its band (`nulltest/probe_cross.py`, `probe_band_path.py`, `probe_mid_edge.py`)

Quiet tones above 1.5 kHz under a loud masker below 1 kHz turn the original down by nothing between 4 and 8 kHz
(`probe_cross.py`; a mid gain applied to the whole steep-edged band of 3.11 turns them down 0.05 to 0.15 dB), and on pink
noise at -18 dBFS the original's high-band gain sits a steady 0.03 dB above such a model's while neither compresses
(`measure_high_gain_noise.py`): the mid band's gain reaches less far up than its nonlinear stage's input.

Probe (`probe_band_path.py`): quiet tones (-50 dBFS, 60 frequencies from 0.9 to 18 kHz, too quiet to move any detector) under
a loud in-band masker (pink noise, 250 to 700 Hz, -6 dBFS RMS), and the masker alone. Each tone's complex change (with
the masker, less alone, less the masker's own output) is the band's gain change times the response of the path the
gain is applied through. Normalised at 900 Hz; the plug-in reads its own path to within 0.05 dB this way.

The original's path relative to the FIR band with the Linkwitz-Riley edge of 3.11, at 100 %:

| | 2.0 | 2.75 | 3.5 | 4.6 | 5.9 | 7.6 | 9.8 | 12.6 | 16.3 kHz |
|---|---|---|---|---|---|---|---|---|---|
| Level (dB) | -0.12 | -0.44 | -1.27 | -2.77 | -3.79 | -5.39 | -7.87 | -14.1 | -21.4 |
| Phase (degrees) | -1 | -1 | 0 | +11 | +59 | +188 | +318 | +483 | +724 |

- It falls faster than the edge and leads in phase above 4 kHz, as if that part of the path were about 8 samples
  shorter.
- It is one filter fixed in Hz: the same at 44.1, 88.2, 96 and 192 kHz (within 0.08 dB and 0.4 degrees below
  10 kHz) and at 50 and 200 % (0.02 dB).
- The other edges match: the high band's low side within 0.05 dB above 900 Hz. The mid band's low side differs by up
  to 0.45 dB below 100 Hz, where the path is 20 dB down (Declined changes).

Model: the measured ratio is applied to the mid band's nonlinear-stage filter from 900 Hz up (`ident.nl_firs`,
NlBandFilters.h and BandFiltersRates.h at every supported rate), no law refitted for it. NULLTESTS.md: "char: pink
-18, 100 %", "char: pink -6, 100 %", "char: drums -6, 100 %", "char: music -10, 50 %" and "100 %".

**The mid shaper's drive.** Tone staircases at 300, 500, 700 and 1000 Hz (`measure_mid_static.py`, 100 %) show the band's
steady gain within 0.01 dB of the original's from -44 to +4 dBFS, with the 3rd harmonic 0.37 dB too strong at low
levels at every frequency: the drive, not a filter. The fitted k (2.514) is 2 % above the 2.445 read with anti-phase
tones (3.14); the measured drive fits worse on program material (Declined changes), so the fitted drive compensates
for a mid-band difference not yet found (8).

**The high band against the mid band of 3.15.** Its gain on pink noise at -6 dBFS follows the original's at a
correlation of 0.993 (0.974 before the mid path was measured). The nodes at 100, 125 and 175 % are refitted on it;
25, 150 and 200 % keep their laws (Declined changes).

### 3.16 The detectors' release, read from tone drops (`nulltest/measure_mid_release.py`, `measure_mid_times.py`, `measure_high_release.py`, `fit_high_static.py`)

Probe: a steady tone in one band (700 Hz for the mid band, 8 kHz for the high band) drops from a loud level to a
quiet one; the other two bands are taken off the output through their laws, the rest inverted through the band's
shaper (3.14) and read as the band gain, one median per cycle; through the band's steady curve the gain becomes the
detector's level, whose slope after the drop is the release. The plug-in reads back its own release this way to
within 0.2 ms.

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Mid release | one fixed speed: after a drop to -45 dBFS the level falls at a steady 48.2 dB/s from 0 or -20 dBFS, a mean-square release of 90.0 to 91.0 ms at every amount from 25 to 200 % | `measure_mid_release.py`, `measure_mid_times.py` | measured |
| Mid attack | agrees with the fitted laws within 3 % | `measure_mid_times.py` | measured |
| Mid laws | keep their program-fitted release, 84.7 to 88.2 ms (the release shows only in quiet tails, which carry almost no energy; Declined changes) | `fit_music.py` | |
| High release against drop depth | shallow drops release slowly, deep ones never faster than about 48 dB/s (47.2 to 48.1 dB/s from 25 to 200 %) | `measure_high_release.depth_slopes` | measured |
| Hold time | how long the tone was held before the drop (30 ms to 3 s) changes nothing: no slow second detector shows here | `measure_high_release.py` | measured |
| High steady curve | fitted directly to a 0.5 dB staircase with one sample-peak detector it matches to 0.012 dB rms | `fit_high_static.py` | measured |

High band, after a drop from 0 dBFS (100 %, the slope 20 ms after the drop):

| Drop to (dBFS) | -3 | -5 | -7 | -9 | -11 | -15 | -21 | -45 |
|---|---|---|---|---|---|---|---|---|
| Original (dB/s) | -31 | -36 | -39 | -41 | -42 | -43 | -44 | -44 |
| Positron (dB/s) | -33 | -39 | -42 | -44 | -46 | -47 | -48 | -48 |

### 3.17 The high band's detector releases on the power (`nulltest/probe_gr_drop.py`, `fit_music.py --ms --hidrops`)

The release table of 3.16 is what a one-pole release on the square of the signal gives: after a deep drop its level
falls at 4.34 / τ dB/s, and more slowly when the new level is close to the old one, because the decaying power adds to
the new level's. Simulated on the tone drops of 3.16 (slope 20 ms after the drop, the release time fitted per
detector):

| Drop to (dBFS) | -3 | -5 | -7 | -9 | -11 | -15 | -21 | -45 |
|---|---|---|---|---|---|---|---|---|
| Original (dB/s) | -31 | -36 | -39 | -41 | -42 | -43 | -44 | -44 |
| One-pole on x², τ 98 ms | -31 | -36 | -39 | -41 | -42 | -43 | -44 | -44 |

A one-pole on |x| gives -22 dB/s for the drop to -3 dBFS and one on x⁴ gives -38, both -44 for the deep drops.

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Detector | mean-square at every amount (`characterDetectorPeak` off), its slow second detector kept, no fall limit (`fallRate` 0) | `probe_gr_drop.py`, `fit_music.py` | |
| Release | 88.5 to 91.0 ms at every amount (the tone drops alone give 98 ms; program material prefers a little faster) | `fit_music.py high N --shaper --loud --track --hidrops --ms --set fallRate=0 --fixed bandlaw_final_v11.json`, `--relative` from 125 %, 8 kHz tone drops in the set, at 200 % pink noise at -10 dBFS RMS with another seed than the stress suite's (`--pink10`) | fit objective -53.87 dB at 100 %, -49.15 at 200 % |
| Laws | `measurements/Positron/character/bandlaw_final_v13.json` | | |

NULLTESTS.md: "defaults, sweep -6", "defaults, drums -1", the mastered track. The sweep at -6 dBFS nulls at -56 to
-66 dB in the crossover region (1.5 to 3.5 kHz), within 0.013 dB of the original's level (`nulltest/probe_sweep_residual.py`,
50 ms windows).

### 3.18 The mid band on loud material (`nulltest/probe_mid_det_spectrum.py`, `probe_mid_det.py`, `fit_music.py`)

The mid band reduces loud pink noise a steady 0.04 dB more than the original (`measure_high_gain_noise.py --band mid`; pink noise at
-6 dBFS, "char: pink -6, 100 %"), and its fitted drive sits 2 % above the measured one (3.15).

**What the detector hears** (`probe_mid_det_spectrum.py --map`: a 700 Hz probe at -40 dBFS rides on a steady sine pump; the
probe's gain is the band's reduction, read back through each plug-in's own in-band curve as a level). In band (300 Hz
to 2 kHz) Positron reads the pump within 0.02 dB of the original; below the band it reads it louder, more at higher
levels; above 2.4 kHz slightly quieter:

| Pump | 60 Hz | 90 Hz | 120 Hz | 157 Hz | 200 Hz | 300 Hz | 3 kHz | 4 kHz |
|---|---|---|---|---|---|---|---|---|
| At -12 dBFS, Positron less original (dB) | | | +0.27 | +0.10 | +0.04 | 0.00 | 0.00 | -0.02 |
| At -6 dBFS | +0.60 | +0.74 | +0.38 | +0.17 | +0.07 | +0.01 | -0.05 | -0.07 |
| At 0 dBFS | +0.86 | +1.01 | +0.58 | +0.27 | +0.11 | +0.02 | -0.08 | -0.07 |

The measured drive in place of the fitted one changes none of these by more than 0.01 dB. A filter cannot explain a
difference that grows with level, and a highpass in front of the mid detector costs music (Declined changes): on
program material the mid detector hears the bass as the original's does, and the low-side difference under a steady
pump is not identified (8). On the sweep at -6 dBFS the same difference shows as 0.014 to 0.025 dB more reduction from
157 Hz to 1.5 kHz, where the sweep nulls at -53 to -54 dB (`probe_sweep_residual.py`).

## 4. Limiter (`measure_limiter.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Gain law | small-signal gain = knob dB - 0.1 dB (0 → -0.10 dB, 5 → +4.90, 12 → +11.90); flat 20 Hz to 20 kHz | tones | exact |
| Ceiling | -0.10 dBFS sample peak (-0.101 for noise, pink noise and sines at 1 to 15 kHz, at any knob setting) | `measure_limiter.py` | exact |
| True peak | not limited: inter-sample peaks reach +0.25 dB (9 kHz sine), +0.53 (pink noise), +2.0 dB (white noise); true-peak (4x) value up to +2.4 dBFS | `measure_limiter.py` | measured |
| Look-ahead | 38 samples of delay; the gain starts falling 19 samples before the first loud sample reaches the output | clicks | exact |
| Attack ramp | over those 19 samples 1/gain rises linearly: the detector level is a linear ramp, like a box filter over the look-ahead | clicks | exact |
| Fast release | when a short overload ends, part of the reduction returns within 8 to 16 samples | bursts | measured |
| Slow release | (1/gain - 1) decays exponentially with τ = 0.3778 s, from 50 ms to 2 s after the end, for 6.6 and 11 dB of reduction | bursts | measured |
| Program dependence | the slow part charges over the overload (τ ≈ 25 ms on a DC step): after a 5 ms overload it holds 3.4 dB, after 20 ms 7.7 dB, after ≥ 0.3 s all 11 dB | bursts | measured |
| Linking | stereo-linked: a quiet R pilot gets -10.2 dB while L is limited by 10 to 11 dB | pilot tone | exact |
| Static, 1 kHz sine | output peak -0.107 dBFS, fundamental -0.093 dBFS (a slightly squared waveform) | tone | measured |

The first model these readings gave, gain = 1 / max(fast, slow) with a box-smoothed windowed peak over the look-ahead
and a slow envelope charging with τ ≈ 25 ms and relaxing to 1 with τ = 0.378 s (levels relative to the ceiling,
0.98855), is refined by the algorithm of 4.1.

### 4.1 The algorithm, identified with probes (`nulltest/probe_limiter.py`)

Isolated clicks, click pairs and trains at chosen spacings and heights, the gain trace read back sample by sample.
The model reproduces the probes to 0.0007 in gain and the trains to an RMS error of 0.00035.

Every level is in units of the 0 dBFS ceiling and never less than 1. The gain is `trim / env`, trim = -0.1 dB; env is
the largest of three things:

1. **The level of the outgoing sample**: its inter-sample peak over [n, n + 1), from a 16-phase Kaiser-windowed sinc
   interpolator (taps and window per rate, below). The ceiling holds on the samples, not on the true peak. On the
   samples the original reads 1.00014 times the sample (`limLevelScale`: an effective ceiling 0.0012 dB lower).
2. **A straight-line plan through the coming peaks.**
   - Only local maxima of the level are targets.
   - When a plan ends, the next heads for the nearest peak within the window ahead (21 samples at 48 kHz) and reaches
     it exactly on arrival; a farther, higher peak does not steepen the line.
   - With no peak ahead the plan falls toward 1 over the release (22 samples at 48 kHz) and stops at the slow
     envelope if it meets it. Right after a peak it falls toward the level 22.9 samples ahead (interpolated there;
     the flank of a peak still beyond the window), so it meets the next rise instead of overshooting below it.
   - A running plan toward a peak changes only when a level within its span rises above its line; it then re-plans
     to the steepest such point.
   - A release watches the whole window, its line continued at 1 past its end: a second peak 24 to 40 samples after
     the first ends the release as soon as it comes within the window, and the release turns into a straight line
     up (or down) to it instead of dropping toward 1 and jumping back.
   - An idle limiter (no plan, state at or under the slow envelope) rests on the slow envelope.
3. **A slow envelope**: it charges toward the level with τ = 24.47 ms; when the level is lower it relaxes toward the
   current level (1 when quiet) with τ = 377.8 ms.

A pair of peaks exactly 24 samples apart still differs for the first 3 samples after the first peak.

**Per rate.** The window and the release are not scaled from 48 kHz; probed at each rate:

| Rate (kHz) | 44.1 | 48 | 88.2 | 96 | 192 |
|---|---|---|---|---|---|
| Look-ahead (samples) | 40 | 38 | 50 | 54 | 96 |
| Window | 19 | 21 | 39 | 43 | 86 |
| Release (samples) | 20 | 22 | 40 | 44 | 87 |

The single-peak and pair probes match to 0.004 at 96 and 192 kHz. Pairs exactly one sample beyond the window still
differ at 44.1 and 88.2 kHz: after a peak the original appears to look one sample further than its attack from idle.

**The interpolator per rate** (`nulltest/null_lim_rate.py`). None of the time constants (window, release, reach, slow
envelope) improves the nulls when changed; the interpolator does. Over a grid of Kaiser taps and window β, scored on
five signals (drums peaking at -1 dBFS, pink -6, a track excerpt, drums at 12 dB input gain, music -2), the good
settings lie on a narrow ridge along which the window's Gaussian core, σ = (taps / 2) / √β, stays the same: 4.4
samples at 44.1 kHz, 3.5 at 48 kHz, 1.3 to 1.8 at 88.2 kHz and above. The original's kernel is neither one fixed
length in samples nor one scaled with the rate. The high-rate surfaces are spiky on drums (single events on
near-ties), so they were chosen by the mean.

| Rate | Taps, β | Five-signal mean (dB) |
|---|---|---|
| 44.1 kHz | 28, 10 | -68.2 |
| 48 kHz | 24, 12 | -69.2 |
| 88.2 kHz | 12, 11 | -52.1 |
| 96 kHz | 12, 14.5 | -56.7 |
| 192 kHz | 10, 16 | -55.4 |

**The level estimate against the original's readings** (`nulltest/probe_lim_pulse.py`, `probe_lim_interp.py`, `limiter_lib.py`, `probe_lim_nl.py`):
an isolated pulse above the ceiling is planned to exactly its level, so at its loudest point output / input =
trim / level. On 3873 isolated pulses (1084 of them raw bursts 2 to 6 samples long):

| Estimator | Error, band-limited pulses (rms) | Raw bursts |
|---|---|---|
| The shipped 24-tap Kaiser sinc, 16 phases | 3.4e-4 | 7.6e-4 (2.1e-3 on the 3858-pulse set) |
| The same at 8 / 32 phases | 3.0e-3 / 9.4e-4 | |
| Best free linear table, 16 phases | 3.3e-4 | 1.7e-3 |
| Free tables of 16 / 64 / 128 taps, 16 phases | | 1.7e-3 / 1.7e-3 / 1.8e-3 |
| Free table, 32 phases | 5.6e-4 | 1.2e-3 |
| Free table, 8 phases | | 3.8e-3 |
| Parabola through the peak and its neighbours | 0.13 | |
| Catmull-Rom cubic | 0.12 | |
| Polyphase 4x upsampler | 0.012 | |

No linear interpolator is left to gain from; on short raw noise bursts the original's readings differ from any 16- or
32-tap linear table by up to 2 to 3 %. The plan rule is right as stated: in a Python copy of the limiter that matches
the plug-in exactly, every variant (peaks of the sample magnitudes, peaks over two neighbours, a minimum prominence,
the steepest reachable peak) is far worse (pink noise -21 … -29 dB against -47.5).

**How far the limiter can null** (`nulltest/probe_sensitivity.py`): the original against itself, white noise added to pink
noise at -6 dBFS (5 dB into the limiter). Noise at -140 or -120 dBFS moves its output by -132 / -113 dB, as a linear
stage would; at -100 dBFS by -67.5 dB, at -80 dBFS by -57.5 dB. A difference of a ten-thousandth in the level changes
plan decisions (near-ties: a local maximum 0.001 above its neighbour that the original does not count as one), and
the model matches the original's levels to 3.4e-4. So "lim: pink -6, gain 5" (-54.82 dB) is at the floor any model
short of a bit-exact copy reaches. Music at -2 dBFS through the whole chain is not like that (-100 dBFS of noise
moves it by -87 dB): its residual is a model difference, mostly the mid band (3.18). At 96 kHz one recurring event in a
drum loop nulls to only -35 dB: a 1e-4 DC pilot changes the original's output there by orders of magnitude more than
its size, so its peak planning sits on a tie.

**At the maximum input gain** (12 dB, `null_lim_max.py`): the limiter alone nulls music at -2 dBFS to -55.8 dB, drums to
-78.4, pink -10 to -58.7, music at -10 dBFS to -96.8; the full chain music -10 -61.2, music -2 -53.1, drums -6 -51.9,
pink -10 -43.2 (-43.1 with the 100 % high-band refit of 3.14). 94 % of the residual sits in 5 % of the time: single plan
decisions (a plan that starts a few samples later, a release restarted from a slowly falling level). The slow envelope's
times are sharply optimal there. Through the whole chain at 12 dB the character section's small differences are
amplified by the limiting (music -10: -69.4 dB character only, -57.1 full chain); a small change in the character
section's output reaches the output about 17 dB larger after the limiter (drums peaking at -1 dBFS at 44.1 kHz: a change
of -58.4 dB in the section's output became -41.6 dB after the limiter, 5 dB into it).

NULLTESTS.md: "lim:" cases, the stress group "limiter gain", the mastered track "limiter only".

## 5. Parameter smoothing (`measure_smoothing.py`)

Method: a steady quiet tone, one parameter jumping at a 64-sample block boundary. Times from the change at the input,
the raw path delay included (3.2 ms with the limiter off, 4.0 ms on):

| Parameter | 10 % / 50 % / 90 % / 99 % (ms) | Shape |
|---|---|---|
| Input Gain 0 → +12 dB | 5.3 / 9.5 / 22 / 43 | smoothed; the longest |
| Output Gain 0 → -12 dB | 1.8 / 10.2 / 28 / 50 | smoothed; no path delay (applied at the output) |
| EQ Mid / Low Gain | 4.7 / 7.9 / 11.1 / 12.4 | ≈ 8 to 10 ms ramp |
| Character 100 → 200 % / → 0 % | 1.5 / 4.8 / 8.1 / 8.9 | ≈ 8 ms ramp, starts before the 3.2 ms path delay |
| Limiter Input Gain 5 → 12 dB | 1.5 / 4.8 / 9.4 / 10.6 | ≈ 9 ms ramp |
| EQ Bypass | switches at 7.0 to 7.4 | instant, no crossfade |
| Character Bypass | switches at 1.1 to 1.7 | instant, no crossfade |
| Limiter Bypass | instant | the 38-sample delay changes at once (it can click on program material) |
| Bypass (main) | instant | |

### 5.1 The control rate (`nulltest/null_steps.py`, per-sample envelopes of steady tones)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Chunks | each host block is cut into chunks of up to 128 samples, counted from the block's start (64-sample blocks: 64-sample chunks) | `null_steps.py` | exact |
| Input and output gains | one-pole smoothed once per chunk by chunk/τ of the remaining distance in linear gain (forward Euler, τ = 478.8 samples, about 10 ms); the gain ramps linearly between chunk ends (the output's slope is piecewise constant in 128-sample pieces) | `null_steps.py` | input-gain steps of +12, +6 and -12 dB at blocks of 64 and 128 to within 0.0005 in gain |
| Input gain, first stage | the parameter ramps linearly in dB over 237.6 samples (about 5 ms), read at each chunk's end (in the first chunk after a change the target is about halfway); the output gain has no such ramp | `null_steps.py` | as above |
| EQ gains and the amount | the same 5 ms parameter ramp read at chunk ends, then a linear glide over 5 ms to each new value, re-planned only when the value changes: a slower first chunk, then a straight line to the end, about 368 samples after the change; the EQ is state-variable filters whose gain glides in linear amplitude | `null_steps.py` | the gliding response matches; direct forms do not |
| Limiter input gain | a linear ramp over 10 ms in linear gain, no chunking | `null_steps.py` | within 0.003 dB |
| EQ switch | follows its own 5 ms ramp and takes effect at the start of the chunk after the one in which the ramp crossed half way (512-sample blocks: 128 samples after the block start) | `null_steps.py` | exact |
| Character and limiter switches | at once; while off they do not run, and switched back on they start from silence (detectors at rest, empty filter and look-ahead buffers) | `null_steps.py` | the bypass toggles null at -60 dB this way, -31 dB with the stages kept running |
| Amount 0 | the character section's detectors keep running: a jump from 0 % settles as fast as one from 100 % | `null_steps.py` | exact |
| Host blocks under 128 samples | the switches of the oversampled section (EQ and character on/off) take effect once a control chunk's worth has gathered: 128 - n rounded up to whole blocks later (96 samples at 32-sample blocks, 64 at 64, 96 at 96) | `null_steps.py` | bypass toggles at 64-sample blocks -57.8 dB; every stress case at 64, 333 and 4096-sample blocks nulls as at 512 |

NULLTESTS.md: the stress group "automation" at blocks 512, 64 and 4096; the mastered track's switched cases.

## 6. Meters (`measure_meters.py`, RefCapture films)

### Band gain-reduction meters

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Bars | 33, each fully on or off (no partial brightness): floor(5.5 × GR), 33 bars over 6 dB, no bar under 0.18 dB, none forced on (`gr_bars.png`) | films of per-band tone staircases and a pink-noise ramp, the band's reduction from the model (`nulltest/measure_stair_gr.py`, `measure_gr_meters.py`) | bar for bar where the model's reduction agrees |
| Readings | 8 kHz at -6 dBFS: 4.7 dB, 25 bars; 100 Hz at 0 dBFS, low band: 2.8 dB, 15 bars; the mid band is pinned at 33 bars for 7.1 dB and more | films | measured |
| Quantity shown | the band's internal (wet-path) reduction, larger than the net change of the audio (1 kHz at -6 dBFS reads 7.1 dB while the fundamental drops 4.9 dB) | films, 3.8 | measured |
| Rise | follows the band's attack: high and low reach their count within one frame (< 30 ms), mid takes ≈ 0.1 s to fill | films | measured |
| Fall | follows the band's release: mid 33 → 1 bars in ≈ 0.5 s after a 0.1 to 0.4 s hold; high ≈ 0.2 s; low ≈ 1 bar per 0.5 s | films | measured |
| Marker | one more bar at the deepest reduction the readout holds (until clicked), on a 20 dB scale (1.65 bars per dB): after a high-band tone at -4 dBFS (6.1 dB) at bar 10, after -2 dBFS (7.5 dB) at 13; the filled bars fall back to the actual reduction (a quiet bed and digital silence alike; band gains on the bed match the model's to 0.05 dB) | films | measured |

**Targets.** Each target fills with the band's reduction itself, not with where its bracket is drawn: full over a range,
fading linearly over about 0.22 dB at each end. Fitted to the staircases and the ramp together:

| Band | Full | Edge |
|---|---|---|
| high | 0.34 … 1.38 dB | 0.25 dB |
| mid | 2.45 … 3.98 dB | 0.22 dB |
| low | 0.97 … 2.46 dB | 0.21 dB |

Lit, a target is two filled blocks, the upper U (meter y - 10 … - 2) and the lower U (+ 10 … + 18), with the bar row
passing between them.

### I/O LED meters

Ramp film, every LED read per frame (`read_leds.py`); the meter redraws about 22 times a second.

| Part | Law | Confidence |
|---|---|---|
| Green bar | the plain RMS (one-pole on x², 150 ms), not the AES value the readout shows | within ±0.15 dB on rising, steady and falling levels |
| Mint run | from the green bar's top to a fast peak (\|x\| follower, 1 ms attack, 50 ms release; about 2 dB under the 10 ms sample peak) | measured |
| Held peak | one mint LED at the peak readout's held value (until clicked); not drawn once that is above 0 dBFS (the readout red) | measured |
| Input target | fills with the same fast peak (either channel): full from -12 to -3 dBFS, fading over 1.5 dB (one LED) at each end; off at LED 29, half at 30, full 31 … 36, half at 37, off from 38 | read frame by frame against the original's own LEDs |

### Numeric readouts

| Readout | Law | Method | Confidence |
|---|---|---|---|
| Band and limiter readouts | hold the deepest GR so far: mid -7.1 (1 kHz -6 dBFS), -9.9 (0 dBFS), -13.1 (+6 dBFS); high -4.7; low -2.8; limiter -0.1, -1.4, -3.0 for the same bursts at the defaults | films | measured |
| RMS readout | live, not held; updates every 0.231 s; the plain RMS (one-pole on x², 89 ms) + 1.5 dB; in silence falls exactly 11.27 dB per update (48.7 dB/s); below -96 dB reads -inf (-96.0 is shown, the next step is -inf); rises within one update (the second update after an onset within 0.1 dB) | `probe_readout.py` (tones, noise, bursts, steps, pulse trains, DC, repeated runs, a fade, 30 s of music), `read_readouts.py` | 0.5 dB rms on music, 0.55 dB rms on steady probes; the original spreads ±0.3 dB between identical runs (a -6 dBFS 1 kHz tone read -7.2, -7.3, -7.3, -7.7) |
| RMS readout, not modelled | signals of constant magnitude read higher (an fs/4 tone at 45° and DC: +2.1 … +2.6 dB over their RMS); sparse pulse trains only +0.3 … +0.6 dB | `probe_readout.py` | measured |
| Peak readout | the sample peak, held until clicked, but sampled: about every 46 ms it takes the latest block's peak, so peaks in the blocks between are never seen (music with +2.12 dBFS overs read +0.9, a 480-sample block whose peak was +0.93; the onset spike of a tone at the output, -0.1 dBFS with a steady peak of -2.6, read -1.3); output readings match block peaks with blocks offset about 230 samples from the host's; input readings match no block of the raw input at any offset (the input meter may see a slightly filtered signal; sines read their peak exactly) | films | measured |
| Position | after the gains: input readouts after the input gain, output readouts after the output gain (-12 dBFS in, +6 / -6 dB gains: input -6.0, output peak -7.3) | films | exact |
| Display | rounded to 0.1 dB (-2.67 shows -2.7); a positive peak turns red | films | exact |

**Short-term LUFS mode** (`nulltest/probe_lufs.py`; films with the settings page switched to Short-term LUFS & Peak and
back, the readouts read frame by frame):

| Quantity | Value | Confidence |
|---|---|---|
| What it shows | the short-term loudness of both channels together (ITU-R BS.1770: K-weighting, a 3 s window), the same value in each channel's box; the peak readout unchanged; a 1 kHz tone at -20 dBFS on both channels reads -20.0 LUFS, not the -23.0 of one channel | exact |
| Accuracy | fifteen tones (1 kHz at -40 to 0 dBFS, 31.5 Hz to 16 kHz at -20 dBFS), each from silence: the highest reading of each matches the standard within 0.1 dB (31.5 Hz -0.02, 4 kHz +0.02, 1 kHz at -30 dBFS -0.1), none above it; the others up to 1.0 dB under, read before the window was full | measured |
| Update | about every 0.70 s (every third tick of the RMS readout's 0.231 s), on a window ending at the update (within about 0.15 s): a 1 kHz tone at -20 dBFS reads -27.0, -23.6, -21.8 at 0.63, 1.32 and 2.03 s after its onset (a 3 s window: -26.8, -23.6, -21.7); after pink noise at -10 dBFS stops it reads -8.6, -10.0, -11.9, -15.2, then -inf 3.1 s after the stop | measured |
| Not modelled | the text sometimes stays unchanged for seconds while the loudness moves (after a tone it held -27.8 instead of reaching -inf; across a change of frequency at a constant level it held for 10 s): the editor not redrawing it | measured |
| Positron (`Source/Loudness.h`) | K-weighting designed for the host rate from the standard's analog parameters, 3 s in 10 ms bins, both channels summed, shown every third RMS update; on the same fifteen tones it reads the standard's value (1 kHz at -20 dBFS: -20.0; 63 Hz: -23.4, the standard -23.35); PositronTests checks 1 kHz and 100 Hz at 44.1 and 48 kHz, the half-filled window and its emptying | tests |

### Limiter meter (`nulltest/measure_dash_meter.py`)

Films of a 1 kHz tone through the limiter alone at 12 dB input gain, rising in 0.5 dB and then 0.1 dB steps, the
reduction read from the output. 31 dash cells on a 4 px pitch from y 90 per channel.

| Part | Law | Confidence |
|---|---|---|
| Marker | at cell ceil((over - 0.05) / 1.5), `over` the limiter's input above 0 dBFS (the reduction without the 0.1 dB trim): cell 0 at no reduction, cell 1 from 0.1 dB over (not at 0.0), cell 2 from 1.6 (not at 1.5), … cell 8 at 11 to 12 dB (not yet 9 at 12.0); the 0.05 dB is the middle of what the steps allow; it holds the deepest reduction, like the readout above it | measured |
| Bar | from cell 0, following the current reduction, one cell shorter than the marker's position: a steady reduction shows the bar, one dark cell, then the marker (12 dB: cells 0 to 6 and 8); when the input stops the bar falls back over about 1.1 s with the limiter's release and the marker stays | measured |
| Positron | the same bar and held marker in its own style: on both probes its cells match the original's at all 50 steps, and after the input stops its bar falls back on the same frames (0.10 to 1.07 s against 0.11 to 1.07 s) | filmed |

## 7. Oversampling (`measure_oversampling.py`, `fit_oversampling.py`, `measure_os_rates.py`, `fit_os_rates.py`)

The setting is switched through the original's own settings page and restored to 1x afterwards.

| | 1x | 2x | 4x | 8x |
|---|---|---|---|---|
| Latency (48 kHz) | 189 | 212 | 217 | 219 |
| Bypassed path at 20 / 22 kHz | 0 / 0 dB | -0.53 / -3.3 dB | -0.53 / -3.1 | -0.53 / -3.1 |
| Character 200 %, 9 kHz at -3 dBFS: alias at 21 kHz (H3 folded) | -32.7 dBc | -54.2 | -54.3 | -54.3 |
| Same, alias at 3 kHz (H5 folded) | -77 dBc | -96 | -111 | -126 |
| Character 100 % small signal, 1 kHz at -6 dBFS, gain | -1.351 dB | -1.349 | -1.348 | -1.350 |

Oversampling adds only the up- and downsampling filters (a top-octave roll-off) and less aliasing; the dynamics and
the small-signal response below 15 kHz do not change.

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Extra delay at 48 kHz | 22.488 / 27.711 / 29.655 samples at 2x / 4x / 8x (group delay at 1 kHz) | `measure_oversampling.py` | measured |
| Design rule | stage k runs at 2^(k+1) times the host rate and is designed when prepared: a Kaiser-windowed sinc cut at a quarter of the stage's rate (a half-band filter), length and window from the textbook Kaiser formulas for a transition band (a passband edge and its mirror image) and a stopband depth, unit gain at DC; filters, latency and top octave change with the host rate | `fit_oversampling.py`, `fit_os_rates.py` | |
| Edge and depth | 17 kHz, 100 dB: at 48 kHz any edge from 16.7 to 17.1 kHz with 100 dB gives the measured lengths (45 / 21 / 17 taps) and the path to 0.03 dB; 44.1 kHz narrows the edge to 16.9 … 17.0 kHz (57 / 23 / 17 taps) | `measure_os_rates.py` | the whole path to 0.000 dB at 44.1, 48, 88.2 and 96 kHz and every ratio |
| Simulated path | upsample, the fixed delay with its fraction at the high rate, downsample; because of the fractional delay between up- and downsampling the folded image does not add in phase (a filter designed as if it did is off by 2 dB at 20 kHz at 2x) | `fit_oversampling.py` | within 0.002 dB and 0.2° up to 23.9 kHz at all three ratios |
| Reported latencies | e.g. 44.1 kHz 1x / 2x / 4x / 8x = 179 / 207 / 213 / 215, 96 kHz 357 / 367 / 371 / 373 | host report | exact |
| Residual delay | a fraction of a sample per rate and ratio after the filters (-0.14 … +0.71), tabulated | `fit_os_rates.py` | |
| 8x | the original's 8x output equals its 4x output two samples later (-82 dB below 16 kHz), so Positron processes 8x at 4x; its bypassed path alone is 1.95 samples later than 4x, but with the character on exactly 2.0 nulls best (music -64.8 against -45 dB) | renders | measured |
| Character path offset | with oversampling the character path keeps its ~22.5 kHz low-pass and sits later than the bypassed path, refined per rate on drums and pink (the nulls move about 10 dB per 0.002 samples; both signals agree): 44.1 kHz +0.010 / +0.033 / +0.033, 48 kHz +0.014 / +0.040 / +0.040 (0.012 / 0.040 at first reading), 96 kHz +0.052 / +0.160 / +0.040 samples at 2x / 4x / 8x; 88.2 kHz treated like 96 kHz (not measured with music) | `null_oversampling.py` | measured |
| Character crossover with oversampling | above 48 kHz the host rate's own filters (at 96 kHz its 96 kHz filters redrawn at the processing rate: drums -41 dB against -36 with the 48 kHz ones); at 44.1 kHz the 48 kHz filters redrawn (-59 against -31 dB) | `null_oversampling.py` | measured |

NULLTESTS.md, "Oversampling".

## 8. Open

- **Loud, dense material in the mid band** (3.15, 3.18): a steady 0.04 dB more reduction than the original on pink noise
  at -6 dBFS RMS; the fitted drive 2 % above the measured one with the measured drive fitting worse; under a steady low
  pump Positron reads 0.3 to 1 dB louder, rising with level, which no filter explains. NULLTESTS.md: "defaults, pink -6"
  (44.1 kHz, 96 kHz, 88.2 kHz rows too), "defaults, drums -1" (-64.2 dB at 44.1 kHz), the mastered track.
- **Pink noise at -10 dBFS, character only, 200 %**: the worst stress case (NULLTESTS.md, "char only 200 %, pink -10").
- **Limiter near-ties** (4.1): dense, continuous limiting is at the original's own sensitivity floor; at 96 kHz one
  drum event sits on a tie; pairs one sample beyond the window at 44.1 and 88.2 kHz.
- **The high band's detector edge** (3.13): about 0.6 dB steeper at 4 kHz than its shaper's.

## Declined changes

| Change | Measured effect |
|---|---|
| A Linkwitz-Riley 2nd-order crossover | fits the masker test ten times worse (3.1) |
| A frequency-sampled redesign of the 48 kHz FIR bands at 44.1 to 192 kHz | -23 to -57 dB per band, worst the high band near the top (the original's own filters: -89 … -123 dB) |
| Band laws fitted directly at the half nodes instead of interpolated | 37.5 %: -34 dB against -71 dB |
| A steep low edge on the high band's nonlinear stage | broadband nulls worse (3.11) |
| The mid and low shapers at their measured k and d above 100 % | music at 200 % -62.3 → -61.2 dB |
| Each node refitted on the music set and the steady curve together | at most amounts the music objective slightly worse; kept only at 100 % (3.14) |
| A first-order highpass in front of the high band's detector, fitted with the law (`--dethp`) | went to its lower bound: no filter |
| A detector-only highpass on the high band without refitting (`probe_det_edge.py`) | program nulls change by under 1 dB either way |
| The mid band's low-side path difference (up to 0.45 dB below 100 Hz) applied | music at 100 % -75.1 → -67.8 dB |
| The mid laws refitted at 25 to 175 % on the path of 3.15 | fit objective 0.05 to 0.2 dB, stress median -66.0 → -65.8 dB |
| The mid compressor fitted with the measured drive (`fit_music.py --shaper`) | worse at every node (100 %: -57.4 against -60.8 dB in the fit) |
| Dry and compressed shares shaped apart, (1 - mix) · F(s) + mix · F(wet · s), with the measured drive | -52.4 dB in the fit |
| The mid release held at the measured 90.1 ms, tone steps added (`--steps --set release=90.1`) | -60.25 against -60.64 dB in the fit |
| A first-order highpass in front of the mid detector only (`probe_mid_det.py`) | pink -6 -47.6 → -49.8 dB at 120 Hz, music and drums 4 to 22 dB worse |
| A second-order highpass in front of the mid detector (0 dB at 700 Hz, `probe_mid_det.py fc/2`) at 40 / 55 / 66 / 80 Hz | pink -6 0.04 to 0.3 dB better; music -10 -75.1 → -69.7 / -65.3 / -63.0 / -61.2 dB, the bass line 3 to 12 dB worse |
| A smoothing of the mid band's reduction in dB (`--gr`) | fits to 0.06 / 4 ms: -43.60 against -43.58 dB, drums -1 -58.6 against -58.9, pink -6 -47.2 both; with the drive free it fits to 2.9 ms (-52.44 against -52.25, pink -6 -47.5 against -47.6) |
| The mid band as an instant level, the static curve, then attack and release on the reduction | -40.95 against -43.58 dB, drums -1 -44.6, pink -6 -44.5 |
| The high band's measured steady curve with one sample-peak detector (release 181 ms, no slow detector) | 100 %: -53.8 against -55.4 dB in the fit (the release on program material is faster than on a steady tone) |
| A fall-rate limit of 47 dB/s on the high band's detector, the law refitted around it | releases 56 to 96 ms; shallow drops release at -43 to -47 dB/s where the original has -32 to -41 (replaced by 3.17) |
| The high band as an instant level, the static curve, then attack and release on the reduction in dB (`probe_gr_drop.py --fit`) | 0.12 to 0.82 dB rms per probe against 0.10 to 0.37; deep drops do not share one slope |
| A peak detector then a smoothing of the reduction in dB (`fit_music.py --gr`) | the smoothing fits to about 0.01 ms (100 %: -52.60 against -53.17 dB without it) |
| A mean-square high-band detector without the slow one | 100 %: -53.04 against -53.87 dB |
| The high band refitted at 25, 150 or 200 % against the mid band of 3.15 | pink noise at -10 dBFS 3 to 5 dB worse at those amounts |
| One fixed limiter interpolator (16 taps, β 6) at every rate | five-signal mean -44.9 / -53.6 / -39.2 / -37.5 / -35.6 dB at 44.1 / 48 / 88.2 / 96 / 192 kHz |
| A free 16 × 16 limiter interpolation table fitted to band-limited pulses | reads them to 5e-5 and drums to -66.9 dB, but pink noise -47.5 → -44.6 dB |
| A pure Gaussian window of the ridge's σ, or a sinc cut below Nyquist, for the limiter interpolator | worse than the Kaiser points on the ridge |
| The limiter's state resting below the slow envelope, or lifted by the level | every case worse |
| 8x's third oversampling stage as a fixed filter at 4x | the character's harmonics filtered twice: music -45 dB |
| The character and limiter stages kept running while bypassed | bypass toggles -31 dB against -60 |

## CPU and performance

| Case | Measured |
|---|---|
| External side-chain (EXT) | 60 s of music renders 43 % slower at 1x and 81 % slower at 4x than in INT (a second band split and oversampler); INT unchanged |

## Scripts

Each value above names the script that measured or fitted it. `measure_high_gain_probe.py` (a probe tone),
`measure_high_gain_program.py` (program material) and `measure_high_gain_noise.py` (noise) read the high band's gain
trace three ways; `measure_mid_release_speed.py` turns `measure_mid_release.py`'s traces into release speeds;
`probe_band_path.py` reads the response a band's gain is applied to; `compare_third_harmonic.py` compares the cubic term
in and out of phase. `scripts/make_character_table.py` writes `Source/dsp/CharacterTable.h`.

## Provenance

How each part of Positron was made:

- Measured: the original's output on generated test signals (tones, sweeps, noise, a drum loop) and on music, section
  by section; its host parameters, ranges and display text; films of its editor while it plays, for the meters' and
  the visualiser's laws and timing.
- Fitted or learned from the original's output: the EQ bands, the character section's crossover, shapers, detectors
  and band laws, the limiter, the parameter smoothing and control rate, the meters and the oversampling filters, as
  identified laws, constants and fitted curves (the scripts named per section).
- Redrawn: the editor, drawn in code from measured positions, sizes and colours with our own shading: the knobs and
  their shadows, the glass of the visualiser (bands of measured geometry), the plate and its grille.
- Shipped on recorded approval: nothing.
- Published measurement data (approval recorded 2026-11-09): [`measurements/Positron/`](../../measurements/Positron/),
  measured responses and fitted values of our own: the latency and core delay per rate (`core/`), the EQ responses and
  fit (`eq/`), the limiter's measured curves and fit (`limiter/`), oversampling and side-chain responses, parameter
  smoothing, the gain-reduction meters, the character section's crossover, static, small-signal and dynamic curves, band
  laws, widths and shaper tables (`character/`, the inputs of `scripts/make_character_table.py`), and the null tests'
  results (`nulltest/`, the data behind NULLTESTS.md). It holds no render of the original and no file the original or a
  host wrote.
- None of the original's code, artwork, preset files, fonts or other files ships with Positron.
