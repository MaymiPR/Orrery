# Null tests

The same signal and settings through the reference (Cradle Orion, VST3) and through Scorpius. The residual is
reference minus ours, in dB re the reference's output energy. Lower is better: -20 dB means the difference is a tenth
of the signal's amplitude, -60 dB is inaudible in practice. Both renders are compensated by each plug-in's reported
latency, block 512; the first 0.1 s is skipped (the reference ramps its settings in over the first ~5 ms). Settings
are applied 400 ms before each render (the reference applies them asynchronously; MEASUREMENTS.md).

Signals: **drums**, a synthetic drum loop (`nulltest/order.py`), peaks near full scale, and the same 12 dB lower;
**track**, 6 s of a mastered track (local only, not in the repository), and the same 10 dB lower.

Reproduce: `python nulltest/nullchain.py model` (our processor through tools/ScRender) or `python nulltest/nullchain.py
ours` (the built VST3; the same numbers), `python nulltest/nullmod.py` for the EQ bands. The reference renders stay
local (git-ignored).

## The whole plug-in: the factory presets

48 kHz (44.1 kHz within 0.4 dB of these, except "all off"):

| Preset | drums | drums -12 | track | track -10 |
|---|---|---|---|---|
| default | -29.7 | -36.6 | -25.8 | -33.9 |
| colour c (drive colour c, compression mode a) | -32.6 | -40.3 | -24.9 | -37.0 |
| no compression | -29.8 | -36.6 | -25.8 | -33.6 |
| loud path | -29.7 | -34.9 | -25.8 | -33.2 |
| deep low end | -29.5 | -35.4 | -26.0 | -33.6 |
| all parallel | -29.7 | -36.7 | -25.6 | -33.8 |
| grit only | -32.9 | -36.6 | -33.4 | -35.1 |
| all off, 48 kHz | exact | exact | exact | exact |
| default with the drive off (the rest of the chain) | -48.2 | -51.2 | -44.8 | -49.5 |
| all off, 44.1 kHz | -51.5 | -51.5 | -63.7 | -63.7 |
| all off, 88.2 kHz | -109.2 | -109.2 | -109.7 | -109.7 |
| all off, 96 kHz | -89.7 | -89.7 | -92.2 | -92.2 |
| all off, 176.4 kHz | -73.1 | -73.1 | -73.3 | -73.3 |
| all off, 192 kHz | -86.2 | -86.2 | -86.4 | -86.4 |
| default, 88.2 kHz | -26.3 | -36.1 | -22.4 | -32.7 |
| default, 96 kHz | -27.6 | -36.4 | -23.0 | -33.0 |
| default, 176.4 kHz | -26.0 | -35.8 | -24.1 | -33.2 |
| default, 192 kHz | -29.1 | -36.7 | -24.7 | -33.6 |

## Quiet material

Where the shared expander acts (below about -58 dBFS peak; MEASUREMENTS.md 3): the same signals far lower, and pink
noise (`python nulltest/nullquiet.py`). Each cell reads without → with the expander reading the end of the group and
its mid and starting open when created with lift on, and lift giving no DC on silence:

| Signal | default | drive colour a alone (hi-pass on) |
|---|---|---|
| track at -60 dBFS | -26.7 → -32.3 | -5.8 → -30.7 |
| track at -66 dBFS | -2.9 → -28.5 | -1.2 → -28.6 |
| drums at -62 dBFS | -2.0 → -26.6 | -4.9 → -31.3 |
| drums at -70 dBFS | -0.1 → -25.4 | -4.8 → -18.8 |
| pink noise at -72 dBFS RMS | -3.3 → -34.3 | -12.0 → -32.6 |
| pink noise at -78 dBFS RMS | -1.0 → -29.4 | -12.0 → -29.5 |

The preset "grit only" on the same quiet signals nulls at -62 … -65 dB (-36 dB on the track at -60), because its
models leave no DC on silence (-45 … -58 with models that do).

## Module by module

