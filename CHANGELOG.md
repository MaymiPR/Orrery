# Changelog

User-facing changes per version, newest first. `## Unreleased` collects the next release; `scripts/bump_version.py`
renames it to `## x.y.z (date)`, and `scripts/release_notes.py` publishes that section as the release notes. Under
each version: `### Highlights` (prose, optional), then `### New`, `### Improved`, `### Fixed`, `### Known issues`,
each only when it has content, with bullets `- **Topic:** what, with the before and after numbers in dB`.

## Unreleased

### Improved

- **Keys in VST3 hosts:** the VST3 editors take the keys the host offers them, so a focused editor
  receives its keys in FL Studio; every key the editor does not use still goes to the host (the space bar, Ctrl+Z).
- **Keys after a click:** each editor hands the keyboard focus back to the host's window after a click, so the space
  bar and the host's other shortcuts keep working after a knob is touched (FL Studio).
- **Suite name:** the suite is called Orrery, its repository's name: the installers are
  `Orrery-<version>-<OS>` files and the About menus and Wraith's plate say Orrery. The plug-ins keep their codes,
  bundle IDs, parameter IDs, company name and install folders, so saved projects, presets and installs are unchanged.

## 1.2.1 (2026-11-04)

### Highlights

Wording update across the documents.

## 1.2.0 (2026-11-04)

### Highlights

A third plug-in joins the suite: **Wraith**, a recreation of Cradle's The Spirit, a vocal chain made with
producer Louis Bell. Its input and output gains, EQ, gain rider and reverb null against the original at -63 to
-143 dB; its Character section (compression and the Focus EQ) and its doubler are fitted models (NULLTESTS.md).

### New

- **Every editor in Orrery Suite's own look:** true black behind, violet-black panels and wells, lavender-white
  lettering, gold for values and meters, pearl for pointers and selections, the Orrery mark on every editor. The knobs
  are dark discs inside a gold value arc, the meters gold-to-pearl bars on the same scales; Positron's plate shows a
  small orrery, Scorpius's the constellation Scorpius, and Wraith's faceplate is drawn as cards. Layouts, controls,
  particle styles and sound are unchanged.
- **Positron, particles at slow tempos:** while the host plays, the light now holds between hits (it rises at once
  and fades over about 1.5 s), so at a low tempo the particles no longer flash in and out; the classic style also
  moves at a calmer pace for its tempo, its sparks glowing longer.
- **Wraith:** the original's 19 controls with their ranges and tapers, plus room / plate as a host parameter;
  its eleven factory presets at their exact values; zero latency, like the original. Its editor at 1044 x 406, with
  the lit displays, meters and the rider panel, resizable from 50 to 200 %, with our own lettering and mark.
- **Wraith, the suite's top bar:** A / B compare, a side-chain input (INT / EXT: the character section's
  detector) and I/O LINK, as on Positron and Scorpius (ours; the original has none of them).
- **Wraith, EQ:** the original's two shelves, exact at every sample rate (-127 to -138 dB).
- **Wraith, gain rider:** the original's law, floor and timing, exact (-63 to -123 dB).
- **Wraith, reverb:** the original's room and plate, measured from its output and run by convolution (room
  -73 to -92 dB; plate -95 dB at a typical mix, -52 dB fully wet); the high-cut filter and the mix law exact.

### Improved

- **Positron, the character section on dense material:** its mid band's compression and saturation now reach
  the treble the way the original's do (they fall away faster above about 2 kHz). Against the original, character
  only: pink noise at -18 dBFS -55.1 → -67.1 dB, at -6 dBFS -42.4 → -47.6 dB, the drum loop -63.8 → -68.4 dB, music at
  100 % -74.0 → -75.1 dB; with oversampling, pink noise at -18 dBFS -51 to -55 → -59 to -63 dB. The 163-case stress
  suite's median goes from -63.3 to -66.0 dB.
- **Positron, 200 % character:** the mid band refitted there: music -63.1 → -65.6 dB, and with the limiter,
  EQ and gains also moved -64.7 → -67.5 dB.
