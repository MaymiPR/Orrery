# Wraith: measurements

The original's audio behaviour, measured from its output, and the values Wraith's DSP takes from it. The null results
are in [NULLTESTS.md](NULLTESTS.md), cited here by case name; the controls and presets are in
[RESEARCH.md](RESEARCH.md).

## Setup

| Item | Value |
|---|---|
| Reference | Cradle The Spirit 1.0.3, VST3, Windows |
| Offline host | `tools/RefRender`: a fresh instance per job, latency compensated by the original's report (0) |
| Editor host | `tools/RefCapture`: real-time captures with the editor open (`record=1`), states saved by the original itself (`savestates=`) |
| Harness | `nulltest/wr_ref.py`; the structure probe (`structprobe.py`), the measurement battery (`measure_suite.py`, at 48, 44.1 and 96 kHz) and `nullrun.py` driven through a target file |
| Rate, block | 48 kHz, block 512 |
| Start state | the factory preset "lead" (RESEARCH.md, Presets); the stage under test keeps that preset's values and every other stage is switched off with its own power button (the five State parameters) |
| Skip | the first 0.1 s of every render |
| Determinism | two renders of one input through the default state are identical (-600 dB); parameters apply before the first block: a 400 ms settle changes nothing at 48 kHz |
| Settle at 44.1 kHz | the reverb's response loads asynchronously at 44.1 kHz only: without a settle the tail is missing (-149 dBFS after an impulse, the dry path alone); after 1 s it is there (-72 dBFS, as at 48 kHz); every 44.1 kHz render with the reverb on uses `settle=1000` |
| Plate | the original plays its plate only with its editor open (a saved state with the plate selected plays the room's filter alone in an offline host, its wet signal silent), so plate cases are real-time captures, with the editor open, after 6 s of silence while the plate loads |
| VST3 check | `nulltest.py --vst3` gives the renderer's numbers to the printed digit; `first_null.py` finds the VST3 and the renderer equal at -333 dB at the start-up preset |

Data and plots live in `measurements/Wraith/` and the renders in `reference/Wraith/`, both git-ignored. This file is
the published record; every number in it is reproduced by the script its section names.

## 1. Path, latency and structure (`structprobe.py`, `measure_suite.py`, `probe_plate_presets.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| All stages off | the output equals the input bit for bit, lag 0, at 48 kHz | null | -600 dB; NULLTESTS.md "path: every stage off" |
| Latency | 0 reported and 0 measured (a click through every stage on its own); the Character stage shows an apparent lag of 2 to 7 samples by cross-correlation (44.1 / 48 / 96 kHz), the group delay of its filters, not a delay line | click | exact |
| Order | input gain → rider → Character → EQ → reverb → doubler → output gain: the original's Character output through its own doubler gives the two together to -335 dB; the reverb comes before the doubler (6.1) | stage renders chained | exact |

Each stage alone at the preset's values (the structure probe):

| Stage | Contribution | Linear | Time-invariant | Memory | Level dependence | Channels | Detector | Distortion |
|---|---|---|---|---|---|---|---|---|
| Rider | -6.1 dB | no (-6.1) | yes (-336) | none after 1.5 s | +10.1 dB at -30, -6.7 at -6 dBFS: levels toward a target | L / R independent paths, linked gain | hears mid only | H3 -72 dB at -6 dBFS (gain modulation) |
| Character | -3.2 dB | no (-5.2) | yes (-134) | none after 1.5 s | +12.4 dB at -30, -8.8 at -6: heavy compression with make-up | linked | hears mid only | odd shaper: H3 -56, H2 -69, even residual -63 dB |
| EQ | -10.7 dB | yes (-137) | yes (-343) | none | none | independent | none | none |
| Doubler | -17.9 dB | almost (-40) | no (-17): modulated | none | none | the right output carries left input (-17 dB) | none | none |
| Reverb | -18.9 dB | yes (-144) | yes (-148) | the tail (-63 dB at 1.5 s) | none | L / R independent responses | none | none |

The battery at three rates:

| Stage | 48 kHz | 44.1 kHz | 96 kHz |
|---|---|---|---|
| Rider | gain +10.1 dB at the pilot, slope 0.40 dB/dB, attack 5.7 ms, release 355 ms, AM ripple 2.7 dB | the same to 0.05 ms | the same |
| Character | gain +12.4 dB, slope 0.30 dB/dB, attack 1.6 ms, release 50 ms, AM ripple 5.3 dB | attack 1.6, release 50 | attack 1.5, release 50 |
| EQ | low shelf +4.09 dB at 23 Hz, +2.44 at 182 Hz, +0.40 at 357 Hz, 0.00 at 1.4 kHz; +0.03 above 5 kHz (the preset's air) | +2.50 at 178 Hz | +2.30 at 188 Hz: the same shelf at every rate |
| Doubler | gain +0.24 dB, +0.8 dB below 50 Hz, flat within 0.2 dB above; no steady LFO on a tone's gain | the same | the same |
| Reverb | gain +0.34 dB, ripple of the response -1.1 to +0.2 dB (a room's comb) | (with the settle) | the same |

Character's noise response differs between rates (-2.9 to +6.4 dB at 1.4 kHz) because its compressor hears a
different in-band level from the same full-band noise; its small-signal response is in 4.2.

| Stage | Class | Method |
|---|---|---|
| Input and output gain | exact | dB gain with the original's smoothing (2) |
| EQ | exact | RBJ shelves (5) |
| Rider | exact | the static law and detector (3) |
| Character | fitted model | the Focus EQ, the expander, the compressor's static curve and dynamics (4) |
| Reverb | exact, measured responses | the filter and the mix law exactly; the room and plate responses measured per rate and run by convolution (6) |
| Doubler | fitted model (time-variant) | modulated delay voices, filters and the lows (7); a behaviour metric beside the nulls |
| Presets | exact data | each loaded from its own state (8) |

## 2. Smoothing (`nulltest/probe_smoothing.py`, `null_auto.py`, `fit_eq_motion.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Gains (input, output, the Mix controls) | the engine runs in 128-sample chunks; at each chunk's start the target moves a share k of the way to the new value, k = (128 / fs) / 9.98 ms (0.2672 at 48 kHz, 0.1335 at 96 kHz: an Euler one-pole of 10 ms), and the gain ramps linearly across the chunk in linear amplitude | `probe_smoothing.py`, the gain read sample by sample | automation jumps of ±6 dB null at -102 to -107 dB |
| EQ gains | a 5 ms linear ramp in dB, coefficients per sample | `fit_eq_motion.py` | knob-sized jumps (about 1 dB) -52 to -61 dB over the first 5 ms, -78 to -136 dB after |
| Large low-shelf jumps (12 to 16 dB) | the original shows a broadband bump of up to +4.6 dB for about 200 samples that no tried filter structure reproduces (Declined changes) | `fit_eq_motion.py` | -10 to -21 dB over the first 5 ms, exact afterwards |

## 3. Rider (`nulltest/probe_rider.py`, `fit_rider.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Static law | gain = Amount × (-15.57 dB - L), L the tone's peak level as the detector reads it; at most +20 dB of boost (no cut limit reached at 0 dBFS); Amount scales the whole gain | fresh renders per level, no history | exact |
| Floor | below the Floor F the boost is limited to 20 × (L + 15.57 - F) / (\|F\| / 5) dB, clamped to 0 … 20: the limit falls from 20 dB to 0 over \|F\| / 5 dB (slopes 2.000 / 2.381 / 2.941 / 3.846 dB per dB measured at F = -50 / -42 / -34 / -26) | staircases | exact |
| Detector | the mid signal's power through a one-pole, the attack from Speed and a release independent of it, no further smoothing | `fit_rider.py`: CMA-ES on level steps at three speeds, noise bursts and music, two held-out signals | |
| Attack | Speed itself, in seconds (fitted 1.0007 × Speed) | as above | |
| Release | 100 ms (fitted 99.99) | as above | |
| Level | reads 16.0 dB under the target in the form above: the asymmetric detector rides the peaks of the squared signal, so a sine reads near its peak, not its RMS | as above | with these rounded values every case nulls at -100 to -133 dB, the held-out ones included |

NULLTESTS.md: "rider:" cases.

## 4. Character

Scripts: `probe_char.py`, `probe_side.py`, `fit_focus_eq.py`, `fit_allpass.py`, `fit_char.py`, `fit_expander.py`,
`fit_overshoot.py`, `fit_curve.py`, `fit_focus_hf.py`.

The stage is the Focus EQ, then a downward expander, the Compression drive and a compressor that holds the output near
a fixed ceiling. Its detectors hear the mid signal only (a quiet 1 kHz probe is ducked 10 to 22 dB by a loud tone
anywhere from 60 Hz to 12 kHz), and its one gain is applied to both channels.

**The side channel.** With L = d + p and R = d - p the drive d sets the gain, and the side output (L - R) / 2 is that
gain times the stage's linear filters applied to p alone. A probe on the side does not reach the detectors: a 4 or
12 kHz tone at -46, -76 and -100 dBFS gives the same gain trajectory to the printed digit (0.1 dB). Most probes below
read the stage's gain or its filters this way (`probe_side.py`).

### 4.1 Static curve (`probe_static.py`, `fit_curve.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Drive | 0.2 × (Compression + 50) dB: 0 dB at -50, +20 dB at +50; the knob is the drive only | small-signal responses | exact |
| One curve | at Compression -50 / -25 / 0 / +25 / +50 the gain, the drive taken out, falls on one curve of the driven level: -50 and +50, 20 dB of drive apart, agree to the printed 0.01 dB at every driven level both cover (e.g. +0.22 dB with -16 dBFS in at -50 and -36 dBFS in at +50) | a 1 kHz tone in 2 dB steps of 0.5 s from -60 to 0 dBFS, Focus +8, the gain over each step's last 0.2 s | exact |
| Shape | in 4 dB steps of driven level from 12 dB under the kink, the slope is about 0.08, 0.19, 0.54, then 0.935 at the kink (about 15:1), rising to about 0.99 some 30 dB above it (100:1); the output held near -16 dBFS, every Compression setting meeting the same ceiling; the 150 Hz ceiling sits 1.5 dB under 1 kHz's | `probe_static.py`, `probe_char.py` | measured |
| On a 1 kHz tone (Compression 0, Focus +8) | the gain eases down from -38 to -28 dBFS, its slope rising steadily from 0.05 to 0.3 dB per dB, then kinks at -28 dBFS into about 15:1 (0.935 dB per dB) | `probe_char.py` | measured |
| On pink noise (Compression -50, Focus +50) | the gain starts to fall near -32 dBFS and reaches a 1 dB per dB slope near -14 dBFS | `probe_char.py` | the model within 0.65 dB |
| Model | the reduction's slope at nine knots 5 dB apart in driven level, linear between them, the curve's integral the reduction: first knot -27.5 dB, slopes 0.13, 0.12, 0.03, 0.93, 0.99, 1.0, 1.0, 0.94, 0.97; make-up 0.10 dB (Character.h, Tuning.h) | `fit_curve.py --penalty 5`: CMA-ES on the stage's null over `fit_overshoot.py`'s cases plus 1 kHz staircases at Compression -50, 0 and +50, pink noise at Compression -50 and 0, two sweeps, loud pink noise and music at Compression +50, a case that got worse than with a single knee counted six times | held out (music at Compression +25, pink at Compression -25 and -50, drums at Compression +50, 150 Hz steps, 5 kHz staircase): mean -24.7 dB; on the 1 kHz staircases -0.37 to +0.37 dB in the compressor's range, one step -0.70 dB |

### 4.2 Focus EQ (`fit_focus_eq.py`, `fit_allpass.py`, `probe_side.py eq`, `fit_focus_hf.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Position | before the dynamics | response where the dynamics hold a constant gain (Compression -50, noise at -38 dBFS) | |
| Focus law | the response changes almost exactly linearly in dB with Focus | as above | worst departure 0.1 dB |
| Structure | a minimum-phase EQ times a fixed all-pass: the excess phase does not change with Focus; the measured excess group delay is about 0.6 cycles at every frequency from 20 Hz to 20 kHz | side-channel clicks | measured |
| Model | 15 RBJ sections (w0 = 2 π f / fs) whose gains move as a + b × Focus / 50, and four second-order all-passes at about 100, 480, 1790 and 4710 Hz (Q 0.4 to 0.6) (`FocusEq.h`, generated by `make_focus_eq.py`) | `fit_focus_eq.py`, `fit_allpass.py` | magnitude within 0.06 to 0.12 dB rms at every Focus value |
| Side-channel clicks | clicks on the side under a steady pink drive (-34 dBFS, Compression -50) give the stage's impulse response at eight Focus values; the original's clicks agree with each other to -87 dB: its gain holds perfectly still under that drive | `probe_side.py` | |
| Model at 48 kHz against the clicks (complex error, Focus -50 / +8 / +50) | -35.7 / -39.6 / -33.2 dB | `fit_focus_hf.py` | |
| Per sample rate | at 44.1, 88.2 and 96 kHz every section from 80 Hz up and the four all-passes are fitted per rate (Character.h uses the nearest rate in the table; 48 kHz keeps its own); the fit holds the model's level at each Focus value to the 48 kHz model's (the EQ sits before the detector, so a level free to move changes what the compressor hears), keeps the gain real, weights the bins as pink noise does, and fits up to 0.48 fs; sections under 80 Hz keep their 48 kHz values (the clicks show nothing under 30 Hz) | `fit_focus_hf.py` against side-channel clicks at eight Focus values | complex error, pink-weighted, up to 0.48 fs: 44.1 kHz -33.9 to -38.0 dB, 88.2 kHz -27.8 to -31.8, 96 kHz -26.7 to -31.6 |
| The original's response per rate | not its 48 kHz response through a resampler: at 96 and 88.2 kHz below 20 kHz it is duller than at 48 kHz by 2 dB at 5 kHz, 6 dB at 12 kHz and 7 dB at 16 kHz, its phase straying from a plain delay by 19 to 29 degrees; above 20 kHz it falls the same way in Hz at both rates (-7 dB at 22 kHz, -18 dB at 23 kHz, -31 dB at 30 kHz); at 44.1 kHz it is 0.3 to 0.6 dB higher at 10 to 15 kHz than the 48 kHz model with 6 to 8 degrees more phase, at 96 kHz 1 to 2 dB lower; two 48 kHz sections shape that top end (a broad low-pass near 21.6 kHz and a narrow cut near 22.5 kHz, just under 48 kHz's Nyquist); at 88.2 and 96 kHz it also differs by 0.5 to 1 dB near 120 to 150 Hz at Focus +50; the stage's excess phase is not the same at every rate | `probe_side.py eq` at 44.1, 48, 88.2 and 96 kHz | measured |
| Quiet pink noise through the stage alone (-36 dBFS, Compression -50, the gain still) | -36 dB at 48 kHz, -35.1 at 44.1 kHz, -30.6 at 96 kHz | renders | measured; the start-up preset per rate: NULLTESTS.md "full chain: start-up" rows |

### 4.3 Expander (`fit_expander.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Static | a downward expander below about -45 dBFS on a 1 kHz staircase (2.2 dB per dB) | `probe_char.py` | measured |
| Release behaviour | a 1 kHz tone stepped down to -60 dBFS keeps its gain for 20 ms, is 5 dB down after 300 ms and 17 dB after 740 ms, closing at 25 to 35 dB/s, and later the louder the material before; in digital silence between drum hits the original holds its gain (+10 dB at the start-up preset) | quiet steps, drums, side channel | measured |
| Detector | its own peak detector with a slow release: release 266 ms, attack 0.11 ms; threshold -40.0 dBFS, ratio 2.18, knee 12.2 dB (Tuning.h) | fitted on quiet steps (rms dB error) and drums | the quiet steps' gain error 1.3 to 1.5 dB rms (0.4 dB at Compression +50) |
| Frequency weighting | equal to the compressor's at Focus -50, flatter as Focus rises: at 40 Hz 7 dB (Focus +8) and 13 dB (+50) above the Focus EQ at -50, the compressor's 3 and 6 dB less than that; on 55 Hz tones Wraith's expander closes 2 to 2.5 dB more than the original's | `probe_det_weight.py ref exp`: the level where the gain comes within 6 dB of its plateau from below | not modelled (below the null suite's levels) |
| By Compression setting | at -60 dBFS in, the original's gain (drive taken out) is -19.0 dB at Compression -50 and -16.5 dB at +50; Wraith -16.1 dB at both (2.9 / 0.4 dB high) | `probe_static.py` | not modelled (below the null suite's levels) |

### 4.4 Compressor dynamics (`probe_steps.py`, `fit_char.py`, `fit_overshoot.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Detector | a peak detector: noise is compressed about 5 dB harder than a tone of the same RMS | `probe_char.py` | measured |
| Constants | threshold, ratio, knee, attack, two release times and their switch (Tuning.h), fitted with CMA-ES on tones, noise bursts, music and drums together, with a held-out set; the release times refitted with the overshoot | `fit_char.py`, `fit_overshoot.py` | |
| Overshoot after a step | 1 kHz from -40 dBFS up to -20 / -10 / 0 dBFS (Compression 0, Focus +8): the reduction runs past its steady value by 0.23 / 0.31 / 0.30 of it (8.8 / 18.4 / 28.2 dB steady, 10.8 / 24.1 / 36.8 dB at its deepest), deepest 30 to 64 ms after the step, then comes back at a constant 20 to 24 dB/s and stops dead at the steady value 300 to 500 ms after the step (identical from 512 ms to 3.9 s) | `probe_steps.py`, the gain read through the side channel | measured |
| Release after a step | back down to -40 dBFS after 1.5 s the original lets go at about 0.3 dB per ms (from 0 dBFS: 28 dB in 64 ms; from -10 dBFS: 16 dB in 64 ms); after a long burst the rate depends on the depth, about 0.34 / 0.27 / 0.2 dB per ms over the 10 to 30 ms after the drop from 28 / 18 / 9 dB of reduction (roughly as the square root of the depth) | `probe_steps.py` | measured |
| After bursts | at -10 dBFS from -40 dBFS: after a 1 / 3 / 10 / 30 ms burst the original recovers 2.1 / 6.2 / 13.6 / 17.6 dB in the first 100 ms, after 100 and 300 ms bursts 18.6 and 17.7 dB: a short burst lets go slowly, a long one fast | `probe_steps.py` | measured |
| Ripple | on steady tones the original's gain ripples at twice the tone's frequency as much as Wraith's or more (100 Hz at 0 dBFS: 0.22 against 0.10 dB): its detector is no slower | `probe_steps.py` | measured |
| Overshoot model | an extra reduction, a share (0.52) of the stage's reduction smoothed over about 10 ms above its own slow average (attack 51 ms, release 35 ms), charging in about 10 ms and letting go over about 140 ms; zero at steady level, so the static curve is unchanged; a long burst lets the slow average catch up, a short one leaves the share charged (Character.h) | `fit_overshoot.py --dynamics-only`: CMA-ES on the stage's null (1 kHz steps at Compression 0 and +50, the bursts, drums at two settings, music and pink noise at three each), the static curve, attack and make-up held | training -24.8 dB; held out drums at Compression +50 / Focus +20 -15.6 dB, pink at Compression -25 -30.3, 150 Hz steps -12.6, music at Compression +25 / Focus -30 -22.7 |

### 4.5 What the detectors hear (`probe_det_weight.py`, `probe_bass_gain.py`)

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Compressor weighting | at Focus -50 it equals the stage's Focus EQ within 0.5 dB at every frequency; at Focus +8 and +50 three dips of the stage's response are missing from it: the narrow notch near 7.4 kHz, the dip near 150 Hz and the narrow dip near 520 Hz | a mid tone stepped up in 2 dB steps from -60 dBFS, its gain read through a 12 kHz side probe; the level where the gain is 6 dB under its plateau, per frequency, normalised to 1 kHz | measured |
| Output ceiling of loud tones | dips by the same amounts (7 kHz: 1.5 / 4.7 / 8.1 dB under 1 kHz at Focus -30 / +8 / +50, linear in Focus and zero near Focus -50): part of the Focus EQ sits after the gain, with gains of 0 dB at Focus -50 | tones | measured; not modelled (Declined changes) |
| Bass | the steady gain on bass tones differs by 0.3 to 0.5 dB at 100 to 200 Hz | `probe_bass_gain.py` | measured; not modelled |

NULLTESTS.md: "character:" cases; the presets without the doubler follow them.

## 5. EQ (`nulltest/fit_eq.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Shelves | an RBJ low shelf at 200 Hz and an RBJ high shelf at 5 kHz, both Q 0.7, w0 = 2 π f / fs without prewarping, the same at every rate (`Biquad.h`) | impulse responses at ±12 and +6 dB per shelf at 44.1 / 48 / 88.2 / 96 kHz | fit -134 to -151 dB |
| Stage null | | against the original | -137 dB median (preset values, the renderer), -129 dB (the VST3, Low -7.5, High +9); NULLTESTS.md "eq:" cases |

## 6. Reverb

Scripts: `nulltest/probe_reverb.py`, `render_plate.py`, `pack_reverb.py`, `null_plate.py`, `render_plate_filter.py`,
`probe_plate_filter.py`.

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Mix | a linear crossfade: dry 1 - m, wet m | nine values | exact to -136 dB |
| Filter | an RBJ low-pass on the wet signal, Q 0.7, w0 unwarped; it stays in at the 20 kHz setting (the fitted corner there is 19924 / 19952 / 19998 / 19999 Hz at 44.1 / 48 / 88.2 / 96 kHz) | `probe_reverb.py` | -120 to -152 dB |
| Filter on the plate | one fixed low-pass after the plate, not a damping inside its tail: each setting's response against the 20 kHz one is the same, per band, in every window from the first 50 ms to 1 to 2 s (within about 1 dB) | `render_plate_filter.py`: seven real-time captures (an impulse at Filter 2 / 5.2 / 8 / 11.4 / 20 kHz, the 5.2 kHz impulse twice, noise at 11.4 kHz; Mix 1, 48 kHz) | the same capture twice agrees to -137 dB; the 11.4 kHz impulse predicts the noise capture to -133 dB (still in time and linear); Wraith against the captures -78, -78, -77, -69, -52 dB |
| Responses | linear and time-invariant, left and right independent (no cross-feed); room: T60 about 1.5 s, 2.27 s long; plate: T60 about 4.7 s; the same length in seconds at every rate | impulses | |
| Capture | both responses recorded with the editor open (`tools/RefCapture record=1`, 5 s of silence first, repeated until two runs agree below -100 dB; the room recorded this way equals the offline render to -132 to -137 dB); the 20 kHz low-pass taken out by regularised deconvolution; each response cut where its decay energy has fallen 80 dB (room 2.07 s, plate 6.07 s), faded over 30 ms and stored as float16 (-73.5 to -73.8 dB re the response): 9 MB for four rates (`ir/`) | `render_plate.py`, `pack_reverb.py` | |
| Nulls | room at the start-up preset -97 dB, fully wet -79 dB (the float16 floor); plate at Mix 0.1 and Filter 8 kHz -95 dB, fully wet -52 dB | `null_plate.py` | NULLTESTS.md "reverb:" cases |

### 6.1 The reverb comes before the doubler (`probe_plate_presets.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Order | with the start-up preset's room playing (offline, its wet signal -19 to -28 dBFS in the tail) and the doubler on, the original's output equals its own doubler run on its output with the doubler off; its reverb run on its output with the reverb off gives only -8 to -18 dB | pink noise, drums, music | -333 to -338 dB |
| Order with the plate | the original's chain with the reverb off, the plate (Wraith's, which matches) and the original's doubler after it rebuild the captures; the plate after the doubler gives -9 to -16 dB | captures | -32 to -48 dB |
| Switching the doubler in the room's tail | the biggest step there, re the tail's own: 3.1x on and 3.6 to 13x off (the original); 3.1x and 3.4 to 18x (Wraith) | renders | measured |
| Model | the doubler and its Mix run after the reverb's crossfade (Engine.cpp); latency (none), the tail length, the bypass and both Mix laws unchanged | | |
| Capture timing | the plate captures play 6 s of silence before the signal, whole periods of a 0.5 Hz modulation but not of the doubler's 0.503 Hz (7.1): in the captures the doubler runs 0.018 cycles ahead, its voices' delays up to 0.17 ms apart; `nulltest.py` gives Wraith's renders the same lead | | |
| What limits the plate presets | the chain in front of the reverb (the preset's state with the reverb off, both sides) nulls at -14.5 / -15.4 dB on pink noise, -17.6 / -18.1 dB on drums, -18.9 / -20.7 dB on music ("big cave" / "wide and wet"), worse than either stage alone (Character -27 dB, doubler -23.5 dB on pink noise): Wraith's doubler fed the original's own Character output nulls at -14.7 dB, against -23.5 dB on plain pink noise, because the Character output puts more of its energy where the doubler's voices differ most (7.3) | `probe_plate_presets.py` | NULLTESTS.md "preset: big cave", "preset: wide and wet" |

## 7. Doubler

Scripts: `probe_doubler.py`, `probe_voices.py`, `fit_dbl_voice.py`, `probe_dbl_rate.py`, `probe_dbl_residue.py`,
`probe_dbl_voiceresp.py`, `probe_dbl_voice_cancel.py`, `probe_dbl_voicegain.py`, `measure_doubler.py`.

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Determinism | two renders of one input are identical; digital silence in gives digital silence out; the same input twice in fresh instances gives the same output to the last bit | renders | -338 dB |
| Mix | a linear crossfade | renders | exact to -148 dB |
| Voices | two, read from the mid signal, in antiphase, not inverted (on white noise their short-window correlation with the input is positive) | clicks every 10 ms over 3 s; short-window cross-correlation | measured |
| Stereo | each voice goes to its own side with gain 1 + 1.636 × Stereo and to the other with 1 - 1.636 × Stereo | five settings | exact |
| Linearity | white noise at -40 / -28 / -16 / -4 dBFS gives the voices' level re the input to the printed 0.1 dB in every band | `probe_dbl_residue.py` | exact |
| Compander | isolated clicks give the voices 64 times the dry energy while steady material barely changes in level; a compander (2:1 before the line, 1:2 after it, 5 to 60 ms) changes the nulls by under 0.3 dB on noise, music and drums | clicks, noise | not modelled |
| Behaviour metric (full wet) | level within 0.11 dB of the original, third-octave spectrum within 0.4 to 0.6 dB rms, left / right correlation 0.949 against the original's 0.912 at Stereo 1 on pink noise | `measure_doubler.py` | NULLTESTS.md, the doubler table |

### 7.1 Modulation (`nulltest/probe_dbl_rate.py`)

Method: white noise in, Mix 1, Stereo 1; every 5 ms the cross-correlation of the side output (L - R, which holds the two
voices with opposite signs and neither the dry path nor the lows) with the input, upsampled 16 times; its positive
peak is the first voice's delay, its negative peak the second's; a sine of free rate, phase, centre and depth is
fitted to each track. The same tracker runs on the original and on Wraith's processor.

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Shape | a clean sine: the fitted sine leaves 2.5 µs rms on the original, the tracker's own noise (Wraith: 2.5 to 3.5 µs); its rate is not 0.5 Hz, so against a 0.5 Hz sine the phase runs away at a steady 0.003 cycles per second (linear over 24 s) | tracker | measured |
| Rate | depends on the sample rate, not monotonically; not on the block size (0.502994 to 0.502996 Hz at blocks of 64, 256 and 1024); no law in the sample rate found (a float32 phase accumulator advanced by rate / fs gives 0.4992 to 0.5005 Hz at a 0.5 Hz setting, not these), so the four measured rates are a table, linear between them and held at the nearest outside them | tracker | table below |
| Line | centre 7.5204 ms (the tracked centre includes the voices' filter delay: Wraith tracks 0.052 ms above its line delay), depth 1.5028 ms, start phase 0.9972 cycles, the phase starting when processing starts | tracker (Doubler.h, Tuning.h) | Wraith's tracks match the original's at all four rates to 0.00002 Hz, 0.0004 cycles and 0.0004 ms of depth |
| Interpolation | cubic | | first-order all-pass interpolation changes the nulls by under 0.1 dB |

| Sample rate | Rate (Hz) | Phase at the start (cycles) | Centre (ms, as tracked) | Depth (ms) |
|---|---|---|---|---|
| 44.1 kHz | 0.502218 | 0.9982 | 7.574 | 1.503 |
| 48 kHz | 0.502995 | 0.9979 | 7.573 | 1.503 |
| 88.2 kHz | 0.503458 | 0.9978 | 7.565 | 1.503 |
| 96 kHz | 0.503278 | 0.9983 | 7.564 | 1.503 |

### 7.2 Voice filters and the lows (`probe_voices.py`, `fit_dbl_voice.py`)

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Voice filters, regressed | on the input read at the tracked delays: a first-order high-pass near 300 to 500 Hz, about -9 dB through the middle, low-passes above 7 to 15 kHz | regression | the tracked delays explain the voices to -9.5 to -10.9 dB; the sine alone to -2.3 dB |
| The lows pass the line | the wet signal also holds an undelayed low-passed copy of the input, at unity below 40 Hz, -7.9 dB at 150 Hz, -15.8 dB at 300 Hz: this is why the original's wet signal is 6.4 dB above the dry below 60 Hz | regression | with it the regression explains the wet signal to -13.2 dB |
| Model | voice gain 0.340, high-pass 508 Hz, low-passes 15.5 kHz (Q 0.26) and 6.7 kHz (Q 0.54); the lows through an RBJ low-pass at 91 Hz, Q 0.84, gain 1.047 (Tuning.h) | CMA-ES on the nulls at Mix 1 / Stereo 0.5 and Mix 0.4344 / Stereo 0.6166, pink, music, drums (`fit_dbl_voice.py`) | settings outside the fit included: NULLTESTS.md "doubler:" cases |

### 7.3 What the voices hold beyond a filtered, delayed copy

Scripts: `probe_dbl_residue.py`, `probe_dbl_voiceresp.py`, `probe_dbl_voice_cancel.py`, `probe_dbl_voicegain.py`.
Measured on the original's side output (L - R at Mix 1, Stereo 1: the two voices with opposite signs, neither the dry
path nor the lows). The voices regressed on the input read at the exact tracked delays leave -12.3 dB of the voice
unexplained on white noise (most below 200 Hz and above 12 kHz); it sets the full-wet floor.

| Quantity | Value | Method |
|---|---|---|
| Odd harmonics | their relative level does not change with the input's level: a 100 Hz tone gives its 3rd, 5th and 7th harmonics 20, 34 and 45 dB under it in the side output (where the fundamental is cut by the voices' low cut), the same at -12 and -36 dBFS; re the input -35 dB at most (the 3rd of 200 Hz), -45 to -70 dB elsewhere: too small to set the floor | tones |
| Images | at 19.5 kHz plus and minus the input's frequency (folded at Nyquist), -34 to -58 dB re the input: too small to set the floor | tones |
| Where the full-wet null loses | 60 to 500 Hz holds 25 to 67 % of the residual on pink noise, drums and the sweep, 4 to 8 kHz 15 to 24 %; the top octave almost nothing | residual per band |
| Voice filter, tone by tone | a steep low cut (-55 dB at 30 Hz, -17 dB at 100 Hz, -0.1 dB at 200 Hz re the middle), flat from 300 Hz to 4 kHz, then a steep top (-0.6 dB at 8 kHz, -12.5 dB at 12 kHz, -51 dB at 18 kHz); a fourth-order high-pass near 170 Hz and two low-passes near 5 and 10 kHz fit it within 0.8 dB rms (Wraith: a first-order high-pass at 508 Hz with a softer top); summing the side output's whole power instead of the fundamental's gives a wrong low end (at 30 Hz the voices' 3rd harmonic is 8 dB above their fundamental) | the side output's power at each tone's own frequency, averaged over whole cycles of the modulation (the modulation's share is the same on both plug-ins, so the ratio of powers is the voice filters' magnitude ratio) |
| The two voices against each other | where the voices' delays are equal (twice a cycle) the side output holds only what differs between them: under 3 kHz, in 1 ms windows at those moments, Wraith -36.3 dB re the input (the two cancel), the original -21.9 dB, against -3.1 dB at the extremes of the modulation; the delays, tracked one by one, differ by 2 µs in their centres and not in depth, rate or phase (2 µs leaves under -38 dB there): the original's voices are not exact copies of each other, by about -19 dB | `probe_dbl_voice_cancel.py` |
| Each voice's gain over time | the two voices' gains agree within 0.04 to 0.21 dB in every band from 150 Hz to 12 kHz, and their gain against their own delay follows Wraith's pattern within 0.6 dB (the original's top a little brighter at the shortest delay and darker at the longest); no dry path or lows reach the side output (its correlation with the input at 0 to 3 ms: -53 dB); its level is 3.0 dB above Wraith's at Stereo 1 and 0.5 on white noise | `probe_dbl_voicegain.py`: per 5 ms the cross-correlation of the band-passed side output with the input at each voice's own delay |
| The voices against Wraith's | the side output (the voices' difference) and, above 300 Hz, the mid output less the dry path (their sum) carry the same ratio: +7 to +9 dB at 200 to 500 Hz, +5 dB at 1 to 2 kHz, +11 dB at 8 kHz, -7 dB at 18 kHz; its phase -10 degrees at 500 Hz, +17 degrees at 5 kHz, -91 degrees at 18 kHz; under 150 Hz the side's falls to -30 dB at 30 Hz with +127 degrees: both voices differ from Wraith's by one filter, the sum and the difference alike, not a stereo matrix of their own | the cross-spectrum at each tone's fundamental over whole cycles of the modulation (both plug-ins run the same delays, so the modulation's phase cancels) |

