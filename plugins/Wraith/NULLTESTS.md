# Null tests

The same signal and settings through the reference (Cradle The Spirit 1.0.3, VST3) and through Wraith.
The residual is reference minus ours, in dB re the reference's output energy. Lower is better: -20 dB means the
difference is a tenth of the signal's amplitude, -60 dB is inaudible in practice. Both plug-ins report no latency.
48 kHz unless the case says otherwise, block 512, the first 0.1 s skipped. Stages are isolated with the
reference's own power buttons. Presets are loaded on the reference from its own saved states.

Reproduce: `python nulltest/nulltest.py` (our processor through tools/WrRender) and
`python nulltest/nulltest.py --ours vst3` (the built VST3 through tools/RefRender). The reference renders stay local.

| Case | Signal | Residual (dB) | Worst second (dB) |
|---|---|---|---|
| path: every stage off | pink -18 | -337.8 | -331.2 |
| gains: in -6, out +4 | pink -18 | -143.6 | -143.5 |
| eq: start-up values | pink -18 | -137.8 | -137.5 |
| eq: low -7.5, high +9 | pink -18 | -127.8 | -127.8 |
| rider: start-up values | pink -18 | -86.1 | -80.0 |
| rider: amount 1, floor -50, speed 0.01 | pink -18 | -63.4 | -57.4 |
| character: start-up (compression 0, focus +8) | pink -18 | -27.2 | -22.5 |
| character: compression +50, focus -30 | pink -18 | -25.8 | -21.0 |
| character: compression -50, focus +50 | pink -18 | -25.5 | -25.3 |
| doubler: mix 0.1, stereo 1 | pink -18 | -32.3 | -31.3 |
| doubler: mix 1, stereo 0.5 | pink -18 | -19.4 | -18.1 |
| reverb: room, start-up values | pink -18 | -90.6 | -88.0 |
| reverb: room, mix 1, filter 3.5 kHz | pink -18 | -72.8 | -69.5 |
| full chain: start-up ("lead") | pink -18 | -26.9 | -22.3 |
| full chain: start-up, 44.1 kHz | pink -18 | -27.1 | -23.1 |
| full chain: start-up, 96 kHz | pink -18 | -23.8 | -18.2 |
| path: every stage off | sweep -12 | -340.7 | -334.8 |
| gains: in -6, out +4 | sweep -12 | -143.8 | -143.8 |
| eq: start-up values | sweep -12 | -137.9 | -137.5 |
| eq: low -7.5, high +9 | sweep -12 | -127.6 | -127.9 |
| rider: start-up values | sweep -12 | -123.4 | -122.9 |
| rider: amount 1, floor -50, speed 0.01 | sweep -12 | -113.2 | -112.9 |
| character: start-up (compression 0, focus +8) | sweep -12 | -17.1 | -14.9 |
| character: compression +50, focus -30 | sweep -12 | -20.5 | -15.5 |
| character: compression -50, focus +50 | sweep -12 | -16.1 | -15.7 |
| doubler: mix 0.1, stereo 1 | sweep -12 | -25.2 | -22.8 |
| doubler: mix 1, stereo 0.5 | sweep -12 | -11.3 | -8.1 |
| reverb: room, start-up values | sweep -12 | -91.5 | -88.2 |
| reverb: room, mix 1, filter 3.5 kHz | sweep -12 | -74.0 | -71.1 |
| full chain: start-up ("lead") | sweep -12 | -16.8 | -13.8 |
| full chain: start-up, 44.1 kHz | sweep -12 | -17.0 | -16.2 |
| full chain: start-up, 96 kHz | sweep -12 | -14.9 | -9.8 |
| path: every stage off | drums -6 | -329.3 | -323.8 |
| gains: in -6, out +4 | drums -6 | -143.5 | -143.5 |
| eq: start-up values | drums -6 | -136.7 | -136.7 |
| eq: low -7.5, high +9 | drums -6 | -129.0 | -129.0 |
| rider: start-up values | drums -6 | -103.0 | -103.2 |
| rider: amount 1, floor -50, speed 0.01 | drums -6 | -96.5 | -96.3 |
| character: start-up (compression 0, focus +8) | drums -6 | -20.8 | -20.9 |
| character: compression +50, focus -30 | drums -6 | -15.1 | -15.1 |
| character: compression -50, focus +50 | drums -6 | -25.2 | -25.4 |
| doubler: mix 0.1, stereo 1 | drums -6 | -28.6 | -28.9 |
| doubler: mix 1, stereo 0.5 | drums -6 | -15.9 | -16.3 |
| reverb: room, start-up values | drums -6 | -91.7 | -89.9 |
| reverb: room, mix 1, filter 3.5 kHz | drums -6 | -74.3 | -72.0 |
| full chain: start-up ("lead") | drums -6 | -21.0 | -21.2 |
| full chain: start-up, 44.1 kHz | drums -6 | -20.1 | -20.4 |
| full chain: start-up, 96 kHz | drums -6 | -20.8 | -20.5 |
| path: every stage off | music -10 | -336.0 | -330.0 |
| gains: in -6, out +4 | music -10 | -143.5 | -143.5 |
| eq: start-up values | music -10 | -137.6 | -137.6 |
| eq: low -7.5, high +9 | music -10 | -128.9 | -128.8 |
| rider: start-up values | music -10 | -114.3 | -113.6 |
| rider: amount 1, floor -50, speed 0.01 | music -10 | -107.8 | -107.0 |
| character: start-up (compression 0, focus +8) | music -10 | -23.6 | -22.5 |
| character: compression +50, focus -30 | music -10 | -20.8 | -19.5 |
| character: compression -50, focus +50 | music -10 | -28.6 | -26.7 |
| doubler: mix 0.1, stereo 1 | music -10 | -39.0 | -38.4 |
| doubler: mix 1, stereo 0.5 | music -10 | -27.2 | -26.1 |
| reverb: room, start-up values | music -10 | -92.3 | -88.7 |
| reverb: room, mix 1, filter 3.5 kHz | music -10 | -73.5 | -71.0 |
| full chain: start-up ("lead") | music -10 | -23.6 | -22.6 |
| full chain: start-up, 44.1 kHz | music -10 | -23.4 | -21.7 |
| full chain: start-up, 96 kHz | music -10 | -20.9 | -19.7 |
| preset: lead | pink -18 | -26.9 | -22.3 |
| preset: lead | drums -6 | -21.0 | -21.2 |
| preset: lead | music -10 | -23.4 | -22.4 |
| preset: up front | pink -18 | -27.0 | -22.2 |
| preset: up front | drums -6 | -20.9 | -21.0 |
| preset: up front | music -10 | -23.4 | -22.3 |
| preset: wide image | pink -18 | -12.0 | -11.6 |
| preset: wide image | drums -6 | -16.5 | -16.8 |
| preset: wide image | music -10 | -19.8 | -19.2 |
| preset: short phase | pink -18 | -11.5 | -11.2 |
| preset: short phase | drums -6 | -16.3 | -16.4 |
| preset: short phase | music -10 | -16.9 | -16.4 |
| preset: wide and wet | pink -18 | -12.1 | -11.4 |
| preset: wide and wet | drums -6 | -12.6 | -12.6 |
| preset: wide and wet | music -10 | -11.8 | -10.4 |
| preset: wide lead | pink -18 | -21.0 | -19.1 |
| preset: wide lead | drums -6 | -19.8 | -20.0 |
| preset: wide lead | music -10 | -22.2 | -21.9 |
| preset: backing stack | pink -18 | -18.6 | -17.0 |
| preset: backing stack | drums -6 | -19.0 | -19.1 |
| preset: backing stack | music -10 | -19.0 | -18.8 |
| preset: big cave | pink -18 | -13.1 | -12.6 |
| preset: big cave | drums -6 | -14.8 | -14.9 |
| preset: big cave | music -10 | -14.2 | -13.2 |
| preset: doubler alone | pink -18 | -17.8 | -16.6 |
| preset: doubler alone | drums -6 | -13.6 | -14.0 |
| preset: doubler alone | music -10 | -26.0 | -24.8 |
| preset: soft room | pink -18 | -26.9 | -22.1 |
| preset: soft room | drums -6 | -20.6 | -20.8 |
| preset: soft room | music -10 | -23.4 | -22.6 |
| preset: hard squeeze | pink -18 | -22.4 | -19.3 |
| preset: hard squeeze | drums -6 | -4.4 | -4.3 |
| preset: hard squeeze | music -10 | -21.1 | -19.6 |