- **Positron, loud material:** the high band refitted around the new mid band at 100, 125 and 175 %: a mastered
  track with the default settings -44.3 → -46.5 dB (character only -46.1 → -49.3 dB), drums peaking at -1 dBFS
  -57.7 → -61.3 dB (at 44.1 kHz -43.8 → -54.3 dB), pink noise at -6 dBFS -41.1 → -47.9 dB.
- **Positron, the high band's release:** after a loud passage its compression lets go the way the original's does
  (its detector follows the signal's power, so small drops in level recover more slowly than deep ones), and the band
  is refitted around that at every amount. Against the original: the mastered track with the default settings
  -46.5 → -49.6 dB, character only -49.3 → -53.1 dB, at 200 % -39.2 → -43.0 dB; a sweep at -6 dBFS -46.9 → -57.0 dB
  (the same at 44.1, 88.2 and 96 kHz); drums peaking at -1 dBFS through the whole chain -61.3 → -65.2 dB (at 44.1 kHz
  -54.3 → -64.2 dB); pink noise at -10 dBFS, character only, 62.5 / 100 / 200 % -56.3 / -51.6 / -42.2 → -61.0 / -54.5 /
  -44.1 dB. Pink noise at -6 dBFS at 88.2 kHz loses 0.5 dB (-48.2 → -47.7 dB); the stress suite's median stays at
  -66.0 dB.
- **Positron, the external side-chain:** with EXT on, the side-chain is now heard through the same band split and
  delay as the input, as the original's is. Against the original, music at -10 dBFS with drums on the side-chain
  -61.7 → -68.1 dB, with a bass line and kick on it -39.5 → -59.3 dB, music at -2 dBFS -54.4 → -58.6 dB, at 200 %
  -57.9 → -63.4 dB; loud pink noise on the main input, character only, -54.4 → -52.3 dB.
- **Positron, meters:** the settings page's "Short-term LUFS & Peak" now works: the second readout of each I/O meter
  shows the short-term loudness of both channels (ITU-R BS.1770, 3 s), as the original's does (it showed RMS whatever
  the setting). The limiter meter now has the original's layout, a bar for the reduction now and a marker that holds
  the deepest, at its 1.5 dB steps; filmed side by side, the two match at every step tested.

- **Wraith, doubler:** its voices are band-limited and its lows pass the delay line, as the original's do (the
  voices were inverted before). Against the original at Mix 0.1: pink noise -18.2 → -31.0 dB, music -19.6 → -38.9 dB,
  drums -20.5 → -28.5 dB; fully wet: pink noise -3.0 → -18.1 dB, music -4.7 → -27.1 dB, drums -5.3 → -15.8 dB. Its
  level at full wet is now within 0.1 dB of the original's (was 2 to 6 dB under it). The factory presets that use it:
  -2.6 to -14.2 → -8.6 to -25.9 dB.
- **Wraith, Character on drums:** the expander now has its own slow detector, as the original's does, so it holds
  its gain between hits instead of closing: drums at Compression 0 / +50 / -50 -9.2 / -6.1 / -12.9 → -14.1 / -9.9 /
  -20.4 dB; the start-up preset on drums -11.3 → -15.1 dB (44.1 kHz -9.4 → -12.8 dB). The 97-case null suite's
  median goes from -19.8 to -21.6 dB.
- **Wraith, doubler modulation:** what looked like a pseudo-random wobble of the original's delay is its modulation
  running at about 0.503 Hz rather than 0.5 Hz (measured per sample rate: 0.5022 to 0.5035 Hz); ours now runs at
  the measured rate and phase. Fully wet pink noise -18.1 → -19.4 dB, at Mix 0.1 -31.0 → -32.3 dB; the sweep
  -10.9 → -11.3 dB; music and drums 0.1 dB better; the factory presets with the doubler on pink noise 1.2 to 1.3 dB
  better.
- **Wraith, Character at 44.1 and 96 kHz:** the top end of the Focus EQ is now fitted per sample rate, so the
  section follows the original at every rate, not only at 48 kHz. The start-up preset at 44.1 kHz: pink noise
  -18.0 → -20.5 dB, drums -12.8 → -13.5 dB, the sweep -16.2 → -16.8 dB; at 96 kHz pink noise -17.2 → -18.3 dB and
  drums -17.1 → -18.1 dB; at 48 kHz 0.1 to 0.5 dB better.
