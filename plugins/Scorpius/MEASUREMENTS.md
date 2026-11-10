# Scorpius: measurements

The original's audio behaviour, measured from its output, and the values and learned models Scorpius's DSP takes
from it. The null results are in [NULLTESTS.md](NULLTESTS.md), cited here by section and case; the controls and the
editor are in [RESEARCH.md](RESEARCH.md).

## Setup

| Item | Value |
|---|---|
| Reference | Cradle Orion 1.2.1, VST3, Windows |
| Offline host | `tools/RefRender.cpp` (shared with Positron): renders float32 files at a fixed rate and block size, sets parameters by displayed value, loads a saved state; `settle=ms` runs the message loop after the parameters are set |
| Harness | `nulltest/sc_ref.py`: `render_many(jobs)`, `ONLY(...)` (only the named modules on), settings the host cannot see written into a copy of the default state, test signals, nulls, an on-disk render cache |
| State editing | `nulltest/refstate_lib.py` edits a saved state by its path in the preset table (the hidden settings and the preferences) |
| Survey scripts | `nulltest/probe_survey.py`, `probe_order.py`, `measure_linear.py`: a first look at every module, the signal order, the small-signal impulse responses (`measurements/Scorpius/ir/`) |
| Rate, block | 48 kHz, block 512 |
| Start state | the factory preset "default"; each test switches the other modules off with their own power buttons (`ONLY`) |
| Settle | 400 ms of message loop after setting parameters: the original applies settings asynchronously, at a random point of the render (without the settle two renders of one input null at -8 dB; with it they are bit-identical) |
| Skip | the first 0.1 s of every render: over the first ~5 ms the processing ramps from the preset's values; after it, chaining modules through separate renders reproduces them to -85 … -115 dB |
| Noise floor | a time-shifted input leaves a residual of -117 dBFS at any level: the original adds a very low noise (or dither) while a module is on; it limits nulls on quiet signals only |
| Gain | the level of the test tone's fundamental (Hann window) at the output re the input |

Data and plots live in `measurements/Scorpius/` and the renders in `nulltest/renders/`, both git-ignored. This file is
the published record; every number in it is reproduced by the script its section names.

## 1. Structure (`probe_order.py`)

Both modules on, against the two modules rendered one after the other in each order (nulls in dB):

| Pair | This order | The other order |
|---|---|---|
| drive, harmonics | drive → harmonics -115 | -16 |
| drive, compression | drive → compression -106 | -16 |
| harmonics, compression | harmonics → compression -106 | -10 |
| harmonics, lift | harmonics → lift -87 | -13 |
| compression, lift | compression → lift -85 | -20 |
| any module, EQ | module → EQ -287 … -291 | -12 … -20 |

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Chain | input gain → drive (+ hi-pass) → harmonics → compression → lift → harmonic EQ → the parallels → output gain | `probe_order.py` | exact |
| Parallels (sub, low, loud, grit) | fed from the end of the chain (after the EQ); each nulls against "chain, then the parallel" | `probe_order.py` | -284 … -294 dB (grit: below) |
| Mixing | independent paths mixed in, not a series: out = chain + Σ (pathₖ - chain) | two parallels on at once | -143 … -145 dB |
| Grit | works on each channel by itself (14); after drive it nulls against "chain, then grit" at -86 dB, after compression at -31 dB (stereo material; 14) | `probe_order.py` | measured |
| All modules off | bit-exact, latency 0 | null | -280 dB at 48 kHz |

## 2. Sample rates

The DSP runs at a fixed 48 kHz. At other rates the audio is converted in and out with the original's own converters
(identified in 14):

| Rate | Reported latency | Impulse peak | All modules off: null against the input | Response near the top |
|---|---|---|---|---|
| 44.1 kHz | 31 | 31 | -38 dB | -0.07 dB at 20 kHz, -0.3 at 22 kHz |
| 48 kHz | 0 | 0 | bit-exact | flat |
| 88.2 kHz | 46 | 49 | (band-limited) | -0.65 dB at 20 kHz, -4.4 at 22 kHz, -83 at 30 kHz |
| 96 kHz | 48 | 52 | (band-limited) | -0.74 / -4.2 / -104 dB |
| 192 kHz | 80 | 88 | (band-limited) | -1.0 / -3.9 / -83 dB |

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Round-trip delay | 27.0 / 31.0 / 48.742 / 51.1 / 81.461 / 87.085 samples at 32 / 44.1 / 88.2 / 96 / 176.4 / 192 kHz | phase slope of white noise (`Resampler.h`) | measured |
| Reported latency | 27 / 31 / 46 / 48 / 75 / 80 samples at the same rates: 3 to 8 samples short of the impulse's peak at 88.2 / 96 / 192 kHz | host report | exact |
| Top | at high rates the output stops at ~23 kHz (the 48 kHz processing band); at 44.1 kHz flat to 22 kHz (-0.3 dB) | | measured |

NULLTESTS.md: "all off" at each rate.

## 3. The low-level expander (`fit_exp.py`, `null_quiet.py`)