## 8. Presets (`read_presets.py`)

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Source | the original's eleven factory presets, read from states it saved itself after each click on its next-preset arrow (`tools/RefCapture savestates=`) | captured states | exact |
| Values | kept exact (EQ Low -2.9647, Reverb Filter 11424.806 Hz, …); two use an output gain of -3.03 dB, five the plate | `read_presets.py` | exact |
| Wraith | loads them under our own names, in the original's menu order (`Presets.cpp`) | | |
| Nulls | from the same states on the original's side (the plate presets with its editor open); the presets without the doubler land where Character does, the doubler presets where the doubler does | `nulltest.py` | NULLTESTS.md "preset:" cases |

## Declined changes

| Change | Measured effect |
|---|---|
| EQ structures for large low-shelf jumps: direct forms I and II, transposed II, state-variable; dB or amplitude ramps; coefficient interpolation; a state reset | none reproduces the original's broadband bump |
| The Character low-cut sections moved after the dynamics (the 150 Hz output ceiling sits 1.5 dB under 1 kHz's) | held-out set worse (music -4.6 dB) |
| The compressor as a feedback design with a log-domain detector and a switched release | 3.2 dB rms error on the level steps |
| A share of the reduction relaxing at a constant rate (fitted on the stage's nulls) | the share went to 0.02; refitting the compressor's other constants there only traded cases (held out: drums -9.3 to -16.5 dB, pink noise at Compression -25 -28.7 to -20.6 dB) |
| The Focus EQ as a crossover tree (Linkwitz-Riley 2 or 4; 5, 8 or 11 bands; band gains solved per Focus value) | no better than -12.8 dB |
| A feedback compressor (its detector following the stage's own output) | follows the original's gain on level steps better (-15 to -21.6 dB on the fit set), but its gain ripples at audio rate and the mid null gets worse (drums at Compression -50: -11.4 against -20.4 dB) |
| A second, soft static stage under the compressor's hard knee | the fit drove its ratio to 1.008 |
| The compressor's constants refitted on the Focus EQ split | -21.1 / -21.6 against -21.2 dB on the fit set |
| The expander hearing the signal before part of the Focus EQ (its measured weighting) | no change in the null suite (the expander acts below its levels); the fit cost response accuracy |
| The bass weighting corrected from the gain on bass tones | music unchanged, the median 1 dB worse |
| The Focus EQ split around the dynamics (six sections after the gain, three of them the dips the detector does not hear), refitted to the clicks and the compressor's weighting | response -34.6 to -35.8 dB complex (unsplit -30.2), weighting 0.19 to 0.25 dB rms (unsplit 2.04); before the overshoot and the static table: median -21.6 → -22.4 dB, worst -1.6 → -2.2, sweeps 3 to 8 dB better, pink noise at the start-up preset -21.6 → -25.9, presets on pink noise about 4 dB better, but 15 cases worse by more than 0.3 dB (music at the start-up settings and the presets on music 0.3 to 1.4 dB: start-up -23.3 → -22.0; pink noise at Compression +50 / -50 0.7 / 1.9 dB; the start-up preset on pink noise at 44.1 kHz 0.7 dB); on music the mismatch is a broadband level of 0.3 to 0.6 dB (the best single gain per case varies from -1.8 to +0.7 dB with the material) |
| The same split on top of the overshoot and the static table, its top end refitted per rate (complex error at 44.1 kHz -24 to -35 dB, against -16 to -17; at 88.2 and 96 kHz -20 to -22, against -14 to -19) | as it stands median -24.4 dB against -23.6, 10 cases better by more than 0.3 dB, 35 worse; with the static table and make-up refitted on it (`fit_curve.py`) median -24.0, 11 better, 28 worse; the same with a worse case counted six times (`--base`) median -23.7, 13 better, 19 worse. In all three the sweeps gain 3 to 6.5 dB (start-up settings -22.8 against -17.1, at 44.1 kHz -23.5 against -16.9), pink noise at Compression -50 / Focus +50 -29.2 against -25.5, "hard squeeze" on pink noise -25.0 against -22.4; drums lose 0.6 to 5.0 dB (Compression -50 / Focus +50 -20.2 against -25.2, the start-up preset -18.7 against -21.0, at 96 kHz -17.5 against -20.1) and music 0.4 to 1.2 dB (Compression -50 / Focus +50 -27.4 against -28.6, the start-up preset at 96 kHz -19.4 against -20.1); the overshoot, fitted with the unsplit EQ, would need refitting with it |
| Every Focus EQ section refitted per rate without the all-passes | -21 to -22.8 dB complex at 96 kHz (with the all-passes: -33 to -37 dB at 96 kHz, -35 to -47 dB at 44.1 kHz) |
| Prewarped Focus EQ sections | -8 dB at 44.1 kHz |
| One set of Focus EQ sections fitted to 44.1, 48 and 96 kHz together | -22 / -33 / -20 dB |
| The 48 kHz Focus EQ response taken as the same in Hz at every rate | -15 dB at 44.1 kHz |
| Focus EQ peaks defined by bandwidth instead of Q | -17 dB |
| Only the top two Focus EQ sections fitted per rate (44.1 kHz -29.3 / -29.5 / -23.5, 88.2 kHz -21.3 / -22.0 / -20.4, 96 kHz -20.8 / -21.4 / -20.0 dB complex at Focus -50 / +8 / +50), or fitted over the whole band at 88.2 and 96 kHz | less accurate than every section from 80 Hz up with the all-passes; the whole-band variant no change in the suite |
| A free phase across the band in the per-rate Focus EQ fit | the fit leans on a constant 14 degree rotation no filter can make: -30 dB on paper, -12 dB rendered |
| Equal bin weights in the per-rate Focus EQ fit | the top octaves outweigh the lows |
| Focus EQ sections under 80 Hz freed in the per-rate fit | resonant sections near 5 to 30 Hz that cost the sweep 6 dB at 96 kHz |
| A fractional delay per rate in the Character model | fitted 0.01 to 0.03 samples, no change in the suite |
| The static curve fitted together with the overshoot | traded pink noise and music for drums on the held-out set (pink at Compression -25: -21.8 against -29.5 dB) |
| A single quadratic knee and one ratio for the static curve | 0.3 to 1.0 dB off between -38 and -16 dBFS on the 1 kHz tone (0.3 to 0.45 dB high just under the kink, about 0.2 dB low above it); on the 1 kHz staircases -0.30 to +0.45 dB; on program material the table gains 0.4 dB of median |
| A gentle region under one knee (its slope rising linearly to a set value over a set width) | fitted freely it traded loud material at Compression +50 for quiet material (median -23.8 dB against -23.2 for the knee, "hard squeeze" on pink noise -20.0 against -22.1); fitted with losses penalised it settled at a width of 7.9 dB and a slope of 0.29, close to the measured shape, but gained less (median -23.29 dB, 17 cases better, none worse) |
| The compressor's level holding its peaks and falling at a set rate in dB, read through the static curve | the fit drove the rate to its limit (3 dB per ms, no hold); held-out mean -19.8 against -24.7 dB |
| The reduction released at a set rate in dB | fitted 0.07 dB per ms; held-out mean -23.0 against -24.7 dB |
| A release time that grows with the depth, time × (depth / 10 dB)^power | fitted 92 ms at 10 dB, power 0.40; training -26.4 against -26.1 dB, held out -24.5 against -24.7 |
| The doubler's first behaviour model (inverted voices, voice gain -0.25, a 6 kHz low-pass from a third-octave match, modulation 7.58 ± 1.505 × sin(2 π 0.5 t) ms) | long-term spectrum within 1.6 dB rms (5.6 dB at worst, below 60 Hz), stereo correlation 0.74 to 0.97 against the original's 0.91 to 1.0, level 2 to 6 dB under it on noise-like material at full wet; nulls -19 to -23 dB at Mix 0.1, -3 to -8 dB fully wet; a least-squares FIR for the voices on steady noise leaves -13.9 dB at any length |
| A 0.5 Hz modulation with a fitted phase (centre 7.516 ms, depth 1.495 ms, phase 0.0042 cycles) | a slow wobble of 0.044 ms rms (0.12 ms peak) left in the tracked delays (its trajectory correlating at 0.993 across noise seeds and levels): the phase running away from 0.5 Hz (7.1) |
| One voice filter for both voices fitted by CMA-ES with the gain, stereo spread, filters, the lows and the dry gain (three tries) | with the high-pass free it went to 74 Hz and traded music for noise: 14 cases better by more than 0.3 dB ("wide image" and "short phase" on pink noise -16.6 / -16.0 against -12.0 / -11.5 dB), 12 worse (music through the doubler 3.5 to 4.2 dB); with the high-pass held at the measured shape 4 and 3 cases better, 18 and 13 worse |
| The stereo spread 3 dB wider | 8 cases better by more than 0.3 dB (the sweep at Mix 0.1 1.8 dB), 3 worse (music through the doubler 1.5 to 2.4 dB) |
| A filter on the voices' difference alone, fitted to the side's magnitude (within 1.1 dB rms) | every doubler case worse (2.9 to 8.0 dB), its phase not the original's |
| The voice filter replaced by a chain fitted to the original's in magnitude and phase (an RBJ high-pass twice, two peaks, a low-pass twice; complex error -10 to -13 dB from 300 Hz up, but 6 to 11 dB too loud at 30 to 50 Hz) | 8 cases better ("short phase" on pink noise -17.2 against -11.5 dB, the sweep at full wet -14.8 against -11.3), 6 worse (music through the doubler 5.4 to 6.4 dB, where its bass reaches the voices) |

## CPU and performance

| Case | Measured |
|---|---|
| The whole plug-in, offline renderer, 120 s of music at 48 kHz (the fastest of ten runs) | 3.29 % of one core with the static table; 3.26 % with the overshoot and without it before the table (3.25 % in another set of runs): neither the overshoot nor the table's lookup costs measurably |

## Open

- The compressor's level on pink noise at low drive (Compression -50 / Focus +50, Compression +50 / Focus -30): a level
  offset of 0.2 to 0.5 dB that comes with the refitted release times (pink noise at Compression -50 / Focus +50 is
  0.36 dB louder than the original with them and no overshoot, 0.10 dB with the earlier ones; with the best single
  gain it nulls at -27.7 dB); the shape of the release after a long burst is
  not what costs it; the detector on noise and the expander's weighting are the candidates (4.3, 4.4).
- The Focus EQ split around the dynamics, worth trying again with the overshoot refitted on it (4.5, Declined
  changes).
- The doubler's voices: about -12 dB of each voice is not a filtered, delayed copy of the input (7.3), the full-wet
  floor; with the doubler after the reverb its error also reaches the reverb's tail. Candidates: the measured voice
  filter with its response under 150 Hz held to the original's, and a voice filter of more sections (one chain of RBJ
  sections reaches the measured phase only to -10 to -13 dB).
- The expander's own frequency weighting and its dependence on the Compression setting (4.3): below the null suite's
  levels.
- The broadband bump after large EQ low-shelf jumps (2).
- The rider at 0.97 into full compression on drums ("preset: hard squeeze"): the preset's rider alone nulls at
  -99 dB there; the loss is the compressor's gain on transients.

## Scripts

Each value above names the script that measured or fitted it. `fit_focus_eq.py` fits the Focus EQ whose sections ship
(`scripts/make_focus_eq.py` writes `Source/dsp/FocusEq.h`); it replaces the earlier single-cascade fit, whose shared
pieces are `focus_eq_lib.py`. `probe_dbl_voice_cancel.py` compares the doubler's two voices where their delays cross;
`scripts/pack_reverb.py` writes `resources/ir/`.

## Provenance

How each part of Wraith was made:

- Measured: the original's output on generated test signals and music, stage by stage at three sample rates; its host
  parameters, ranges and display text; its editor's layout from screenshots; its factory presets' values from states
  it saved itself.
- Fitted or learned from the original's output: the gains, the two shelves, the gain rider's law and timing, the
  reverb's high cut and mix law as identified laws and constants; the Character section (compression and the Focus EQ)
  as a fitted model, its expander's detector, its compressor's overshoot and static curve from the original's gain;
  the doubler's modulation, stereo matrix, voice filters and the lows that pass its delay line.
- Redrawn: the editor, drawn in code at measured positions and sizes in the suite's own look (its palette, knobs,
  meters and toggles): the faceplate, the knobs, the buttons, the meters and the displays.
- Shipped on recorded approval: the room and plate reverb responses, measured from the original's output at each
  sample rate (`ir/`); the original's factory preset values, under our own names.
- Published measurement data (approval recorded 2026-11-09): [`measurements/Wraith/`](../../measurements/Wraith/),
  measured responses and fitted values of our own: the Character section's fitted band models per order and band count
  (`char/`) and the doubler's behaviour metric (`nulltest/doubler_metric.json`). It holds no render of the original and
  no file the original or a host wrote.
- None of the original's code, artwork, preset files, fonts or other files ships with Wraith.
