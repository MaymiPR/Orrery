# Null tests

The same signal and settings through the reference (Cradle Orion 1.2.1, VST3) and through Scorpius. The residual is
reference minus ours, in dB re the reference's output energy. Lower is better: -20 dB means the difference is a tenth
of the signal's amplitude, -60 dB is inaudible in practice. Both renders are compensated by each plug-in's reported
latency, block 512; the first 0.1 s is skipped (the reference ramps its settings in over the first ~5 ms). Settings
are applied 400 ms before each render (the reference applies them asynchronously; MEASUREMENTS.md).

Signals: **drums**, a synthetic drum loop (`nulltest/probe_order.py`), peaks near full scale, and the same 12 dB lower;
**track**, 6 s of a mastered track (local only, not in the repository), and the same 10 dB lower.

Reproduce: `python nulltest/nulltest.py` (our processor through tools/ScRender) or `python nulltest/nulltest.py ours`
(the built VST3; the same numbers), then `python nulltest/nulltest.py --report`. The reference renders stay local
(git-ignored).

The words used for a residual: a null below -60 dB, close from -40 to -60 dB, a model from -20 to -40 dB, not a null
above -20 dB. Of the 174 measured cases of the three tables read from the results (presets, quiet material, the
modules), 51 are a null, 43 close, 75 a model and 5 not a null.

## The whole plug-in: the factory presets

48 kHz (44.1 kHz within 0.3 dB of these, except "all off"):

| Preset | drums | drums -12 | track | track -10 |
|---|---|---|---|---|
| default | -29.7 | -36.6 | -25.8 | -33.9 |
| colour c (drive colour c, compression mode a) | -32.6 | -40.4 | -24.9 | -37.0 |
| no compression | -29.8 | -36.6 | -25.8 | -33.6 |
| loud path | -29.7 | -35.0 | -25.8 | -33.2 |
| deep low end | -29.5 | -35.5 | -26.0 | -33.6 |
| all parallel | -29.7 | -36.7 | -25.6 | -33.8 |
| grit only | -32.9 | -36.6 | -33.4 | -35.1 |
| all off, 48 kHz | exact | exact | exact | exact |
| default with the drive off (the rest of the chain) | -48.2 | -51.2 | -44.8 | -49.5 |
| all off, 44.1 kHz | -51.5 | -51.5 | -63.7 | -63.7 |
| all off, 88.2 kHz | -109.2 | -109.2 | -109.7 | -109.7 |
| all off, 96 kHz | -89.7 | -89.7 | -92.2 | -92.2 |
| all off, 176.4 kHz | -73.1 | -73.1 | -73.2 | -73.2 |
| all off, 192 kHz | -86.2 | -86.2 | -86.4 | -86.4 |
| default, 88.2 kHz | -26.3 | -36.1 | -22.4 | -32.7 |
| default, 96 kHz | -27.6 | -36.4 | -23.0 | -33.0 |
| default, 176.4 kHz | -25.9 | -35.8 | -24.1 | -33.2 |
| default, 192 kHz | -29.1 | -36.7 | -24.7 | -33.6 |

## Quiet material

Where the shared expander acts (below about -58 dBFS peak; MEASUREMENTS.md 3): the same signals far lower, and pink
noise. The expander reads the end of the group and its mid, starts open when created with lift on, and lift gives no
DC on silence:

| Signal | default | drive colour a alone (hi-pass on) |
|---|---|---|
| track at -60 dBFS | -32.3 | -30.7 |
| track at -66 dBFS | -28.5 | -28.6 |
| drums at -62 dBFS | -26.6 | -31.3 |
| drums at -70 dBFS | -25.4 | -18.8 |
| pink noise at -72 dBFS RMS | -34.3 | -32.6 |
| pink noise at -78 dBFS RMS | -29.4 | -29.5 |

The preset "grit only" on the same quiet signals: -36.3 … -65.2 dB.

## Module by module