Drive, harmonics, compression and lift share one downward expander; the EQ and the parallels have none, and with all
four modules off there is none.

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Input | the output of the group (drive, harmonics, compression and lift together), not the drive's alone | compression alone at amount 1: a -64 dBFS tone leaves at -60.3 dBFS (its make-up) and the expander's gain is the curve's at -60.3 (-4.3 dB, the output -0.56 dB re the input) | compression, lift and harmonics at amounts 0 … 1 on -64 and -70 dBFS tones within 0.05 dB (lift 0.2 … 0.6) |
| Detector | the mid's peak, \|L + R\| / 2: a tone in one channel reads 6 dB lower; the same tone inverted in the other channel closes it to the floor; half level in the other channel reads 2.5 dB lower, a phase offset of 1 rad 1.1 dB lower | one- and two-channel tones | within 0.04 dB |
| Peak, not RMS | white noise at -62 dBFS RMS (peaks -50) passes unchanged; white noise of a tone's peak gets the tone's gain | noise | measured |
| Static curve | threshold -58.18 dBFS peak; below it 2.03 dB of gain per dB, so the output falls about 3 dB per dB (a 1 kHz tone: unchanged down to about -56 dBFS peak; -59 dBFS: -1.6 dB; -65: -13.8; -71: -26.0; -80: -44.4) | tone staircase | |
| Floor | -44.49 dB: it closes no further (any tone at -85 dBFS or below) | tones | measured |
| Holds | once the mid's peak has reached the threshold, fully open for 1.10 s after the last such sample, even after a 2 ms burst; below the threshold it holds the peak of the last 0.10 s | 28 level patterns per 1 ms (drops from above and below the threshold, rises, bursts of 2 … 50 ms, repeated bursts, stairs) | every pattern within 0.04 dB |
| Closing | a one-pole on the linear gain, 0.10 s time constant (it closes over about 0.6 s after the hold, the same from -20 or -40 dBFS) | as above | as above |
| Opening | a one-pole on the linear gain, 1 ms, from the -44.5 dB floor: the gain at the sound's n-th sample after silence is 1 - 0.994 e^(-(n + 1) / 48), at -12 and -30 dB alike and at any time in the render | drums after silence, only the compression on at amount 0 | -141 dB |
| Switched on | the modules' expander starts closed, as after silence | `probe_switch_on.py` | exact |
| At creation | with lift on, the expander starts fully open and holds 1.1 s as after a loud passage, then closes (the default preset, with the drive off, and with the colour, the hi-pass or an amount changed); with lift off (lift alone off, lift and harmonics off, any one module alone) it starts closed | -70 dBFS tone from the first sample | the default preset within 0.3 dB |
| With the drive | drive a alone: the threshold sits 1.4 dB higher for a sine and about 3.2 dB higher for pink noise than the expander's own, the drive's gain on each (-1.39 / -3.22 dB below the expander) | sine and pink noise | after the drive: within 0.3 dB (sine, -80 … -56 dBFS); pink noise through drive a, either hi-pass setting, within 0.1 dB at -50 … -80 dBFS RMS |

NULLTESTS.md, "Quiet material" and "Automation" (the switches).

## 4. Small-signal responses (`measure_linear.py`)