Signals: **pink -18**: pink noise, -18 dBFS RMS; **sweep -12**: log sine sweep 20 Hz - 20 kHz, -12 dBFS; **drums -6**: synthetic drum loop (kick, snare, hats), peaks -6 dBFS; **music -10**: synthetic mix (bass, chords, noise bed, drums), peaks -10 dBFS.

Median -23.8 dB over 97 cases; worst -4.4 dB (preset: hard squeeze / drums -6).

| Part | Cases | Median (dB) | Best (dB) | Worst (dB) |
|---|---|---|---|---|
| path | 4 | -336.9 | -340.7 | -329.3 |
| gains | 4 | -143.5 | -143.8 | -143.5 |
| eq | 8 | -132.9 | -137.9 | -127.6 |
| rider | 8 | -105.4 | -123.4 | -63.4 |
| character | 12 | -22.2 | -28.6 | -15.1 |
| doubler | 8 | -26.2 | -39.0 | -11.3 |
| reverb | 8 | -82.5 | -92.3 | -72.8 |
| full chain | 12 | -20.9 | -27.1 | -14.9 |
| preset | 33 | -19.0 | -27.0 | -4.4 |

## What the numbers say

The words used for a residual: a null below -60 dB, close from -40 to -60 dB, a model from -20 to -40 dB, not a null
above -20 dB. Of the 97 cases, 32 are a null, 0 close, 37 a model and 28 not a null.