- **Wraith, Character on transients:** the compressor now runs past its steady reduction after a rise in level and
  comes back over a few hundred ms, and lets go slowly after a short burst and fast after a long one, as the
  original's does (it reached its steady value in 10 to 30 ms before). Drums at Compression 0 / +50 -14.2 / -10.0 →
  -19.0 / -14.4 dB; the start-up preset on drums -15.1 → -18.9 dB (44.1 kHz -13.5 → -17.9 dB) and on pink noise
  -21.7 → -26.2 dB; "hard squeeze" on drums / pink noise / music -1.7 / -19.1 / -18.7 → -4.0 / -22.1 / -21.3 dB. The
  null suite's median -21.8 → -23.2 dB. Five cases lose 0.5 to 3.0 dB (below); no measurable CPU cost.
- **Wraith, the order of the stages:** the reverb now comes before the doubler, as in the original (measured to
  -333 dB). The presets with both on, on pink noise: "big cave" -8.7 → -13.1 dB, "wide and wet" -9.0 → -12.1 dB,
  "wide lead" -16.7 → -21.0 dB, "backing stack" -15.4 → -18.6 dB (the null suite now also lines up its plate captures'
  start, part of these numbers); "wide and wet" on drums and music -14.5 / -13.2 → -12.6 / -11.8 dB, where the doubler's
  own error now reaches the reverb's tail.
- **Wraith, Character at 44.1, 88.2 and 96 kHz:** the Focus EQ, its all-passes among it, is now fitted at each of
  those rates, as the original's response differs from rate to rate. The start-up preset at 96 kHz: pink noise
  -18.4 → -23.8 dB, music -20.1 → -20.9 dB, drums -20.1 → -20.8 dB; at 44.1 kHz pink noise -24.6 → -27.1 dB, drums
  -19.7 → -20.1 dB. 48 kHz is unchanged; no case worse.
- **Wraith, Character's static curve:** the compressor now follows the original's measured curve, one curve of the
  driven level at every Compression setting, its slope easing in over about 12 dB under the kink and still rising
  above it. Music at Compression -50 / Focus +50 -18.2 → -28.6 dB, drums there -22.0 → -25.2 dB; the start-up
  preset on drums -18.9 → -21.0 dB (44.1 kHz -17.9 → -19.7 dB); the presets on pink noise and drums 0.4 to 1.5 dB
  better. The null suite's median -23.2 → -23.6 dB. The sweep at the start-up settings loses 0.3 to 0.4 dB (below).
- **Scorpius, the drive (colour a, the default):** a new learned model, a three-layer recurrent network that
  follows the original's drive more closely, with the hi-pass a fixed filter after it as in the original; it uses
  no more CPU than the original's. The default preset: drums -26.6 → -29.7 dB, drums 12 dB lower -34.6 → -36.6 dB, the
  track -22.4 → -25.8 dB, the track 10 dB lower -31.2 → -33.9 dB. The drive alone, hi-pass off: drums -23.4 → -28.8
  dB, the track -20.7 → -25.9 dB.
- **Scorpius, drive colour b:** the same kind of model, with either hi-pass setting. The drive alone, hi-pass on:
  drums -28.3 → -30.6 dB, drums 12 dB lower -36.6 → -39.9 dB, the track -22.7 → -25.8 dB, the track 10 dB lower
  -34.1 → -37.3 dB. Hi-pass off: drums -28.7 → -30.5 dB, drums 12 dB lower -39.2 → -40.3 dB, the track -23.0 →
  -25.7 dB, the track 10 dB lower -34.9 → -37.3 dB.