Impulse responses from 20 s of white noise at -50 dBFS (above the expander, below the modules' saturation). Gain in
dB at chosen frequencies (Hz); every module processes both channels alike (L - R below -300 dB):

| Case | 20 | 30 | 40 | 50 | 60 | 80 | 100 | 150 | 200 | 500 | 1k | 2k | 5k | 10k | 15k | 20k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| drive a | -33.6 | -13.5 | -4.1 | +0.5 | -1.8 | -0.9 | -0.3 | -0.5 | -0.8 | -1.3 | -1.4 | -1.9 | -1.7 | -0.7 | +0.4 | +1.9 |
| drive b | -22.1 | -11.2 | -6.0 | +0.9 | -0.4 | -0.4 | 0.0 | -0.5 | -0.8 | -0.8 | -0.8 | -1.2 | -0.9 | +0.8 | +2.4 | +3.2 |
| drive c | -14.4 | -10.3 | -4.7 | +2.7 | +1.5 | +1.4 | +1.9 | +1.5 | +1.2 | +1.3 | +1.3 | +0.8 | +1.2 | +2.5 | +3.5 | +3.9 |
| harmonics 80 Hz, 1.0 | -2.2 | -1.2 | +1.3 | +3.0 | +4.0 | +5.1 | +5.6 | +5.7 | +5.2 | +2.2 | +0.7 | +0.2 | 0 | 0 | 0 | 0 |
| harmonics 50 Hz, 1.0 | -3.0 | +0.7 | +3.4 | +4.7 | +5.3 | +5.7 | +5.6 | +4.8 | +3.8 | +1.1 | +0.3 | +0.1 | 0 | 0 | 0 | 0 |
| compression b, 1.0 | +2.4 | +3.1 | +3.4 | +3.5 | +3.6 | +3.6 | +3.7 | +3.7 | +3.7 | +3.7 | +3.7 | +3.7 | +3.7 | +3.6 | +3.3 | +3.1 |
| compression a, 1.0 | +2.1 | +2.8 | +3.1 | +3.2 | +3.3 | +3.3 | +3.4 | +3.4 | +3.4 | +3.4 | +3.4 | +3.4 | +3.3 | +3.3 | +3.1 | +3.0 |
| lift 1.0 | +2.5 | +3.0 | +3.2 | +3.3 | +3.3 | +3.4 | +3.5 | +3.5 | +3.5 | +3.8 | +4.3 | +4.2 | +4.1 | +3.5 | +2.4 | +1.5 |
| lift 0.0 | +0.5 | +0.5 | +0.4 | +0.3 | +0.3 | +0.3 | +0.3 | +0.2 | +0.2 | +0.3 | +0.5 | +0.2 | 0 | 0 | 0 | 0 |
| EQ 40 Hz +6 | +4.4 | +6.3 | +5.5 | +4.1 | +3.0 | +1.7 | +1.0 | +0.4 | +0.2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| EQ 100 Hz +6 | -1.7 | -2.0 | -0.2 | +1.7 | +3.5 | +6.0 | +7.0 | +5.6 | +3.8 | +0.8 | +0.2 | +0.1 | 0 | 0 | 0 | 0 |
| EQ 1 kHz +6 | -0.2 | -0.3 | -0.3 | -0.3 | -0.3 | -0.2 | -0.1 | +0.1 | +0.5 | +3.5 | +7.1 | +3.5 | +0.6 | +0.1 | 0 | 0 |
| EQ 3 kHz +6 | 0 | -0.1 | -0.1 | -0.1 | -0.1 | -0.1 | -0.1 | -0.1 | 0 | +0.4 | +1.7 | +5.3 | +4.6 | +1.1 | +0.3 | +0.1 |
| EQ 10 kHz +6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | +0.4 | +3.9 | +6.7 | +7.1 |
| sub 1.0 | +1.6 | +8.3 | +9.4 | +9.4 | +9.0 | +7.0 | +3.0 | +3.6 | +1.9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| low 1.0 | -0.8 | +1.5 | +0.6 | +0.6 | +2.6 | -0.2 | -0.5 | -0.1 | -0.1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| loud 1.0 | +4.4 | +4.3 | +4.1 | +4.1 | +4.1 | +4.2 | +4.3 | +4.6 | +4.5 | +4.6 | +4.6 | +4.7 | +4.5 | +4.7 | +4.6 | +4.7 |
| grit 1.0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

- The drive's hi-pass switch changes the small-signal response only below 20 Hz (-33.6 → -34.4 dB at 20 Hz for a);
  the main low cut is the drive's own (6). On music it is a fixed filter after the drive (14).
- A "+6" EQ band peaks at +7.1 dB; 3 dB gives +3.7. The 40 Hz band peaks at ~30 Hz; the 10 kHz band is a shelf. The
  100 Hz band cuts the deep lows a little (-2 dB at 30 Hz). Sub has a notch near 125 Hz.
- Compression's and lift's small-signal gain is the make-up of their wet path (5, 8).

## 5. Amount laws

Each amount between 0 and 1 against the best mix of the renders at 0 and 1, y ≈ y₀ + w (y₁ - y₀) (a drum-like test
signal; nulls in dB):

| Control | w at 0.25 / 0.5 / 0.75 | Null |
|---|---|---|
| compression | 0.250 / 0.500 / 0.750 | -137 … -145: an exact wet / dry mix |
| lift | 0.250 / 0.500 / 0.750 | -137: an exact mix |
| harmonics | 0.237 / 0.483 / 0.738 | -48 … -51: almost a mix (the amount also changes the processing, 14) |
| sub, low, loud levels | 0.092 / 0.251 / 0.526 | -139 … -156: an exact mix with the faders' taper (e^(2.188 L) - 1) / (e^2.188 - 1) (RESEARCH.md, faders) |
| grit level | 0.088 / 0.241 / 0.505 | -36 … -51 on this signal; grit's contribution is an exact mix (-100 … -126 dB re the contribution at 0.088 / 0.5 / 0.731 on drums and the track), except once (drums at 0.189: -10) |

## 6. Drive

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Oversampling | none: a 9 kHz tone at 0 dBFS aliases at -26 … -36 dB | tone | measured |
| Structure | an asymmetric saturator, then a low cut: a 1 kHz tone flattens at +0.49 / -0.43 (colour a), +0.63 / -0.53 (b), +0.85 / -0.70 (c) | tones | measured |
| Asymmetry | the second harmonic, present even at -50 dBFS (-84 dB for a), rising 10 dB per 10 dB | tones | measured |
| Low cut after the saturator | a 25 Hz tone at 0 dBFS still clips fully (output peaks as at 1 kHz) and its second harmonic ends up above the fundamental (+2 dB): the fundamental is cut after the saturator by the steep low cut of 4 (-34 dB at 20 Hz, a resonant peak near 50 Hz) | tones | measured |
| Gain of a 1 kHz tone | a -1.4 dB up to -12 dBFS, -5.2 at 0, -10.9 at +6; b -0.8 / -4.1 / -9.2; c +1.2 / -1.7 / -6.9 | tones | measured |
| Memory | the loops of output against input are wide (filters with phase around the saturator) | | measured |
| Time invariance | a time-shifted input nulls at -67 dB; no dependence on the block size | renders | measured |
| Determinism | not chaotic: noise added at -100 … -60 dBFS moves its output in proportion; depends on no future input | renders | measured |
| Linear part | a linear filter explains only 3 … 4 dB of its output, even 10 dB below full scale | Wiener fit | measured |
| Model class | neither a filter and a shaper in any order (Wiener, Hammerstein, both, with learned FIR filters: -14 dB at best on held-out music) nor a short-memory network reproduces it; its peaks wander irregularly far above full scale: a learned model in the original too | fits | inferred |

The learned models are in 14. NULLTESTS.md, "Module by module" (drive rows) and every preset.

## 7. Harmonics

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Small signal | a bass boost, +5.7 dB around 100 … 125 Hz at 80 Hz (around 80 … 100 Hz at 50 Hz) (4) | IR | measured |
| Harmonics | odd only, as from a cubic term: h3 rises 2 dB per dB (100 Hz at amount 1: -97 dB at -30 dBFS, -74 at -18, -62 at -12, -50 at -6, -39 at 0), h5 4 dB per dB (-66 at 0 dBFS); nearly the same from 30 to 400 Hz (-39 … -45 dB at 0 dBFS), much less at 1 kHz (-64): the shaper works on the lows | tones | measured |
| Compression | little: the boost at 120 Hz is +5.8 dB up to -12 dBFS, +5.3 at 0, +4.3 at +6 | tones | measured |
| Amount | almost a wet / dry mix (5); the processing changes with it (14) | | measured |

## 8. Compression (`probe_comp.py`, `probe_comp_colour.py`)

At amount 1 (the wet path; the amount mixes it with the dry signal exactly):

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Make-up | +3.4 dB (mode a), +3.7 dB (mode b) below -16 dBFS | 1 kHz staircase | measured |
| Static curve | a soft knee from about -14 dBFS; above it 0.8 dB of reduction per dB (ratio 5:1): -8 dBFS 0.0 / +0.3, -6 -1.6 / -1.3, 0 -6.4 / -6.1, +12 -16.0 / -15.7 dB (a / b); the two modes' curves are the same but for the make-up | 1 kHz staircase | measured |
| Detector | the same at every frequency (30 Hz … 15 kHz: 4.9 … 5.0 dB of reduction at -6 dBFS); a fast envelope between peak and RMS (noise of the tone's RMS is reduced 4.1 dB more than the tone, noise of the tone's peak 1.7 dB less); stereo-linked on the mid signal (one channel at -6 dBFS reduces the other, quiet one, by 0.9 dB, as (L + R) / 2 at -12 dBFS would) | tones, noise | measured |
| Timing | after a step from -30 to +6 dBFS the reduction reaches 90 % in ~2 ms (-9 dB of -11 after 2 ms); it recovers in ~20 ms (the make-up back after 30 … 40 ms) | steps | measured |
| Gain modulation | within the cycle, odd harmonics at low frequencies (40 Hz at 0 dBFS: h3 -27 dB) | tones | measured |
| The modes | agree in every tone test (static, steps, bursts, low frequencies) but for the 0.33 dB of make-up; on drums they differ (null -23 dB after the make-up): they differ in their wet filters and fine dynamics (14) | tones, drums | measured |
| Colour | the wet path is not linear besides its gain: steady tones below the threshold, where the gain stands still, come out with even harmonics in both modes (h2 -88 dB re the tone at -36 dBFS, -70 at -24, -65 at -18; 1 kHz and 100 Hz alike), about 1 dB more per dB, as from a gentle quadratic term; at amount 0 nothing (below -150 dB); modes a and b very likely colour the wet signal after the gain, each in its own way | `probe_comp_colour.py` | inferred |

The fitted law and the learned gain correction are in 14.

## 9. Lift

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Amount 0 | not the dry signal: a fixed gentle lift, +0.3 dB at 100 Hz, +0.5 at 1 kHz, 0 above 5 kHz (linear) | IR | measured |
| Amount 1 | a saturator with even and odd harmonics (1 kHz: h2 -48 / h3 -69 dB at -30 dBFS, h2 -28 / h3 -12 at 0 dBFS) between fixed filters: the gain curve has the same shape at 100 Hz, 1, 5 and 10 kHz (+3.5 / +4.3 / +4.1 / +3.5 dB small-signal, about 7 dB less at 0 dBFS) | tones | measured |
| Oversampling | none: aliases at -18 … -44 dB from a 9 kHz tone at 0 dBFS | tone | measured |
| Model class | a learned model in the original (as the drive, 6) | fits | inferred |
| Silence | on digital silence the original's lift gives -181 dBFS RMS | render | measured |

## 10. Harmonic EQ

| Quantity | Value | Method | Confidence |
|---|---|---|---|
| Linear range | linear below about -20 dBFS (4 for the band shapes) | tones | measured |
| Saturation | each boosted band saturates symmetrically: odd harmonics (1 kHz +6 dB: h3 -88 dB at -40 dBFS, -48 at -20, -22 at 0) and its boost shrinks (+7.1 → +6.2 at -10 dBFS, +3.6 at 0); the 10 kHz shelf compresses too (+3.9 → +2.0 dB at 0 dBFS) with its harmonics above the band | tones | measured |

The identified filters and clip are in 14.

## 11. Parallels

Each path is mixed in with the faders' taper (5); levels below at level 1.

| Path | Behaviour | Confidence |
|---|---|---|
| Sub | linear at every level (+9.5 dB at 50 Hz from -40 to 0 dBFS); the response of 4 (a lift around 40 … 60 Hz, a notch near 125 Hz) | measured |
| Low | works on the deep lows (below ~80 Hz) and grows faster than the signal: its contribution at 50 Hz is -36 dB re the input at -30 dBFS and -12 dB at -6 dBFS (about 2 dB per dB), with a second harmonic 19 dB under it; less again at 0 dBFS (-18 dB); no factory preset uses it | measured |
| Loud | upward compression, the same at every frequency: +6.6 dB at -60 dBFS, +5.1 at -48, +3.4 at -30, +1.9 at -12, +0.5 at 0, +0.3 at +6 (1 kHz); fast: down within 4 ms when the level jumps, back up over ~20 ms; the fast gain gives odd harmonics at low frequencies (h3 -34 dB at 100 Hz) | measured |
| Grit | no change to steady tones; on a kick-like hit a burst 3 … 18 dB under the hit for its first ~20 ms, decaying to -50 dB by 40 ms; its amount changes the processing, not only the mix (5) | measured |

The identified laws and learned models are in 14.

## 12. Smoothing and switching (`nulltest/probe_autom.py`, `measure_autom_curve.py`, `probe_switch_on.py`, `measure_harm_ramp.py`)

First readings, a 1 kHz tone at -20 dBFS, a change at a 64-sample block boundary:

| Change | Time to 90 % |
|---|---|
| a module's power (compression, lift) | ~5 ms (the module restarting, below) |
| compression amount 0 → 1 | ~10 ms ramp |
| EQ gain 0 → 6 | ~5 ms |
| input gain 0 → +6 dB | 19 ms, exponential (τ ≈ 8 ms) |
| a parallel's power | within 2 ms |

On drums, a change at 1 s and back at 2 s, the output during it fitted as a blend of the steady outputs at the two
values in 4-sample windows, at host blocks of 32 … 512. The original shares Positron's control rate (Positron's
MEASUREMENTS.md 5):