- **Exact:** with every stage off the output is the input (-329 to -341 dB). The input and output gains (-144 dB),
  the EQ's two shelves (-128 to -138 dB) and the gain rider (-63 to -123 dB; the -63 is a fast rider on pink noise, the
  rest -96 dB and better) are the original's own laws, and the reverb's room is its measured response (-73 dB fully
  wet, where the 16-bit storage of the response sets the floor, to -92 dB at its start-up mix). The plate, which the
  original only plays with its editor open, leaves -95 dB at a typical mix and -52 dB fully wet, which is close and
  not exact (null_plate.py; typed in, no published result file yet).
- **A model:** the character section, at its worst not a null, is a fitted model of the original's expander, drive and compressor: -16 to
  -29 dB on noise, sweeps and music, -15 to -25 dB on drums. Its expander has its own slow-release detector, measured
  on the original's gain (MEASUREMENTS.md 4.3): it holds its gain through the gaps between drum hits, as the original
  does. Its compressor overshoots a rise in level as the original's does, by about 0.3 of its reduction, and lets go
  slowly after a short burst and fast after a long one (MEASUREMENTS.md 4.4): with the overshoot, drums at the
  start-up settings leave -19.0 dB (-14.2 dB without it) and pink noise at -26.5 dB (-21.8 dB without it). Its
  static curve is a table of the original's, one curve of the driven level at every Compression setting
  (MEASUREMENTS.md 4.1): with the table, music at Compression -50 / Focus +50 leaves -28.6 dB (-18.2 dB with a
  single curve) and drums at the start-up settings at -20.8 dB (-19.0 dB with a single curve).
  What the two cost: five cases are 0.5 to 3.0 dB worse with the overshoot than without it (Compression -50 / Focus
  +50 on pink noise -25.5 dB against -28.3 dB, Compression +50 / Focus -30 on music -20.8 dB against -21.0 dB and on
  the sweep -20.5 dB against -21.0 dB, "short phase" and "wide image" on pink noise about 0.5 dB each), each a level
  offset of 0.3 dB or so from the refitted release times; the table costs the sweep at the start-up settings 0.3 to
  0.4 dB (Character -17.1 dB against -17.5 dB, the full chain -16.8 dB against -17.1 dB, at 44.1 kHz -16.9 dB
  against -17.3 dB). Being first in the chain, the section sets the residual of everything after it: the start-up
  preset lands at -24 dB on music and -21 dB on drums. The with-and-without figures of this paragraph are from
  earlier builds and are typed in; the table above is the current data.