- **Scorpius, very quiet material:** the low-level expander now listens where the original's does, at the end of the
  drive, harmonics, compression and lift group and to the mid, and it holds and releases as the original's does;
  created with lift on, it starts open, as the original's does. A quiet tone or quiet noise now gets the original's
  gain within 0.1 dB with the drive on (was up to 2.6 and 8.5 dB off) and at every compression, lift and harmonics
  amount (was up to 9 dB too low). Lift, drive colour c, harmonics and grit no longer leave a faint DC offset on silence
  ("grit only" on quiet material: -45 to -58 → -62 to -65 dB). On the track, drums and pink noise 60 to 78 dB down the
  default preset nulls at -25 to -34 dB and the drive alone at -19 to -33 dB (the build before these changes: 0 to
  -27 and -1 to -12 dB).
  Switching a module on while audio plays, around the switch: the drive -27.6 → -30.5 dB, compression -41.9 →
  -59.3 dB, lift -40.9 → -53.2 dB, harmonics -40.0 → -69.0 dB.

### Known issues

- **Wraith, Character:** a fitted model of the original's expander, drive and compressor: -16 to -29 dB on
  steady and program material, -15 to -25 dB on drums. Its release on noise is not yet the original's, which leaves
  some cases 0.3 dB or so off in level: with the overshoot above, pink noise at Compression -50 / Focus +50 -28.3 →
  -25.5 dB, Compression +50 / Focus -30 on music -21.0 → -20.8 dB and on the sweep -21.0 → -20.5 dB, and "short
  phase" and "wide image" on pink noise -12.0 / -12.5 → -11.5 / -12.0 dB. With the static curve above, the sweep at
  the start-up settings -17.5 → -17.1 dB (the full chain -17.1 → -16.8 dB, at 44.1 kHz -17.3 → -16.9 dB). The "hard
  squeeze" preset on drums (the rider into full compression) is still a poor null (-4.4 dB).
- **Wraith, doubler:** fully wet it nulls at -11 to -27 dB: its delay follows the original's, but the filtering of
  its two voices does not yet (both voices differ from ours by the same response, steeper at both ends). It also
  limits "wide and wet" and "big cave" on drums and music (-11.8 to -14.8 dB).
- **Positron:** the limiter under continuous heavy limiting (pink noise 5 dB into it, -54.8 dB) is at the original's
  own limit: noise at -80 dBFS on its input moves its output by -57.5 dB.

## 1.1.1 (2026-10-31)

### Highlights

In both plug-ins: **much lighter on the CPU, with the same sound.** Scorpius takes about a third of the processor
time it did (its default settings: ~21 % of one core → ~7 % on a Ryzen 9800X3D), Positron about a third too
(~9.5 % → ~3 %): the learned models' arithmetic uses AVX2 and AVX-512 where the processor has them, and the filters
and the limiter work through blocks of samples instead of one at a time. The output differs from before by less than
-130 dB.

### New

- **Scorpius, a new "Scorpius" particle style** (ours, the default): two scorpions drawn in glowing green lines, back
  to back in the middle of the stripe. They shed green motes that stream out into black holes past the ends, as the
  Orion style's particles do; their tails strike on every kick and 808, back to back too (snares and hats leave them
  still). With no sound they stay faintly lit. It replaces the venom style. In both styles the streams now pinch into
  a line close to the ends.

### Improved

- **Scorpius, switching a module on now sounds like the original's:** the drive, harmonics, compression and lift
  start from silence, as Orion's do (ours started from a state the models never saw in training, and the lift
  carried on from where it stopped). Around the switch, against the original: drive -8 → -28 dB, the others -24 to
  -30 → -40 to -42 dB, at every host block size.
- **Scorpius, the low-level expander** in front of those modules opens over about 5 ms, as the original's does,
  instead of at once, and never closes beyond -44.5 dB (it used to keep falling on very quiet input).

### Fixed

- **Scorpius, the stripe's light no longer flickers with sparse, decaying loops** (FL Studio's DL Clubbed at 60 BPM,
  say): a moment of silence between hits used to drop it; it now stays lit through them and fades after the music
  stops, as the original's does.

## 1.1.0 (2026-10-28)

### Highlights

**Scorpius**, the suite's second plug-in: a recreation of Cradle's Orion (v1.2.1), the drum-bus processor, null-tested
against the original. VST3, CLAP and a standalone app on Windows; VST3 and CLAP on Linux; AU, VST3 and CLAP on macOS.

### New