| Quantity | Value | Method | Residual or confidence |
|---|---|---|---|
| Amounts | two stages: a 5 ms ramp read once per 128-sample control chunk (chunks from the block's start), then a 5 ms linear glide to each reading, started afresh every chunk: 0.284 at the first chunk's end, then 0.0030 per sample, there at 368 samples; the same at blocks of 128, 256 and 512 | `measure_autom_curve.py` | predicts the measured curve |
| A module's power | switches at the block's start, no crossfade; with blocks under 128 samples a change waits until a whole chunk has gathered: 128 - n, rounded up to whole blocks (+64 at 64, +96 at 32) | `probe_autom.py` | exact |
| Switched back on | every module starts as if from silence: its output after the switch equals its output on the same input with silence before it (harmonics, compression, lift to -44 … -57 dB from the first sample; the drive to -43 … -60 dB from 10 ms on, its first milliseconds differing), not its output carrying on from where it stopped (-4 … -30 dB in the first 20 ms); the drive's ~100 ms of settling is a process with memory hearing sound after silence; the EQ restarts too | `probe_switch_on.py` | measured |
| EQ gains | a plain 5 ms ramp | `probe_autom.py` | -44 dB (Declined changes) |
| Parallels' levels | limited by the parallels themselves | | measured |
| Harmonics amount change | during and after the change the original's output is not that of any held amount: its output swings well away from both steady states during the ramp (-15 dB, while they differ by -36); the difference lies below 200 Hz and dies away over ~30 ms, after the ramp has ended | `measure_harm_ramp.py` | at every held amount 0.2 … 0.9 Scorpius nulls at -65 … -71 dB |

Scorpius: a learned model keeps the state it has after silence, computed when prepared, and returns to it when its
module is switched on (the LSTM drives' rest state is written with the model by `export_models.py`); the expander
starts closed (3), also while a switch waits for its chunk with small blocks; a harmonics model coming in when the
amount crosses a node first hears the input it missed (its whole memory). NULLTESTS.md, "Automation".

## 13. CPU and performance

| Case | Measured |
|---|---|
| The original, default preset | 60 s of drums at 48 kHz, offline, one instance, wall time less the ~1.2 s of loading: 8.3 s, ~14 % of a core (9.1 to 9.8 s in other runs); everything on ~20 % |
| The original, by module | drive 4.9 s (the most), compression 1.6, lift 1.7, harmonics 0.2, EQ 0 |
| Scorpius, default preset, same run as the original | NULLTESTS.md, "CPU" |
| Scorpius's drive | no more than the original's: the colour a LSTM 5.0 s of a core per minute stereo (5.9 s with the hi-pass filter after it), about 17 % less with the unclamped sigmoid (14); the WaveNet drives 5.6 against the original's 5.8 s |
| Compression's learned gain correction | about 0.6 s of a core per minute (mono); compression alone, 60 s of drums through ScRender less its all-off run: mode a 0.86 s, b 0.42 s (two corrections per mode); the default preset 4.23 s the same way |
| Learned parts | a block at a time in vector registers, 8 wide where the processor has AVX (`ScorpiusTests bench` times them separately) |

## 14. Fitted models and learned blocks

### Fitted laws

| Module | Law | Method | Residual or confidence |
|---|---|---|---|
| Harmonic EQ | RBJ-cookbook filters, all fed from the same input and summed in parallel: a low shelf at 43.8 Hz (Q 0.70), bells with Q ≈ 2/3 at 100 Hz, 983 Hz and 3.01 kHz, a high shelf at 9.66 kHz (Q 0.71); each band's boost, (H - 1) x, soft-clipped as u / (1 + \|u\|^2.15)^(1/2.15) with ceiling 0.47, then high-passed at 20 Hz (Butterworth); a knob's dB sets the filter's gain a little higher (+0.62 dB at 0.5, +3.65 at 3, +7.12 at 6) | `fit_eqfinal.py`, `fit_eqsat.py`, `fit_eqnull.py`, `fit_eqlaw.py` | two bands on equal the sum of their contributions to -142 dB; the high-pass after the clip, not before, is worth 10 … 16 dB on the low bands |
| Sub | the chain's output doubled, through a 6th-order Butterworth low-pass at 140 Hz and a high-pass at 15 Hz | `fit_sub_parallel.py` | NULLTESTS.md "sub" |
| Compression | feed-forward on the mid signal: threshold -12.8 dBFS (detector level), ratio 5.0, knee 7.3 dB, detector attack 1.0 ms and release 20 ms (nearly a peak follower: 4 % RMS); the wet path's fixed shelving a vector fit; modes a and b fit the same constants and differ in their wet filters (make-up); the gain comes before the wet filters, not after (the two agree on steady tones but not when the gain moves fast through the filters' low cut: a kick's attack) | `fit_comp.py`, `fit_comp_timing.py` | the learned correction below |
| Low | a subharmonic synthesizer an octave below the bass, an octave divider times an envelope: a flip-flop toggles at each falling zero crossing of the input through a 6th-order low-pass at 217 Hz (silent until the first, starting negative, keeping its state through silence); its square wave times the peak envelope of that signal (attack 0.05 ms, release 50 ms) times 0.89 goes through a 4th-order Butterworth low-pass at 46.4 Hz, then v + 0.91 v² (the DC it makes is kept: no high-pass) and a soft limit. On a steady tone the contribution is a square wave at half the frequency whose height follows the tone's level (at 25 Hz: -0.9 × the tone's amplitude for one cycle, +0.9 for the next) | `fit_low_parallel.py` | tones and chords -35 … -46 dB re the contribution (60 + 90 Hz gives 45 and 15 Hz; 40 + 60 + 100 Hz gives 50 and 10 Hz); a sweep 25 … 160 Hz at -30 dBFS follows the low-pass to 0.5 dB; loud tones (-3 dBFS) -10 dB (the soft limit) |
| Low on music | the octave's shape matches (correlation ±0.99 … 1.00 in most 50 ms windows of the drums) but its polarity slips against the original's now and then, so the null is about 0 dB: some crossings count differently (not a fixed or level-relative hysteresis, not a minimum interval between flips, not a reset in silence) | `fit_low_parallel.py` | open |
| Loud | its gain against a fast mid-signal detector as a table; the detector a peak follower with an instant attack and a 9.9 ms release | `fit_loud.py`, `fit_loud_timing.py` on level steps and music | the parallel's error re its contribution -19 dB |
| Loud, within a cycle | the original's gain c / x moves within each cycle about 10 times more than Scorpius's (a 50 Hz tone at -20 dBFS: 0.30 at the peak, 0.44 just after the zero crossing; Scorpius 0.35 … 0.38), and at 200 Hz its lowest point lags the peak by about a fifth of a cycle; its contribution is not flat in frequency (0.42 of the input at 40 … 60 Hz, 0.48 above 250 Hz; Scorpius 0.47 … 0.48 throughout), with up to 6 degrees of phase lead at 100 Hz | contribution against the input, sample by sample | open (Declined changes) |
| Converters at 96 and 192 kHz | a decimating FIR (the stream's first sample kept, then every 2nd / 4th) and an interpolating FIR, not linear-phase (no windowed sinc of any length its delay allows reaches its response near 20 … 24 kHz); its responses to impulses at every phase fix the pair (y_c[t] = Σ over q ≡ -c (mod R) of d[q] u[t + S - q]), the split between the two free up to a filter in z^R, taken with the decimator at unity gain | `fit_converters.py`, alternating least squares | fit -76 / -78 dB; the round trip -86 … -92 dB on music and the presets |
| Converters at 88.2 and 176.4 kHz | rational polyphase converters: the responses to impulses repeat exactly every 147 host samples (80 / 40 inner samples), so the inner instants fall 147 / 80 (147 / 40) host samples apart and one pair of filters on a grid of 1 / 80 (1 / 40) host sample describes them: v[k] = Σ_j x[j] d[147 k - 80 j], y[m] = Σ_k v[k] u[80 (m + S) - 147 k]; fitted by alternating least squares in which both steps split into small independent problems (each d tap belongs to one impulse phase; the outputs at 80 (m + S) ≡ c (mod 147) touch only the u taps ≡ c), with a line search, both filters causal, started from the 96 kHz pair in continuous time (which alone fits only -34 dB) | `fit_converters.py`, `fit_resample_high.py` | 88.2 kHz: fit -90 dB, music round trip -110 dB; 176.4 kHz converges slowly (-70 / -73 dB) |
| Grit, structure | each channel by itself: the left channel's gain is the same whatever the right one holds (silent, half, inverted), except when both are exactly equal and near full scale (the same drums at +0.4 dBFS peak: -10 dB difference; at 0.7 of that, or with the right channel at 0.999 of the left, none); nothing added to steady tones; at an onset a burst within the first 10 ms decaying by ~20 dB per 20 … 25 ms, band-limited (at -24 dBFS: -5 … -8 dB re the tone at 300 Hz … 1 kHz, -14 at 3 kHz, -25 at 100 Hz), mostly at the tone's own frequency and in phase with it, with odd harmonics once it saturates (-12 dBFS: up to +2 dB over the tone at 1 kHz); nothing below 100 Hz; the level fader scales the contribution exactly | probes | no linear filter of the input explains it (-1 dB), nor a gain on a filtered copy updated every millisecond (-4 … -10 dB) |
| Grit after compression | on stereo material grit inside the chain is not the original's grit applied to the compressor's output (-6 … -11 dB re its contribution; exact for identical channels), nor to its input, nor to its mid or swapped channels; the factory presets with both use grit at 0.189 | probes | open |
| Harmonics, fitted structure | the pattern of an EQ band: a wide bell (Q 0.32, +5.8 dB) at 1.4 times the chosen frequency (112 / 70 Hz), its boost soft-clipped and then high-passed at 20 Hz | `fit_harmlin.py`, `fit_harm.py` | -43 … -48 dB (the learned model below replaces it) |
| Harmonics, amount | not quite a mix: the output at amount a is (1 - w) x + w wet (+0.4 % of x) with w = 0.105 / 0.21 / 0.37 / 0.52 / 0.72 / 0.86 at a = 0.9 … 0.15 | `fit_harm.py` | -31 … -53 dB re the contribution that no filters on the two terms explain |
| Silence | on digital silence the original's modules give -167 dBFS RMS or less (lift -181, drive -167, compression -207; the default preset -129, its noise floor); every Scorpius module gives -149 dBFS RMS or less (lift -203, drive colour c -222 or exact zero, harmonics and grit exact zero; the default preset -140) | renders | measured |

### Learned blocks

Every learned block is trained on captures of the original's output (`render_training.py`: 174 s of program material per
setting, held-out pieces up to +4 dBFS peak), with our own weights, on the GPU when there is one. `export_models.py`
writes the weights and each network's rest state; where a network settles to a constant on silence, driven by its
biases, `--rest` computes that constant from the weights with the plug-in's own arithmetic and takes it off the
output bias (nothing is added to the plug-in's preparation).

| Block | Structure around it | Target | Training | Held out (mean, loudest piece) | Plug-in equals PyTorch |
|---|---|---|---|---|---|
| Drive colour a, hi-pass off | an LSTM of 3 layers of 24 alone: no filters around it, its output not added to its input, y = W LSTM(x) | the drive alone | `train_gru.py PURE=1 SKIP=0 GWARM=4096`, 150k steps; then from those weights 60k steps at a peak learning rate of 5e-4, batches of 64 (25 min on the GPU), then 100k steps at 3e-4 | -32.7 dB | through the plug-in, the capture's pieces -33.1 dB (hi-pass off) / -32.7 (on) |
| Drive colour a, hi-pass on | the same LSTM followed by a 2048-tap fixed filter fitted from the hi-pass-off output to the hi-pass-on output | the drive with its hi-pass | the filter: least squares | the filter alone -39.5 … -45.4 dB (the input's linear part alone: -4.5) | as above |
| Drive colour b, both hi-pass settings | the same kind of LSTM, one network, with a fitted filter for the hi-pass (-44.4 … -49.6 dB held out) | the drive alone | as colour a, then 60k steps at 5e-4 from those weights | -35.4 dB (-26.1) | as colour a |
| Drive colour c | a WaveNet of 8 channels, 12 layers of dilations 1 … 2048 with 3 taps each, the input mixed into every layer (`KERNEL=3 MIXIN=1`), its output beside a long filter, y = Post(u) + WaveNet(u), between a learned short FIR and a learned 8192-tap FIR; one per hi-pass setting (its hi-pass also a filter after the drive: -39.6 … -41.7 dB) | the drive alone | `train_wn.py` | -36.3 (-25.6) hi-pass off, -34.6 (-25.5) on | |
| Harmonics | a WaveNet as colour c's drive, learning the fully wet process at amount 1 (`render_training.py harm80 / harm50`) and at amounts 0.25, 0.5 and 0.75 the fully wet equivalent x + (y - x) / w (`train_wn.py EQUIV`); the plug-in mixes by the measured amount weights and interpolates the two models either side of the amount | the module at each amount | `train_wn.py` | -62 / -63 dB at amount 1; -51 … -75 dB at the other nodes; at 0.8 in place -55 … -71 dB | NULLTESTS.md, harmonics rows |
| Lift | a WaveNet on the wet path between a learned short FIR and a learned 8192-tap FIR | the module at amount 1 | `train_wn.py`, 60k steps | -48.1 dB | on silence -203 dBFS RMS after `--rest=lift` |
| Grit | a WaveNet as the drive's, one channel (the left, the right silent), run on each channel | the parallel at level 1 | `render_training.py grit` | in place -24 … -27 dB at level 1 (leaving it out: -20 … -25) | NULLTESTS.md, grit rows |
| Compression's gain correction | the wet path as IIR(x g 10^(c/20)), g our fitted gain and the plug-in's own IIR fixed; c (dB) from a small WaveNet that hears the detector's signal and our gain, run on each channel by itself (it hears that channel and our gain from the mid); trained through a 65536-tap copy of the IIR | the original's wet path | `train_gain.py`; mode b 4 channels, 10 layers of 3 taps (~0.13 s of memory); mode a 8 channels and 12 layers (~0.5 s, `train_gain.py a 40000 8 12`) | mode a -52.3 dB (the track excerpts -60 … -63; the start-up piece -28.2, a capture artefact: below); mode b -59.3 | to 0.1 dB on mono pieces |

**Drive.** The drive's error on the loud mastered track is broadband (-11 … -20 dB in every band), the same in loud and
quiet passages, as large as the signal in its quietest samples: dense intermodulation the model gets slightly wrong.
Colour a's network nulls its own training pieces about as well as the held-out ones (the loud track excerpts -26 …
-27 dB trained on, -24.4 held out): it underfits rather than overfits, and the loud pieces are the limit in training
too (the quiet ones to -29 dB, the loud ones to -16 … -19; trained on one loud piece alone it reaches -21 dB with 8
channels, -26 with 16). What is left after the network is spread over the spectrum, most of it from 30 Hz up.

**Arithmetic.** The plug-in's sigmoid is 1 / (1 + e^-x) with e^x by scaling and squaring (`FastMath.h`), which keeps
the tails: a forget gate near 1 is how an LSTM's slow cells remember. It matches exact activations to 0.01 dB on
every piece (through the plug-in, colour a's capture pieces -31.9 dB on average with the first-pass weights); a
sigmoid computed as 0.5 + 0.5 tanh(x / 2) with tanh clamped at 4.97 stops at 0.99995, forgets within about 20000
samples, and left -30.3 dB with the quieter pieces up to 4.5 dB worse (the track at -13 dB peak -30.9 against -35.4;
at 0 dB -27.2 alike); tanh's clamp does not matter. The hidden size is fixed at compile time, the activations computed
gate by gate and four columns a pass (`LearnedLSTM.h`).

**Rest state.** On silence colour a's network settles to a small constant (-1.4e-5, about -97 dBFS, where the original
gives none) and lift's wet network to -93 dBFS of DC (2.2e-5); colour c's drives gave -132 / -141 dBFS after the closed
expander (about 44 dB more while it is open), the harmonics models -167 … -200, grit -125 dBFS of DC (the parallels have
no expander). With `--rest` silence leaves -150 dBFS (colour a), -203 dBFS RMS (lift), -222 dBFS RMS or exact zero
(colour c), exact zero (harmonics, grit). The network itself is linear at low level (-1.40 dB from -28 to -108 dBFS,
with the plug-in's arithmetic); with the expander after the group (3) a 1 kHz sine at -60 dBFS is within 0.3 dB of the
original.

**Compression.** On held-out pieces the fitted gain and the fitted wet IIR null at -43.2 (a) / -53.8 dB (b) without the
correction; the correction learns the gain's dynamics. What it stands for in the original's terms (a detector shape, a
program-dependent release) is not pinned down. On stereo material the correction runs on each channel: the side's
gain itself matches the plain gain (drums on the mid, quiet pink noise on the side: the original's gain on the side,
solved for in 1 ms steps, within 0.15 dB rms in mode a, 0.05 in b), no linear filter of the mid or the side and no
product of the two explains the side's residual, and a share of the mid's correction on the side or a power of the
plain gain does not help (best at none and 1). Offline with the trained networks, stereo / side null on the track:

| Form | Mode a | Mode b |
|---|---|---|
| Correction from the mid, applied to both channels | -52.3 / -43.3 | -52.9 / -45.8 |
| Each channel by itself | -58.5 / -53.6 | -55.4 / -51.1 |
| Mid and side each | -52.7 / -43.9 | -53.0 / -46.0 |

Mode a's one bad held-out piece (a quiet excerpt, -28 dB with any model) is the capture's, not the original's
behaviour: over its first 0.95 s the original was still in mode b, which it applies asynchronously (0.33 dB louder,
mode b's make-up); from 1.0 s on the piece nulls at -60 … -71 dB. It is the only such piece among the 38 of each mode's
capture, and a held-out one, so the training material is clean.

Input with no mid at all (the same signal on both channels, one inverted) drops the original's output by 10 … 30 dB in
step with the drums: the expander, which reads the mid (3).

## Declined changes

| Change | Measured effect |
|---|---|
| The expander in front of the drive | a quiet sine up to 2.6 dB too loud and pink noise up to 8.5 dB (after the group: within 0.3 and 0.1 dB); a 1 kHz sine at -60 dBFS through colour a's drive 2.5 dB louder than the original (-68.3 against -70.8 dBFS) |
| The expander reading the drive's output instead of the group's | compression alone at amount 1, a -64 dBFS tone: -8.1 dB of expander gain against the original's -4.3 |
| The expander with one hold of 1.13 s at every level, closing in dB (threshold -58.1 dBFS, 208 ms time constant, taking the signal's own level at the start of playback) | up to 8 dB off below the threshold; white noise of a tone's peak 1.8 dB too little gain; pink noise through drive a up to 2.8 dB off |
| Compression's correction run on the mid and applied to both channels (in the plug-in) | the whole stereo track -43.5 dB against -48.7 without the correction, though the mid improved (-57.7 against -46.7): the side -33.3 with the corrected gain, -43.3 with the plain one |
| The EQ gains on the chunked control-rate ramp | -39 dB against -44 with a plain 5 ms ramp |
| A learned model reset to all zeros when its module is switched on | switching the drive back on nulled +1.0 dB around the switch (from its rest state: -30.7 dB); the lift from zeros -11 dB |
| Restarting the harmonics model from silence ~128 samples after an amount change | fits the tail of a rise (-45 … -56 dB from 10 ms) but not of a fall (-8 dB) |
| A high-pass after the harmonics amount (17 … 20 Hz, as the one after its boost) | explains 10 dB of the amount-change residual |
| Harmonics as one model at amount 1 mixed by weight | at 0.8 -46 … -52 dB in place (two interpolated models: -55 … -71) |
| Harmonics with the amount as an extra input of one model (`COND`) | -37 … -44 dB at amount 1 |
| Harmonics as a one-layer LSTM of 24 units | -50 dB held out (the WaveNet: -62 / -63) |
| Lift as a GRU of 16 units | -39.8 dB held out (the WaveNet: -48.1) |
| Compression's gain after the wet filters | loud drums -30.5 dB (mode b) and -29.7 (a), against -47.5 and -40.2 with the gain before |
| A hold before compression's release, a detector low shelf, feedback from the output, a detector high-pass | no improvement |
| A WaveNet learning compression's whole wet path (`render_training.py comp_a / comp_b`, 174 s per mode) | held out -43.8 / -54.0 dB against the fitted IIR's -43.2 / -53.8; in the plug-in drums -40.0 against -39.8 (a), -48.5 against -47.8 (b) |
| A WaveNet learning only what the IIR leaves (`train_wn.py KPOST=64 POSTZERO=1`) | -0.5 / +0.7 dB on that rest |
| The correction network hearing the dry signal too (`XCOND`) | no better |
| Compression mode a's correction with 16 layers (`train_gain.py a 40000 8 16`, 80 min) | held out -53.1 against -52.3 dB; in place drums -47.4 against -47.7, drums -12 -58.2 against -57.1, the track -59.2 against -58.5, the track -10 -64.6 against -64.3; the presets unchanged; a third more CPU in the correction |
| The loud parallel's detector as a peak follower with a second smoother, \|x\| or x², fitted with the gain table | -50 dB on a steady tone with a release under 1 ms, but drums and the track -14 … -17 dB against -19 |
| Grit as a transient shaper on the full band (`fit_grit.py`) | no correlation with the original's contribution |
| The 96 / 192 kHz converter split with the decimator 2.5 dB hot | drives the drive harder: -6 … -15 dB |
| Drive colour a: more channels or layers in the WaveNet | 16 channels -25.5 against -24.6 dB |
| Drive colour a: a longer memory (dilations to 8192 or 32768, 0.34 / 1.4 s) | -24.1 / -24.0 dB |
| Drive colour a: slow envelopes of the input (10 ms … 1 s) as extra inputs | -23.8 dB |
| Drive colour a: a long pre-filter | -24.2 dB |
| Drive colour a: the WaveNet's output through the long filter instead of beside it | -24.6 against -26.1 dB (8 channels; -27.2 with 12; the loudest piece -16.3 against -18.7 / -20.0), 60k steps; the default preset on the track -16.1 against -20.8 dB; beside the filter colours b and c are better on loud pieces, worse on quiet ones |
| Drive: WaveNets without 3-tap dilations and the input mixed into every layer (`KERNEL=3 MIXIN=1`) | 3 … 5 dB worse held out for every colour (loudest piece 1.4 … 2 dB; with them colour a hi-pass -29.7 (-21.8) with 12 channels); in place the default preset 1.5 … 1.8 dB worse (with them drums -26.6, the track -22.4), colour c 1.5 … 3.6, deep low end 1 … 3 |
| Drive: a longer run of the plain WaveNet (120k steps, 12 channels), a loss weighted against loud passages (`LOSSP`) | smaller gains than the 3-tap mixed-input WaveNet |
| Drive colour a: LSTMs beside filters | 1 × 24: -19.7 dB; 3 × 16 / 3 × 24: -20.5 / -21.0 after 20k steps; 3 × 24 after 100k: -23.4 (its loudest piece -13.7) |
| Drive colour a: LSTM trained from the state half a second of material leaves (`train_gru.py STATEWARM=24000`) | -20.9 dB against -21.0 without it |
| Drive colour a: LSTM output alone over windows of 16384 samples after 4096 without gradients (`SEG=16384 STATEWARM=4096`), 20k steps | -21.4 dB (loudest piece -13.1) |
| Drive colour a: the WaveNet (hi-pass off / on) | -28.3 (-20.5) / -29.7 (-21.8) dB held out, against the LSTM's -31.9 (-24.4) / -31.6 (-24.5) at its first pass |
| Drive colour a with the hi-pass: an LSTM trained for it directly | -25.7 dB at 150k steps; -26.1 at a peak learning rate of 2e-3; diverged at 300k |
| Drive colour a trained on the same material also 24, 40 and 56 dB lower (`render_training.py drive_a_wide`) | -24.4 dB held out against -31.9 (quiet pieces pass the original's expander, which the network cannot learn from the input alone) |
| A Wiener filter of 8192 taps after the drive network | -27.2 against -29.6 dB held out |
| Drive colour b as WaveNets (hi-pass off / on) | held out -33.6 (-23.7) / -32.1 (-23.6) against the LSTM's -34.9 (-25.5) / -34.7 (-25.6) at its first pass; in place, hi-pass off, the drive alone: drums -28.7, drums -12 -39.2, the track -23.0, the track -10 -34.9 dB against the LSTM's -30.0 / -40.2 / -25.2 / -36.7 (the default preset in colour b with the hi-pass off: -31.1 / -40.1 / -23.4 / -35.4 against -32.2 / -40.8 / -25.5 / -37.2) |
| Drive colour b, a further 100k steps at 3e-4 | -35.9 dB held out and 0.6 … 1.0 dB more at normal levels, but drums at -70 dBFS 0.8 … 0.9 dB worse |
| Drive colour c as an LSTM (hi-pass off / on) | held out -34.3 (-26.9) / -33.5 (-26.8); 1 … 1.5 dB better on the track, worse on quieter drums (drums -12 -36.9 against -42.0 hi-pass off, -36.7 against -39.8 on; the preset "colour c" -37.1 against -40.3) |
| Drive colour c's LSTM trained on (60k steps at 5e-4, then 100k at 3e-4) | held out -36.0, then -36.9 dB; in place the preset "colour c" drums -35.2 against -32.6, the track -27.4 against -24.9, the track -10 -38.6 against -37.0, but drums -12 -39.0 against -40.4 with the hi-pass on and quiet material 1.2 … 3 dB worse (pink noise at -78 dBFS RMS with the hi-pass off -19.7 against -29.2); its level on quiet tones and noise within 0.1 … 0.2 dB, the worst quiet case at the expander's threshold |

## Open

- The drive on loud, dense material (all of the default preset's error); the LSTM drives' fit to their own training
  material (colour a's loud pieces -26 … -27 dB, trained on or held out alike); colour c's LSTMs on quieter drums.
- Compression mode a on drums (NULLTESTS.md, "Module by module") and what its learned correction stands for.
- The default preset on drums at -70 dBFS (NULLTESTS.md, "Quiet material").
- Which crossings the low path's flip-flop counts on music; its soft limit on loud bass.
- Grit after the compressor on stereo material.
- The harmonics amount change (12).
- The loud parallel's gain within a cycle (14).

## Scripts

Each value above names the script that measured or fitted it. `fit_low_parallel.py` fits the low parallel,
`fit_sub_parallel.py` the sub parallel; `scripts/export_models.py` writes `Source/dsp/LearnedModels.h`.

## Provenance

How each part of Scorpius was made:

- Measured: the original's output on generated test signals (tones, sweeps, noise, a drum loop) and on excerpts of a
  mastered track, module by module with the others switched off; its host parameters, ranges and display text; films
  of its editor while it plays, for the meters' and the visualiser's timing and motion.
- Fitted or learned from the original's output: the EQ, sub, expander, compression's gain law, the rate converters
  and the linear filters as identified laws and constants; the drive (per colour), harmonics, lift and grit as small
  networks, and compression's gain correction, trained on captures of its output, with our own weights.
- Redrawn: the editor, laid out from measured positions and sizes and drawn in Orrery Suite's own look (its knobs,
  fader caps, meters, boxes and plate); the visualiser's stripe and glass in both particle styles drawn in code from
  measured tokens with our own shading.
- Shipped on recorded approval: the original's factory preset values, under our own names.
- Published measurement data (approval recorded 2026-11-09): [`measurements/Scorpius/`](../../measurements/Scorpius/),
  measured responses and fitted values of our own: the compressor's measured curves, the EQ tones, the module survey and
  the drive's responses, and the null tests' results (`nulltest/results.json`, the data behind NULLTESTS.md). It holds
  no render of the original and no file the original or a host wrote.
- None of the original's code, artwork, preset files, fonts or other files ships with Scorpius.