- **The doubler, a model:** its two voices, their modulation and its stereo matrix are the original's; the
  modulation runs at the original's measured rate (about 0.503 Hz, per sample rate: MEASUREMENTS.md 7.1), not as a
  pseudo-random wobble of its delay. The voices are band-limited (a high-pass near 500 Hz, low-passes above 6 kHz)
  and the lows pass the delay line undelayed, as measured. It leaves -25 to -39 dB at Mix 0.1 and -11 to -27 dB
  fully wet, not a null at its worst; at full wet what is left is in the voices themselves, not their delay (worst on the sweep and on drums
  at Stereo 1). By what it does, at full wet (measure_doubler.py):

  | Signal, setting | Spectrum error, rms (dB, third octaves) | Spectrum error, worst (dB) | L / R correlation, original | ours | Level, ours less original (dB) |
  |---|---|---|---|---|---|
  | pink -18, Stereo 0 | 0.60 | 1.90 | 1.000 | 1.000 | 0.11 |
  | pink -18, Stereo 0.5 | 0.60 | 1.90 | 0.977 | 0.987 | 0.09 |
  | pink -18, Stereo 1 | 0.60 | 1.90 | 0.912 | 0.949 | 0.03 |
  | music -10, Stereo 0 | 0.44 | 1.19 | 1.000 | 1.000 | -0.05 |
  | music -10, Stereo 0.5 | 0.44 | 1.19 | 0.997 | 0.996 | -0.05 |
  | music -10, Stereo 1 | 0.44 | 1.19 | 0.988 | 0.983 | -0.04 |

- **Presets** follow from their stages: the ones with the doubler land at -11 to -26 dB, the ones without it where the
  character section does (-21 to -27 dB), except the one with the rider at 0.97 into full compression on drums
  (-4.4 dB), where the two together do not null.
- **Our VST3 equals our renderer:** `nulltest.py --ours vst3` gives the same numbers to the printed digit, and
  `first_null.py` finds the two equal at -333 dB at the start-up preset.

## A mastered track

A demo track (a loud, dense future-house mix; local only, not in the repository) through the reference and the built VST3 at the track's own rate, block 512 (`python nulltest/null_track.py`). The track is a full mix, not a vocal: a stress case for a vocal chain.

| Setting | Residual (dB) | Worst second (dB) |
|---|---|---|
| start-up settings | -16.59 | -7.4 |
| every stage on | -16.25 | -7.82 |
| every stage off | -356.01 | -257.43 |
| rider off, the others on | -15.3 | -7.82 |
| character off, the others on | -25.33 | -19.67 |
| eq off, the others on | -16.85 | -7.82 |
| doubler off, the others on | -17.86 | -7.4 |
| reverb off, the others on | -16.27 | -7.8 |
| rider alone | -110.73 | -103.6 |
| character alone | -17.33 | -7.4 |
| eq alone | -136.88 | -132.35 |
| doubler alone | -25.56 | -19.67 |
| reverb alone | -89.58 | -62.13 |
| reverb switched off at 23 s, on at 46 s | -16.61 | -7.4 |
| character switched off at 23 s, on at 46 s | -26.64 | -7.4 |

By the scale: 4 a null, 0 close, 3 a model, 8 not a null.

## Stress tests

`python nulltest/null_stress.py`: 260 cases over the settings, levels, signals, parameter automation, sample
rates and block sizes. Median -19.3 dB, worst -5.1 dB; by the scale: 53 a null, 5 close, 69 a model, 133 not a null.

