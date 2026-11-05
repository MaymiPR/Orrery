- **Exact:** with every stage off the output is the input (-329 to -341 dB). The input and output gains (-144 dB),
  the EQ's two shelves (-128 to -138 dB) and the gain rider (-63 to -123 dB; the -63 is a fast rider on pink noise, the
  rest -96 dB and better) are the original's own laws, and the reverb's room is its measured response (-73 dB fully
  wet, where the 16-bit storage of the response sets the floor, to -92 dB at its start-up mix). The plate, which the
  original only plays with its editor open, nulls at -95 dB at a typical mix and -52 dB fully wet (null_plate.py).
- **A model:** the character section is a fitted model of the original's expander, drive and compressor: -16 to
  -29 dB on noise, sweeps and music, -15 to -25 dB on drums. Its expander has its own slow-release detector, measured
  on the original's gain (MEASUREMENTS.md 4.3): it holds its gain through the gaps between drum hits, as the original
  does. Its compressor overshoots a rise in level as the original's does, by about 0.3 of its reduction, and lets go
  slowly after a short burst and fast after a long one (MEASUREMENTS.md 4.4): with the overshoot, drums at the
  start-up settings null at -19.0 dB (-14.2 dB without it) and pink noise at -26.5 dB (-21.8 dB without it). Its
  static curve is a table of the original's, one curve of the driven level at every Compression setting
  (MEASUREMENTS.md 4.1): with the table, music at Compression -50 / Focus +50 nulls at -28.6 dB (-18.2 dB with a
  single curve) and drums at the start-up settings at -20.8 dB (-19.0 dB with a single curve).
  What the two cost: five cases are 0.5 to 3.0 dB worse with the overshoot than without it (Compression -50 / Focus
  +50 on pink noise -25.5 dB against -28.3 dB, Compression +50 / Focus -30 on music -20.8 dB against -21.0 dB and on
  the sweep -20.5 dB against -21.0 dB, "short phase" and "wide image" on pink noise about 0.5 dB each), each a level
  offset of 0.3 dB or so from the refitted release times; the table costs the sweep at the start-up settings 0.3 to
  0.4 dB (Character -17.1 dB against -17.5 dB, the full chain -16.8 dB against -17.1 dB, at 44.1 kHz -16.9 dB
  against -17.3 dB). Being first in the chain, the section sets the null of everything after it: the start-up preset
  lands at -24 dB on music and -21 dB on drums.
- **The doubler, a model:** its two voices, their modulation and its stereo matrix are the original's; the
  modulation runs at the original's measured rate (about 0.503 Hz, per sample rate: MEASUREMENTS.md 7.1), not as a
  pseudo-random wobble of its delay. The voices are band-limited (a high-pass near 500 Hz, low-passes above 6 kHz)
  and the lows pass the delay line undelayed, as measured. It nulls at -25 to -39 dB at Mix 0.1 and -11 to -27 dB
  fully wet; at full wet what is left is in the voices themselves, not their delay (worst on the sweep and on drums
  at Stereo 1). By what it does, at full wet (doubler_metric.py):

{doubler_metric}

- **Presets** follow from their stages: the ones with the doubler land at -10 to -26 dB, the ones without it where the
  character section does (-21 to -27 dB), except the one with the rider at 0.97 into full compression on drums
  (-4.4 dB), where the two together do not null.
- **Our VST3 equals our renderer:** `nulltest.py --vst3` gives the same numbers to the printed digit, and
  `first_null.py` finds the two equal at -333 dB at the start-up preset.