- **Scorpius, signal chain:** input gain, drive (colours a / b / c, optional hi-pass), harmonics (50 or 80 Hz),
  compression (modes a / b, with a gain-reduction readout), lift and a five-band harmonic EQ, then the sub, low, loud
  and grit parallels mixed in, and output gain. The original's nine factory presets; your own save as `.scorpius`
  files.
- **Scorpius, editor:** the original's layout, meters, knobs, faders and particle stripe, measured from it, with A / B
  compare. Ours on top: an external side-chain (INT / EXT) for the compressor, I/O LINK, and a "Scorpius" particle
  style (the default) next to the original's.
- **Positron, A / B compare** (ours, as Cradle's Orion has it): two complete settings in one instance, switched
  from the top bar; the arrow copies the active one over the other.
- **Both, double-click a knob to type a value.** The suite's top bars match: A / B left of the preset menu, then the
  side-chain switch and I/O LINK.

### Improved

- **Positron, oversampling at every sample rate:** its filters are now designed for the session's rate, as the
  original's are. At 44.1 kHz with 2x or 4x it used to differ clearly from the original (-14 dB on drums); now -61 dB.
  96 kHz improves the same way (-19 → -57 dB), and 4x / 8x at 48 kHz a little (-53 → -59 dB).
- **Positron, particles:** the classic style now glows like neon around a black hole in the centre, the
  glass is clearer and reflects the sparks in its rims, and both styles move with the project's tempo.
- **Positron, fine adjustment** of the knobs is Shift only, as on The God Particle (Ctrl now drags at the
  normal speed).

### Known issues

- **Scorpius, how close:** the EQ, sub and rate converters are the original's own filters (-50 to -70 dB); everything
  but the drive nulls at -45 to -51 dB together; the default preset at about -22 to -27 dB on loud material, limited
  by the drive. Parameter changes and power switches follow the original's timing. See plugins/Scorpius/NULLTESTS.md.

## 1.0.1 (2026-10-25)

### Improved

- **Positron, the I/O readouts read like The God Particle's,** measured frame by frame from films of the
  original:
  - **RMS readout:** live instead of held. It updates about four times a second and shows the RMS + 1.5 dB, as the
    original does. It falls back to -inf when the audio stops, on the input and the output.
  - **Peak readout:** held until clicked, as before, but it now samples the level about every 46 ms as the original
    does. Very short spikes read lower than the sample peak, as they do on the original.
  - Below -96 dB a readout shows -inf.

### Fixed

- **Positron, About no longer crashes the host.** Choosing "About Positron" from the logo's menu could
  crash the DAW; the menu now closes safely before the panel opens. The About panel is also larger, so its text has
  room.

## 1.0.0 (2026-10-25)

### Highlights

The first release of Orrery Suite, with its first plug-in, **Positron**: a recreation of Cradle's The God
Particle (v1.2.4), its controls, look and sound, null-tested against the original. VST3, CLAP and a standalone app on
Windows; VST3 and CLAP on Linux; AU, VST3 and CLAP on macOS (universal).

### New

- **Signal chain:** input gain, a three-band EQ, the character section (a 3-band FIR split with a parallel compressor
  and a sine shaper per band, amount 0 to 200 %), a look-ahead limiter at -0.1 dBFS, output gain. Oversampling 1 / 2 /
  4 / 8x and an external side-chain (INT / EXT) for the character section's detectors.
- **Editor:** the original's layout, knobs, glass visualiser and meters, measured from it: the value readout on a
  knob, Shift or Ctrl for fine adjustment, the I/O meters' colours and the gain-reduction LEDs, and particles that
  follow the input level. Zoom 50 to 200 %, from the menu or by dragging the bottom-right corner.
- **Additions of ours:** an I/O LINK switch (the output follows the input gain inverted, so level changes cancel) and
  a "Positron" particle style on the settings page.
- **Presets:** the original's default as a factory preset, and user presets saved as .positron files in
  Documents/Positron/Presets.

### Known issues

- **How close:** on a mastered future-house track at the default settings the difference to the original is about
  -44 dB, with the limiter alone -61 dB; on synthetic music -62 to -74 dB. The stress suite (163 cases over settings,
  levels, rates, block sizes and automation) has a median of -63 dB. See plugins/Positron/NULLTESTS.md.