| Run | Group | Cases | Median (dB) | Worst (dB), case |
|---|---|---|---|---|
| 48 kHz, block 512 | alone rider | 6 | -111.8 | -53.8, rider alone: amount 0.85, floor -23.5, speed 0.007 / dynamic -4 |
| 48 kHz, block 512 | alone character | 6 | -18.0 | -11.3, character alone: compression 38, focus 41 / voice -8 |
| 48 kHz, block 512 | alone eq | 6 | -130.1 | -126.3, eq alone: low -10.5, high 7.9 / music -10 |
| 48 kHz, block 512 | alone doubler | 6 | -20.1 | -7.5, doubler alone: mix 0.85, stereo 1 / voice -8 |
| 48 kHz, block 512 | alone reverb | 6 | -76.0 | -73.5, reverb alone: mix 0.9, filter 2700 / music -10 |
| 48 kHz, block 512 | pairs | 20 | -18.3 | -11.2, character + doubler / voice -8 |
| 48 kHz, block 512 | io gain | 4 | -145.7 | -141.1, gains only: in -4.5, out 7.5 / music -10 |
| 48 kHz, block 512 | presets | 14 | -14.6 | -7.7, preset: doubler alone / voice -8 |
| 48 kHz, block 512 | levels | 16 | -22.2 | -12.4, full chain: start-up / voice -1 |
| 48 kHz, block 512 | random | 48 | -13.0 | -5.1, random 16 (EQ+DBL+REV) / drums -6 |
| 48 kHz, block 512 | automation | 8 | -64.8 | -13.1, gain and eq moves, full chain: start-up / voice -8 |
| 44.1 kHz | pairs | 20 | -17.4 | -11.2, character + doubler / voice -8 |
| 44.1 kHz | levels | 16 | -22.1 | -11.9, full chain: start-up / voice -1 |
| 96 kHz | pairs | 20 | -18.4 | -11.3, character + doubler / voice -8 |
| 96 kHz | levels | 16 | -19.3 | -13.0, full chain: start-up / voice -1 |
| block 64 | levels | 16 | -22.2 | -12.4, full chain: start-up / voice -1 |
| block 64 | automation | 8 | -65.1 | -13.1, gain and eq moves, full chain: start-up / voice -8 |
| block 2048 | levels | 16 | -22.2 | -12.4, full chain: start-up / voice -1 |
| block 2048 | automation | 8 | -65.8 | -13.1, gain and eq moves, full chain: start-up / voice -8 |

Every case of the run "48 kHz, block 512":