Each module alone (the others off with the reference's own power buttons), on the same four signals:

| Module | Residual (dB) |
|---|---|
| EQ, one band at +6 dB | -55 … -67 |
| EQ, all bands at +4 dB | -46 … -48 |
| sub | -65 … -72 |
| harmonics (learned), amount 1 / 0.8 / 0.6 / 0.3 | -50 … -65 / -55 … -71 / -59 … -67 / -66 … -67 |
| compression, mode b / a (the gain corrected by a learned model) | -52.3 … -59.9 / -47.7 … -64.3 |
| loud, level 1 | -31 … -39 |
| lift (learned) | -43.5 … -51.5 |
| drive colour a, hi-pass on (learned, the default) | -25.9 … -35.6 |
| drive colour a, hi-pass off (learned) | -25.9 … -36.3 |
| grit (learned), level 1 / 0.731 | -27 … -31 / -33 … -37 |
| low, tones and chords | -38 … -46 |
| low, music | about 0 (the octave's polarity slips against the reference's) |

The learned drive models on held-out pieces of their training material (up to +4 dBFS peak), mean (loudest piece):
colour a -31.6 (-24.5) / -31.9 (-24.4) dB (hi-pass on / off: a recurrent network of 3 layers of 24, with the hi-pass
a fixed filter after it, against WaveNets at -29.7 (-21.8) / -28.3 (-20.5)), colour b -34.7 (-25.6) / -34.9
(-25.5) (the same kind of network, with the filter for the hi-pass, against WaveNets at -32.1 (-23.6) / -33.6
(-23.7)), colour c -34.6
(-25.5) / -36.3 (-25.6). The plug-in runs the recurrent networks as trained: through the plug-in, colour a's capture
pieces null at -31.9 dB on average (with exact activations the same), where a sigmoid clamped at 0.99995 left -30.3 and
the quieter pieces up to 4.5 dB worse (MEASUREMENTS.md 14). A second, finer training pass of colour a's network:
-32.7 / -32.3 dB through the plug-in, hi-pass off / on, and a third: -33.1 / -32.7. Colour b's network,
a second pass the same way: -35.4 (-26.1) held out, hi-pass off.

## Automation

A parameter jumps at 1 s and back at 2 s on the drums at -12 dB, one module on (`python nulltest/autom_probe.py`):
the null in the 0.15 s around each jump, at host blocks of 512 / 64 samples. Each cell reads without → with Cradle's
control rate (chunked amount smoothing, switches at the block start; MEASUREMENTS.md 12), modules switched on
starting from silence with the expander closed (MEASUREMENTS.md 3, 12) and the expander reading the end of the group
and its mid. For comparison the same setting held still nulls at the "steady" value.

| Change | Around the jumps, block 512 (dB) | Block 64 (dB) | Steady |
|---|---|---|---|
| compression amount 0.2 ↔ 0.9 | -41.7 / -40.1 → -60.4 / -60.5 | -46.6 / -42.1 → -60.5 / -59.3 | -61.4 |
| lift amount 0.2 ↔ 0.9 | -43.3 / -37.4 → -48.9 / -57.7 | -44.8 / -41.5 → -48.9 / -55.3 | -51.7 |
| harmonics amount 0.2 ↔ 0.9 | -23.5 / -19.7 → -33.6 / -31.5 | -22.9 / -25.4 → -29.4 / -28.9 | -68.5 |
| compression off / on | -28.6 / -22.2 → -70.4 / -59.3 | -28.5 / -28.7 → -70.0 / -57.6 | |
| lift off / on | -28.7 / -19.8 → -61.3 / -53.9 | -29.3 / -26.0 → -61.3 / -52.7 | |
| harmonics off / on | -22.8 / -27.4 → -78.4 / -69.0 | -25.5 / -29.3 → -78.2 / -70.1 | |
| EQ off / on | -23.6 / -29.6 → -54.0 / -53.7 | -27.3 / -25.7 → -54.0 / -54.6 | |
| drive off / on | -18.6 / -8.3 → -43.0 / -30.8 | -16.1 / -8.2 → -42.2 / -28.2 | |
| EQ 1 kHz 0.6 ↔ 4.8 dB | -43.8 / -43.1 (unchanged) | -42.9 / -49.9 | -52.7 |

## What the numbers say

- **The fixed parts are close to exact** (EQ, sub, the rate converters: -50 to -70 dB): these are the reference's own
  filters, identified from its responses.
- **Everything but the drive** nulls at -44 … -51 dB together (the default preset with the drive off): the
  compressor applies its gain before its filters (as the reference), lift and harmonics are learned (harmonics at
  four amounts, interpolated).
- **The whole plug-in is limited by the drive**, which the reference runs as a learned model of its own and which
  Scorpius learns from the reference's input and output: on loud program material the default preset nulls at about
  -22 to -27 dB, 10 … 12 dB lower at -32 to -37 dB. Loud, dense material is the hard part: a linear filter explains
  only 3 dB of the drive's output there, and even a model trained on one loud piece alone reaches only -21 (8
  channels) to -26 dB (16) on it.
- **Above 48 kHz** (88.2, 96, 176.4, 192 kHz) Scorpius runs the reference's own converters, identified from its
  impulse responses (-73 … -110 dB with everything off); the presets null as at 48 kHz.
- **Grit** is learned too (a transient shaper of the mids, each channel by itself), 5 … 9 dB better than a
  hand-made transient shaper; after the compressor on stereo material the reference's grit still differs a little.
- **Low** matches on tones and chords; on music its octave keeps the right shape and level but its polarity drifts
  against the reference's (which crossings its flip-flop counts is not pinned down).

## CPU

60 s of the drum loop, stereo, 48 kHz, one instance, offline, the two plug-ins in the same run: the default preset
takes 10.6 … 10.8 s of CPU against the reference's 9.1 s (drive alone 4.6 s against 5.7, lift 3.3 against 2.3,
compression 0.5 against 2.1, grit 2.8 against 4.1). The learned parts run in 8-wide vector registers where the
processor has AVX.