Each module alone (the others off with the reference's own power buttons), on the same four signals:

| Module | Residual (dB) |
|---|---|
| EQ, one band at +6 dB | -55 … -67 |
| EQ, all bands at +4 dB | -46 … -48 |
| sub, level 1 | -64.6 … -67.0 |
| harmonics (learned), amount 1 / 0.8 / 0.6 / 0.3 | -49.7 … -64.5 / -54.5 … -71.3 / -59.0 … -66.9 / -65.8 … -67.3 |
| compression, mode b / a (the gain corrected by a learned model) | -52.3 … -59.9 / -47.8 … -64.3 |
| loud, level 1 | -31.2 … -39.4 |
| lift (learned), amount 1 | -41.7 … -50.3 |
| drive colour a, hi-pass on (learned, the default) | -25.9 … -35.6 |
| drive colour a, hi-pass off (learned) | -25.9 … -36.3 |
| grit (learned), level 1 / 0.731 | -26.8 … -30.5 / -32.9 … -36.6 |
| low, level 1 (not a null: the octave keeps its shape and level, its polarity slips against the reference's) | 1.7 … -0.6 |
| low, tones and chords | -38 … -46 (measured with an earlier build and typed in: no published result file) |

The learned drive models on held-out pieces of their training material (up to +4 dBFS peak), mean (loudest piece):
colour a -31.6 (-24.5) / -31.9 (-24.4) dB (hi-pass on / off: a recurrent network of 3 layers of 24, with the hi-pass
a fixed filter after it, against WaveNets at -29.7 (-21.8) / -28.3 (-20.5)), colour b -34.7 (-25.6) / -34.9
(-25.5) (the same kind of network, with the filter for the hi-pass, against WaveNets at -32.1 (-23.6) / -33.6
(-23.7)), colour c -34.6
(-25.5) / -36.3 (-25.6). The plug-in runs the recurrent networks as trained: through the plug-in, colour a's capture
pieces leave -31.9 dB on average (with exact activations the same), where a sigmoid clamped at 0.99995 left -30.3 and
the quieter pieces up to 4.5 dB worse (MEASUREMENTS.md 14). A second, finer training pass of colour a's network:
-32.7 / -32.3 dB through the plug-in, hi-pass off / on, and a third: -33.1 / -32.7. Colour b's network,
a second pass the same way: -35.4 (-26.1) held out, hi-pass off.

## Automation

A parameter jumps at 1 s and back at 2 s on the drums at -12 dB, one module on (`python nulltest/probe_autom.py`):
the residual in the 0.15 s around the jump and around the jump back, at host blocks of 512 and 64 samples, and in the
same window of the stretch between them, where the setting is held (a module switched off there passes its input, as
the reference's does: exact). Scorpius follows the reference's control rate
(chunked amount smoothing, switches at the block start; MEASUREMENTS.md 12), switches a module on from silence with
the expander closed (MEASUREMENTS.md 3, 12) and reads the expander at the end of the group and its mid.

| Change | Around the jumps, block 512 (dB) | Block 64 (dB) | Steady, block 512 (dB) |
|---|---|---|---|
| Comp Amount 0.2 to 0.9 and back | -60.4 / -60.5 | -60.5 / -59.3 | -61.4 |
| Harm Amount 0.2 to 0.9 and back | -33.6 / -31.4 | -29.4 / -28.9 | -68.7 |
| Lift Amount 0.2 to 0.9 and back | -48.9 / -57.7 | -48.9 / -55.3 | -51.7 |
| Comp switched off and on | -70.4 / -59.3 | -70.0 / -57.6 | exact |
| Lift switched off and on | -61.4 / -53.9 | -61.3 / -52.7 | exact |
| Par Loud switched off and on | -37.9 / -35.8 | -37.6 / -37.2 | exact |
| EQ 1kHz 0.1 to 0.8 and back (normalised) | -43.8 / -43.1 | -42.9 / -49.9 | -52.7 |
| Par Loud Level 0.2 to 0.9 and back | -30.9 / -34.7 | -29.1 / -35.8 | -32.4 |
| Harm switched off and on | -78.3 / -69.0 | -78.1 / -70.0 | exact |
| Drive switched off and on | -43.0 / -30.8 | -42.2 / -28.2 | exact |
| EQ switched off and on | -54.0 / -53.7 | -54.0 / -54.6 | exact |

## What the numbers say

- **The fixed parts are close or a null** (single EQ bands, sub, the rate converters: -51 to -110 dB; all five EQ
  bands together -46 to -48 dB): these are the reference's own filters, identified from its responses.
- **Everything but the drive** is close: -44 … -51 dB together (the default preset with the drive off). The
  compressor applies its gain before its filters (as the reference), lift and harmonics are learned (harmonics at
  four amounts, interpolated).
- **The whole plug-in is limited by the drive**, which the reference runs as a learned model of its own and which
  Scorpius learns from the reference's input and output: on loud program material the default preset is a model, not a
  null: about -22 to -30 dB, 10 … 12 dB lower -33 to -37 dB. Loud, dense material is the hard part: a linear filter explains
  only 3 dB of the drive's output there, and even a model trained on one loud piece alone reaches only -21 (8
  channels) to -26 dB (16) on it.
- **Above 48 kHz** (88.2, 96, 176.4, 192 kHz) Scorpius runs the reference's own converters, identified from its
  impulse responses (-73 … -110 dB with everything off); the presets leave what they leave at 48 kHz.
- **Grit** is learned too (a transient shaper of the mids, each channel by itself), 5 … 9 dB better than a
  hand-made transient shaper; after the compressor on stereo material the reference's grit still differs a little.
- **Low** matches on tones and chords; on music its octave keeps the right shape and level but its polarity drifts
  against the reference's (which crossings its flip-flop counts is not pinned down).

## CPU

60 s of the drum loop, stereo, 48 kHz, one instance, offline, the two plug-ins in the same run: the default preset
takes 10.6 … 10.8 s of CPU against the reference's 9.1 s (drive alone 4.6 s against 5.7, lift 3.3 against 2.3,
compression 0.5 against 2.1, grit 2.8 against 4.1). The learned parts run in 8-wide vector registers where the
processor has AVX. These figures were measured with an earlier build and are typed in: no published result file
backs them yet.

## A mastered track

A demo track (a loud, dense future-house mix; local only, not in the repository) through the reference and the built VST3 at the track's own rate, block 512, with the settings a user would try (`python nulltest/null_track.py`). The worst second is the loudest part.

| Setting | Residual (dB) | Worst second (dB) |
|---|---|---|
| default | -25.39 | -20.32 |
| preset colour c | -23.99 | -16.93 |
| preset no compression | -25.06 | -15.65 |
| preset loud path | -25.42 | -20.54 |
| preset deep low end | -25.59 | -20.22 |
| preset all parallel | -25.35 | -20.53 |
| preset grit only | -33.83 | -25.15 |
| preset all off | -57.27 | -46.21 |
| drive off | -41.79 | -29.78 |
| harm off | -25.38 | -20.08 |
| lift off | -25.18 | -19.95 |
| eq off | -25.39 | -20.32 |
| comp switched off at 20 s, on at 40 s | -25.29 | -19.05 |
| drive switched off at 20 s, on at 40 s | -27.97 | -22.75 |

By the scale: 0 a null, 2 close, 12 a model, 0 not a null.

## Stress tests

`python nulltest/null_stress.py`: 334 cases over the settings, levels, signals, parameter automation, sample
rates and block sizes. Median -35.9 dB, worst 0.6 dB; by the scale: 29 a null, 64 close, 221 a model, 20 not a null.

| Run | Group | Cases | Median (dB) | Worst (dB), case |
|---|---|---|---|---|
| 48 kHz, block 512 | module alone | 30 | -52.7 | -28.8, drive, hi-pass on / drums |
| 48 kHz, block 512 | pairs | 15 | -36.0 | -8.0, comp + low / drums |
| 48 kHz, block 512 | presets | 24 | -32.7 | -28.4, colour c / bass -6 |
| 48 kHz, block 512 | eq | 20 | -54.2 | -29.7, default chain, eq 2.2/3.8/1.1/4.9/2.6 / drums |
| 48 kHz, block 512 | parallels | 20 | -43.1 | 0.6, low 0.9 / drums |
| 48 kHz, block 512 | levels | 18 | -35.6 | -24.8, default / bright peak -1 |
| 48 kHz, block 512 | io gain | 6 | -36.0 | -29.7, input +12 output -12 / drums -12 |
| 48 kHz, block 512 | random | 48 | -30.0 | -1.4, random 10 / drums |
| 48 kHz, block 512 | automation | 11 | -53.5 | -36.1, loud level: Par Loud Level 0.2 to 0.9 and back / drums -12, 3 s |
| 44.1 kHz | presets | 24 | -32.9 | -28.4, colour c / bass -6 |
| 44.1 kHz | levels | 18 | -34.7 | -22.9, default / bright peak -1 |
| 96 kHz | presets | 24 | -31.8 | -27.4, no compression / drums |
| 96 kHz | levels | 18 | -34.2 | -15.7, default / bright peak -1 |
| block 64 | levels | 18 | -35.6 | -24.8, default / bright peak -1 |
| block 64 | automation | 11 | -53.3 | -35.8, loud level: Par Loud Level 0.2 to 0.9 and back / drums -12, 3 s |
| block 2048 | levels | 18 | -35.6 | -24.8, default / bright peak -1 |
| block 2048 | automation | 11 | -25.8 | -12.7, drive power: Drive On/Off 1 to 0 and back / drums -12, 3 s |

Every case of the run "48 kHz, block 512":

| Group | Case | Residual (dB) |
|---|---|---|
| module alone | drive, hi-pass on / drums | -28.76 |
| module alone | drive, hi-pass on / dynamic -4 | -32.92 |
| module alone | drive, hi-pass off / drums | -28.81 |
| module alone | drive, hi-pass off / dynamic -4 | -32.98 |
| module alone | drive colour b / drums | -30.62 |
| module alone | drive colour b / dynamic -4 | -33.47 |
| module alone | drive colour c / drums | -30.21 |
| module alone | drive colour c / dynamic -4 | -33.46 |
| module alone | harm 0.45 / drums | -63.64 |
| module alone | harm 0.45 / dynamic -4 | -65.86 |
| module alone | harm 0.7 / drums | -61.18 |
| module alone | harm 0.7 / dynamic -4 | -63.16 |
| module alone | harm 0.9 / drums | -57.43 |
| module alone | harm 0.9 / dynamic -4 | -59.15 |
| module alone | comp 0.45 / drums | -58.28 |
| module alone | comp 0.45 / dynamic -4 | -60.66 |
| module alone | comp 0.7 / drums | -54.85 |
| module alone | comp 0.7 / dynamic -4 | -57.55 |
| module alone | comp 0.9 / drums | -53.03 |
| module alone | comp 0.9 / dynamic -4 | -55.93 |
| module alone | lift 0.45 / drums | -48.98 |
| module alone | lift 0.45 / dynamic -4 | -52.41 |
| module alone | lift 0.7 / drums | -45.63 |
| module alone | lift 0.7 / dynamic -4 | -49.18 |
| module alone | lift 0.9 / drums | -43.87 |
| module alone | lift 0.9 / dynamic -4 | -47.50 |
| module alone | comp 0.55, mode a / drums | -52.24 |
| module alone | comp 0.55, mode a / dynamic -4 | -53.60 |
| module alone | comp 0.55, mode b / drums | -56.70 |
| module alone | comp 0.55, mode b / dynamic -4 | -59.21 |
| pairs | drive + harm / drums | -29.56 |
| pairs | drive + comp / drums | -28.92 |
| pairs | drive + lift / drums | -28.99 |
| pairs | drive + eq / drums | -29.65 |
| pairs | harm + comp / drums | -57.81 |
| pairs | harm + lift / drums | -44.81 |
| pairs | harm + eq / drums | -50.52 |
| pairs | comp + lift / drums | -48.72 |
| pairs | comp + eq / drums | -49.74 |
| pairs | lift + eq / drums | -45.89 |
| pairs | drive + sub / drums | -28.05 |
| pairs | comp + low / drums | -8.02 |
| pairs | lift + loud / drums | -42.51 |
| pairs | comp + grit / drums | -35.95 |
| pairs | harm + grit / drums | -34.68 |
| presets | default / drums | -29.70 |
| presets | default / bass -6 | -28.82 |
| presets | default / wide -10 | -38.20 |
| presets | colour c / drums | -32.61 |
| presets | colour c / bass -6 | -28.40 |
| presets | colour c / wide -10 | -39.90 |
| presets | no compression / drums | -29.78 |
| presets | no compression / bass -6 | -28.67 |
| presets | no compression / wide -10 | -38.08 |
| presets | loud path / drums | -29.70 |
| presets | loud path / bass -6 | -29.70 |
| presets | loud path / wide -10 | -33.85 |
| presets | deep low end / drums | -29.49 |
| presets | deep low end / bass -6 | -29.65 |
| presets | deep low end / wide -10 | -36.05 |
| presets | all parallel / drums | -29.71 |
| presets | all parallel / bass -6 | -28.79 |
| presets | all parallel / wide -10 | -38.12 |
| presets | grit only / drums | -32.88 |
| presets | grit only / bass -6 | -53.51 |
| presets | grit only / wide -10 | -39.92 |
| presets | all off / drums | -283.85 |
| presets | all off / bass -6 | -286.77 |
| presets | all off / wide -10 | -273.60 |
| eq | eq 40Hz 1.35 / drums | -50.09 |
| eq | eq 40Hz 4.7 / drums | -53.81 |
| eq | eq 100Hz 1.35 / drums | -51.48 |
| eq | eq 100Hz 4.7 / drums | -57.48 |
| eq | eq 1kHz 1.35 / drums | -60.25 |
| eq | eq 1kHz 4.7 / drums | -64.05 |
| eq | eq 3kHz 1.35 / drums | -61.59 |
| eq | eq 3kHz 4.7 / drums | -65.95 |
| eq | eq 10kHz 1.35 / drums | -58.48 |
| eq | eq 10kHz 4.7 / drums | -60.82 |
| eq | eq 1.3/2.7/0.9/4.4/5.6 / drums | -46.47 |
| eq | eq 1.3/2.7/0.9/4.4/5.6 / bright -8 | -55.67 |
| eq | eq 1.3/2.7/0.9/4.4/5.6 / bass -6 | -43.78 |
| eq | eq 5.1/0/3.3/0/1.7 / drums | -54.45 |
| eq | eq 5.1/0/3.3/0/1.7 / bright -8 | -46.81 |
| eq | eq 5.1/0/3.3/0/1.7 / bass -6 | -56.62 |
| eq | eq 6/6/6/6/6 / drums | -54.03 |
| eq | eq 6/6/6/6/6 / bright -8 | -51.20 |
| eq | eq 6/6/6/6/6 / bass -6 | -52.45 |
| eq | default chain, eq 2.2/3.8/1.1/4.9/2.6 / drums | -29.70 |
| parallels | sub 0.25 / drums | -75.57 |
| parallels | sub 0.55 / drums | -69.42 |
| parallels | sub 0.9 / drums | -65.37 |
| parallels | low 0.25 / drums | -15.66 |
| parallels | low 0.55 / drums | -5.91 |
| parallels | low 0.9 / drums | 0.57 |
| parallels | loud 0.25 / drums | -54.80 |
| parallels | loud 0.55 / drums | -44.97 |
| parallels | loud 0.9 / drums | -37.18 |
| parallels | grit 0.25 / drums | -47.60 |
| parallels | grit 0.55 / drums | -37.48 |
| parallels | grit 0.9 / drums | -28.99 |
| parallels | sub 0.25 / bass -6 | -75.78 |
| parallels | sub 0.55 / bass -6 | -71.59 |
| parallels | sub 0.9 / bass -6 | -68.59 |
| parallels | low 0.25 / bass -6 | -50.92 |
| parallels | low 0.55 / bass -6 | -41.25 |
| parallels | low 0.9 / bass -6 | -34.90 |
| parallels | default chain, all four 0.4 / drums | -29.70 |
| parallels | default chain, all four 0.4 / wide -10 | -38.20 |
| levels | default / drums peak -30 | -37.06 |
| levels | default / drums peak -24 | -37.04 |
| levels | default / drums peak -18 | -36.92 |
| levels | default / drums peak -12 | -36.64 |
| levels | default / drums peak -6 | -35.56 |
| levels | default / drums peak -3 | -33.72 |
| levels | default / drums peak -1 | -31.68 |
| levels | default / bass peak -30 | -35.66 |
| levels | default / bass peak -12 | -33.86 |
| levels | default / bass peak -1 | -25.17 |
| levels | default / bright peak -30 | -47.11 |
| levels | default / bright peak -12 | -36.30 |
| levels | default / bright peak -1 | -24.82 |
| levels | default / wide peak -30 | -39.41 |
| levels | default / wide peak -12 | -38.55 |
| levels | default / wide peak -1 | -31.91 |
| levels | default / dynamic -4 | -33.82 |
| levels | default / sweep -6 | -33.68 |
| io gain | input -12 output +0 / drums -12 | -37.03 |
| io gain | input -6 output +3 / drums -12 | -36.92 |
| io gain | input +6 output -6 / drums -12 | -35.40 |
| io gain | input +12 output -12 / drums -12 | -29.70 |
| io gain | input +0 output +12 / drums -12 | -36.61 |
| io gain | input +9.5 output +0 / drums -12 | -32.96 |
| random | random 00 / drums | -17.21 |
| random | random 00 / wide -10 | -19.30 |
| random | random 01 / drums | -27.55 |
| random | random 01 / wide -10 | -35.76 |
| random | random 02 / drums | -27.72 |
| random | random 02 / wide -10 | -37.09 |
| random | random 03 / drums | -44.38 |
| random | random 03 / wide -10 | -45.99 |
| random | random 04 / drums | -32.86 |
| random | random 04 / wide -10 | -39.06 |
| random | random 05 / drums | -34.02 |
| random | random 05 / wide -10 | -34.41 |
| random | random 06 / drums | -39.44 |
| random | random 06 / wide -10 | -37.83 |
| random | random 07 / drums | -5.92 |
| random | random 07 / wide -10 | -10.31 |
| random | random 08 / drums | -33.94 |
| random | random 08 / wide -10 | -35.40 |
| random | random 09 / drums | -30.72 |
| random | random 09 / wide -10 | -38.27 |
| random | random 10 / drums | -1.42 |
| random | random 10 / wide -10 | -2.79 |
| random | random 11 / drums | -23.49 |
| random | random 11 / wide -10 | -33.50 |
| random | random 12 / drums | -18.48 |
| random | random 12 / wide -10 | -20.60 |
| random | random 13 / drums | -23.65 |
| random | random 13 / wide -10 | -31.31 |
| random | random 14 / drums | -13.21 |
| random | random 14 / wide -10 | -18.22 |
| random | random 15 / drums | -29.31 |
| random | random 15 / wide -10 | -34.22 |
| random | random 16 / drums | -16.10 |
| random | random 16 / wide -10 | -21.94 |
| random | random 17 / drums | -18.42 |
| random | random 17 / wide -10 | -23.39 |
| random | random 18 / drums | -31.58 |
| random | random 18 / wide -10 | -38.73 |
| random | random 19 / drums | -3.23 |
| random | random 19 / wide -10 | -6.91 |
| random | random 20 / drums | -20.74 |
| random | random 20 / wide -10 | -37.25 |
| random | random 21 / drums | -19.84 |
| random | random 21 / wide -10 | -36.91 |
| random | random 22 / drums | -20.62 |
| random | random 22 / wide -10 | -36.29 |
| random | random 23 / drums | -32.45 |
| random | random 23 / wide -10 | -39.56 |
| automation | comp amount: Comp Amount 0.2 to 0.9 and back / drums -12, 3 s | -64.11 |
| automation | harm amount: Harm Amount 0.2 to 0.9 and back / drums -12, 3 s | -44.70 |
| automation | lift amount: Lift Amount 0.2 to 0.9 and back / drums -12, 3 s | -54.45 |
| automation | comp power: Comp On/Off 1 to 0 and back / drums -12, 3 s | -62.26 |
| automation | lift power: Lift On/Off 1 to 0 and back / drums -12, 3 s | -53.47 |
| automation | loud power: Par Loud On/Off 1 to 0 and back / drums -12, 3 s | -37.32 |
| automation | eq gain: EQ 1kHz 0.1 to 0.8 and back / drums -12, 3 s | -50.76 |
| automation | loud level: Par Loud Level 0.2 to 0.9 and back / drums -12, 3 s | -36.06 |
| automation | harm power: Harm On/Off 1 to 0 and back / drums -12, 3 s | -72.49 |
| automation | drive power: Drive On/Off 1 to 0 and back / drums -12, 3 s | -37.39 |
| automation | eq power: EQ On/Off 1 to 0 and back / drums -12, 3 s | -53.54 |