| Group | Case | Residual (dB) |
|---|---|---|
| alone rider | rider alone: amount 0.35, floor -41.5, speed 0.002 / voice -8 | -115.64 |
| alone rider | rider alone: amount 0.35, floor -41.5, speed 0.002 / dynamic -4 | -121.30 |
| alone rider | rider alone: amount 0.85, floor -23.5, speed 0.007 / voice -8 | -57.56 |
| alone rider | rider alone: amount 0.85, floor -23.5, speed 0.007 / dynamic -4 | -53.78 |
| alone rider | rider alone: amount 0.55, floor -33.5, speed 0.005 / voice -8 | -107.99 |
| alone rider | rider alone: amount 0.55, floor -33.5, speed 0.005 / dynamic -4 | -117.40 |
| alone character | character alone: compression 17, focus -13 / voice -8 | -13.47 |
| alone character | character alone: compression 17, focus -13 / music -10 | -22.44 |
| alone character | character alone: compression -33, focus 27 / voice -8 | -13.04 |
| alone character | character alone: compression -33, focus 27 / music -10 | -24.82 |
| alone character | character alone: compression 38, focus 41 / voice -8 | -11.30 |
| alone character | character alone: compression 38, focus 41 / music -10 | -22.69 |
| alone eq | eq alone: low 3.3, high -4.7 / voice -8 | -134.04 |
| alone eq | eq alone: low 3.3, high -4.7 / music -10 | -137.56 |
| alone eq | eq alone: low -10.5, high 7.9 / voice -8 | -130.32 |
| alone eq | eq alone: low -10.5, high 7.9 / music -10 | -126.31 |
| alone eq | eq alone: low 11.1, high 11.7 / voice -8 | -128.84 |
| alone eq | eq alone: low 11.1, high 11.7 / music -10 | -129.97 |
| alone doubler | doubler alone: mix 0.25, stereo 0.8 / voice -8 | -15.64 |
| alone doubler | doubler alone: mix 0.25, stereo 0.8 / music -10 | -33.38 |
| alone doubler | doubler alone: mix 0.55, stereo 0.15 / voice -8 | -13.41 |
| alone doubler | doubler alone: mix 0.55, stereo 0.15 / music -10 | -30.35 |
| alone doubler | doubler alone: mix 0.85, stereo 1 / voice -8 | -7.50 |
| alone doubler | doubler alone: mix 0.85, stereo 1 / music -10 | -24.51 |
| alone reverb | reverb alone: mix 0.25, filter 12500 / voice -8 | -81.87 |
| alone reverb | reverb alone: mix 0.25, filter 12500 / music -10 | -81.12 |
| alone reverb | reverb alone: mix 0.6, filter 5200 / voice -8 | -76.36 |
| alone reverb | reverb alone: mix 0.6, filter 5200 / music -10 | -74.25 |
| alone reverb | reverb alone: mix 0.9, filter 2700 / voice -8 | -75.74 |
| alone reverb | reverb alone: mix 0.9, filter 2700 / music -10 | -73.46 |
| pairs | rider + character / voice -8 | -13.78 |
| pairs | rider + character / drums -6 | -18.33 |
| pairs | rider + eq / voice -8 | -115.49 |
| pairs | rider + eq / drums -6 | -110.63 |
| pairs | rider + doubler / voice -8 | -15.65 |
| pairs | rider + doubler / drums -6 | -19.06 |
| pairs | rider + reverb / voice -8 | -81.91 |
| pairs | rider + reverb / drums -6 | -80.57 |
| pairs | character + eq / voice -8 | -13.33 |
| pairs | character + eq / drums -6 | -18.24 |
| pairs | character + doubler / voice -8 | -11.16 |
| pairs | character + doubler / drums -6 | -17.60 |
| pairs | character + reverb / voice -8 | -13.42 |
| pairs | character + reverb / drums -6 | -18.37 |
| pairs | eq + doubler / voice -8 | -15.53 |
| pairs | eq + doubler / drums -6 | -23.65 |
| pairs | eq + reverb / voice -8 | -81.84 |
| pairs | eq + reverb / drums -6 | -80.27 |
| pairs | doubler + reverb / voice -8 | -14.76 |
| pairs | doubler + reverb / drums -6 | -16.88 |
| io gain | gains only: in -12, out 0 / music -10 | -145.92 |
| io gain | gains only: in -4.5, out 7.5 / music -10 | -141.11 |
| io gain | gains only: in 9.3, out -9.3 / music -10 | -150.06 |
| io gain | gains only: in 12, out -12 / music -10 | -145.44 |
| presets | preset: lead / voice -8 | -13.34 |
| presets | preset: lead / music -10 | -23.63 |
| presets | preset: up front / voice -8 | -13.55 |
| presets | preset: up front / music -10 | -23.43 |
| presets | preset: wide image / voice -8 | -8.08 |
| presets | preset: wide image / music -10 | -19.49 |
| presets | preset: short phase / voice -8 | -7.79 |
| presets | preset: short phase / music -10 | -15.71 |
| presets | preset: doubler alone / voice -8 | -7.66 |
| presets | preset: doubler alone / music -10 | -25.63 |
| presets | preset: soft room / voice -8 | -13.48 |
| presets | preset: soft room / music -10 | -23.41 |
| presets | preset: hard squeeze / voice -8 | -11.61 |
| presets | preset: hard squeeze / music -10 | -21.21 |
| levels | full chain: start-up / music -30 | -17.19 |
| levels | full chain: start-up / music -20 | -31.36 |
| levels | full chain: start-up / music -10 | -23.63 |
| levels | full chain: start-up / music -6 | -22.14 |
| levels | full chain: start-up / music -1 | -22.21 |
| levels | full chain: start-up / voice -30 | -33.71 |
| levels | full chain: start-up / voice -18 | -15.79 |
| levels | full chain: start-up / voice -8 | -13.34 |
| levels | full chain: start-up / voice -1 | -12.36 |
| levels | full chain: start-up / drums -18 | -28.70 |
| levels | full chain: start-up / drums -1 | -17.46 |
| levels | full chain: start-up / bass -6 | -24.23 |
| levels | full chain: start-up / bright -8 | -23.63 |
| levels | full chain: start-up / wide -10 | -27.73 |
| levels | full chain: start-up / dynamic -4 | -21.43 |
| levels | full chain: start-up / sweep -12 | -16.79 |
| random | random 00 (RIDER+CHAR+EQ+DBL+REV) / voice -8 | -5.53 |
| random | random 00 (RIDER+CHAR+EQ+DBL+REV) / drums -6 | -8.32 |
| random | random 01 (RIDER+CHAR+EQ+DBL+REV) / voice -8 | -9.79 |
| random | random 01 (RIDER+CHAR+EQ+DBL+REV) / drums -6 | -11.55 |
| random | random 02 (RIDER+EQ+DBL) / voice -8 | -18.31 |
| random | random 02 (RIDER+EQ+DBL) / drums -6 | -20.66 |
| random | random 03 (RIDER+CHAR+EQ+DBL+REV) / voice -8 | -6.07 |
| random | random 03 (RIDER+CHAR+EQ+DBL+REV) / drums -6 | -11.66 |
| random | random 04 (CHAR+EQ+DBL) / voice -8 | -7.92 |
| random | random 04 (CHAR+EQ+DBL) / drums -6 | -12.59 |
| random | random 05 (RIDER+CHAR+EQ+DBL) / voice -8 | -14.51 |
| random | random 05 (RIDER+CHAR+EQ+DBL) / drums -6 | -20.87 |
| random | random 06 (RIDER+CHAR+DBL+REV) / voice -8 | -13.74 |
| random | random 06 (RIDER+CHAR+DBL+REV) / drums -6 | -16.94 |
| random | random 07 (RIDER+CHAR+DBL+REV) / voice -8 | -6.15 |
| random | random 07 (RIDER+CHAR+DBL+REV) / drums -6 | -9.57 |
| random | random 08 (EQ+DBL+REV) / voice -8 | -13.01 |
| random | random 08 (EQ+DBL+REV) / drums -6 | -13.31 |
| random | random 09 (RIDER+CHAR+EQ+REV) / voice -8 | -13.46 |
| random | random 09 (RIDER+CHAR+EQ+REV) / drums -6 | -21.32 |
| random | random 10 (RIDER+CHAR+EQ) / voice -8 | -13.08 |
| random | random 10 (RIDER+CHAR+EQ) / drums -6 | -22.05 |
| random | random 11 (RIDER+CHAR+EQ+DBL+REV) / voice -8 | -6.98 |
| random | random 11 (RIDER+CHAR+EQ+DBL+REV) / drums -6 | -10.76 |
| random | random 12 (EQ+DBL) / voice -8 | -8.72 |
| random | random 12 (EQ+DBL) / drums -6 | -13.48 |
| random | random 13 (RIDER+CHAR+EQ+DBL+REV) / voice -8 | -11.87 |
| random | random 13 (RIDER+CHAR+EQ+DBL+REV) / drums -6 | -17.59 |
| random | random 14 (RIDER+CHAR) / voice -8 | -13.09 |
| random | random 14 (RIDER+CHAR) / drums -6 | -16.27 |
| random | random 15 (CHAR+REV) / voice -8 | -10.99 |
| random | random 15 (CHAR+REV) / drums -6 | -14.25 |
| random | random 16 (EQ+DBL+REV) / voice -8 | -5.27 |
| random | random 16 (EQ+DBL+REV) / drums -6 | -5.14 |
| random | random 17 (CHAR+EQ+REV) / voice -8 | -12.97 |
| random | random 17 (CHAR+EQ+REV) / drums -6 | -17.51 |
| random | random 18 (RIDER+CHAR+EQ+DBL+REV) / voice -8 | -18.41 |
| random | random 18 (RIDER+CHAR+EQ+DBL+REV) / drums -6 | -18.85 |
| random | random 19 (CHAR+DBL+REV) / voice -8 | -5.31 |
| random | random 19 (CHAR+DBL+REV) / drums -6 | -8.24 |
| random | random 20 (EQ+DBL) / voice -8 | -15.65 |
| random | random 20 (EQ+DBL) / drums -6 | -29.32 |
| random | random 21 (RIDER+CHAR+EQ+DBL+REV) / voice -8 | -9.12 |
| random | random 21 (RIDER+CHAR+EQ+DBL+REV) / drums -6 | -11.74 |
| random | random 22 (CHAR+DBL+REV) / voice -8 | -6.49 |
| random | random 22 (CHAR+DBL+REV) / drums -6 | -11.89 |
| random | random 23 (RIDER+CHAR+EQ+DBL+REV) / voice -8 | -13.19 |
| random | random 23 (RIDER+CHAR+EQ+DBL+REV) / drums -6 | -17.30 |
| automation | input gain jumps +6/-6/0, gains only / music -10 | -109.12 |
| automation | output gain jumps -6/+9, gains only / drums -6 | -100.12 |
| automation | input gain ramp -12 to +12 in 41 steps, gains only / pink -18 | -123.77 |
| automation | eq high jumps +12/-12/0, eq only / music -10 | -63.09 |
| automation | eq low jumps -12/+12/0, eq only / pink -18 | -33.15 |
| automation | eq low up and high down in 41 steps, eq only / music -10 | -57.84 |
| automation | gain and eq moves, eq + reverb / voice -8 | -66.59 |
| automation | gain and eq moves, full chain: start-up / voice -8 | -13.06 |
