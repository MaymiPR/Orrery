# Scorpius: research

What the original does and how its controls and editor are measured. Scorpius is an open-source recreation of
Cradle's **Orion**, a drum-bus processor made with mix engineer Jaycen Joshua. Its audio behaviour is in
[MEASUREMENTS.md](MEASUREMENTS.md).

Local sources are an installed copy of the original. Nothing from it (images, scripts, fonts, presets, renders,
screenshots) is in this repository: those files stay in the git-ignored `reference/scorpius/` folder. Behaviour is found
by measuring the plug-in from the outside.

## Sources

| Id | Source | What it gives |
|---|---|---|
| **W1** | Official product page: [cradle.app/products/orion](https://cradle.app/products/orion) | positioning, formats, system requirements, price |
| **W2** | Support article [GUI Overview](https://support.cradle.app/hc/en-us/articles/30831917426708-GUI-Overview) | every section described |
| **W3** | [How do I use Orion?](https://support.cradle.app/hc/en-us/articles/30831954160404-How-do-I-use-Orion) | intended use, meaning of the input target |
| **W4** | [What is Orion?](https://support.cradle.app/hc/en-us/articles/30831901369876-What-is-Orion) | positioning, relation to The God Particle |
| **W5** | [KVR product page](https://www.kvraudio.com/product/orion-by-cradle) (secondary) | listing, reviews |
| **L1** | The installed plug-in (VST3) and the version information it carries | version 1.2.1, VST 3.7.8 SDK, category Fx; built in January 2025 |
| **L2** | `tools/ParamDump` run on L1 (`reference/scorpius/params_{48k,41pt,44k,96k}.txt`) | every host parameter: names, ranges, defaults, display text; buses, latency, editor size |
| **L3** | The plug-in's default saved state, from L2 (read with `scripts/nulltest/ref_state_lib.py`) | the preset structure, including settings the host cannot see |
| **L5** | Screenshots of the editor at 100 % and 200 % (`tools/RefCapture`, 50 Hz tone bursts; `reference/scorpius/editor_*.png`), menus and settings page (`ui_*.png`), every factory preset (`preset_*.png`, `presets_dump.txt`); RefCapture films at 200 % | the 1.2.1 layout, 888 × 403 px; every preset's settings; the animations |
| **L7** | The maker's installer | 1.2.2 is current; 1.2.1 measured (VST3 and AAX installed) |

## Product facts (W1, W2, W3, W4, W5)

- Cradle, $119 (a bundle with The God Particle). Formats: macOS AU / VST3 / AAX, Windows VST3 / AAX (no CLAP, no
  Linux). Licensing through Cradle Hub.
- A drum-bus processor made with the co-designer (W4); the defaults are how he starts his drum mixes (W1). Made to
  complement The God Particle (W1), on the same principles and with the same kind of interface (W4).
- Use (W3): set the input so the loudest section of the drums lights the green input target; the input level drives
  how much compression, saturation and character every module produces.
- Reviews note heavy CPU use (W5); measured in MEASUREMENTS.md 13.

## Controls (W2, with L2 for the numbers, L3 / L5 for the hidden ones)

Signal order, from the panel layout and W2, confirmed by measurement (MEASUREMENTS.md 1):
**input gain → drive (+ hi-pass) → harmonics → compression → lift → harmonic EQ → parallels (sub, low, loud, grit,
mixed in) → output gain**.

| Control (UI) | Host parameter (L2) | Range / display (L2) | Default (preset "default") | Documented behaviour (W2 unless noted) |
|---|---|---|---|---|
| **input** knob (plate, left) | `Input Gain` | -12 … +12 dB, linear (2.4 dB per 0.1) | 0 dB | level into the plug-in; meter with peak readout (red over 0 dBFS) and RMS readout, both reset by clicking; a green target bracket at the intended level |
| drive power | `Drive On/Off` | 2 steps | on | |
| drive **hi pass** | `Drive Hi-Pass` | 2 steps | on | a high-pass filter after the drive; the drive icon shows stars when on, "+" marks when off (L5) |
| drive **color a / b / c** | none (in the saved state, L3) | a / b / c | a | three colours, each with its own character |
| harmonics power | `Harm On/Off` | 2 steps | on | |
| harmonics **freq 50Hz / 80Hz** | `Harm Freq` | 2 steps: 50 / 80 | 80 Hz | excitement and energy for the kick drum and other low-frequency content, focused at 50 or 80 Hz |
| **harmonics** knob | `Harm Amount` | 0 … 1 (the UI shows %, e.g. 80.0 %) | 0.8 | amount; a deforming circle above the knob follows the processing (L5) |
| compression power | `Comp On/Off` | 2 steps | on | |
| compression **mode a / b** | none (in the saved state, L3) | a / b | b | two modes |
| **compression** knob | `Comp Amount` | 0 … 1 | 0.9 | a mix control for more or less compression; the co-designer aims for -1 … -2 dB of gain reduction; a numeric GR readout above it (L5) |
| lift power | `Lift On/Off` | 2 steps | on | |
| **lift** knob | `Lift Amount` | 0 … 1 | 0.8 | saturation and harmonic excitement across the spectrum, with extra focus on the high frequencies (presence, transient detail); a small deforming circle above it (L5) |
| harmonic EQ power | `EQ On/Off` | 2 steps | off | |
| **40Hz, 100Hz, 1kHz, 3kHz, 10kHz** knobs | `EQ 40Hz` … `EQ 10kHz` | 0 … +6 dB, linear (boost only) | 0 dB | five fixed bands that boost and shape harmonic content, where 1 dB steps matter; when on, a display above the knobs (L5) |
| **sub, low, loud, grit** faders, each with a power button | `Par Sub On/Off` / `Par Sub Level`, … `Par Grit …` | on/off; level 0 … 1 | all off, level 0 | parallel paths: **sub** more impact in the sub range; **low** weight in the low end (boom on kicks, warmth on bass); **loud** more perceived loudness and presence without raising the output; **grit** accentuates transients |
| **output** knob (plate, right) | `Output Gain` | -12 … +12 dB, linear | 0 dB | final level; meter as the input's |
| preset menu, ← →, disk icon | none | factory / user list (L5) | default | the same menu as The God Particle's |
| **Compare A → B** (top bar) | none (in the saved state, L3) | A / B; → copies A to B | A | two complete settings in one instance |
| UI Scale menu | none (in the saved state, L3) | 50 / 75 / 85 / 100 / 125 / 150 / 200 % (L5) | 100 % | window zoom |
| settings (gear) | none (in the saved state, L3) | particle animation ON / OFF (L5) | on | the only setting: no oversampling or LUFS options |
| none | `Bypass` | Off / On | Off | the host bypass |

The host-reported defaults of the on/off switches (L2: all 1, EQ 40 Hz … 0) are the parameters' own defaults; the
plug-in opens with the factory preset "default" (L3), whose values are the Default column.

### Factory presets (L5)

Nine presets, named here by our own names (their values are the original's). Settings that differ from "default"
(drive a, hi-pass on, harmonics 80 Hz 0.8, compression mode b 0.9, lift 0.8, EQ off, parallels off):

| Preset | Differences |
|---|---|
| colour c | drive color **c**, compression mode **a** |
| colour c easy | drive color **c**, compression mode **a**, lift **0.5** |
| no compression | compression **off** |
| hot and lifted | input **+9.12 dB**, compression mode **a** **0.76**, lift **0.7**, grit **on 0.189** |
| loud path | harmonics **50 Hz**, lift **1.0**, loud **on 0.731** |
| deep low end | hi-pass **off**, harmonics **50 Hz**, EQ **on, 40 Hz +6 dB** |
| all parallel | harmonics **1.0**, compression **1.0**, lift **1.0** |
| default | (the defaults) |
| grit only | drive, harmonics, compression and lift **off** (amounts 1.0), grit **on 0.731** |

### Host-level facts (L1, L2, L3)

- One effect class, vendor Cradle.
- Buses: stereo in, stereo out, no side-chain (Scorpius adds one: "Scorpius's own editor" below). Mono to mono is
  not supported.
- Latency: 0 samples at 48 kHz, 31 at 44.1 kHz, 48 at 96 kHz (L2): the DSP runs at a fixed 48 kHz and converts other
  rates (MEASUREMENTS.md 2).
- No VST programs; the state is about 3.1 kB. Tail 0.
- Editor: 888 × 403 px at 100 % (a wider plate than The God Particle's 888 × 359), not resizable by dragging.
- In the saved state harmonics, compression and lift form one group, separate from the drive, the EQ and the
  parallels; input and output gain are part of the preset ("hot and lifted" sets the input to +9.12 dB), unlike The
  God Particle's.

## Editor (W2, L5)

Layout at 100 % (888 × 403), version 1.2.1:

- **Top bar** (black): the maker's logo, `Preset` label and drop-down, ← / → arrows, disk (save) icon, a `Compare`
  label and an `A (→) B` segmented toggle (where The God Particle has its side-chain toggle), `UI Scale` drop-down,
  settings gear.
- **Main panel** (black, light-grey rounded outline), columns separated by thin vertical lines:
  1. input meter: peak and RMS readouts L/R, a green target bracket, two LED bar meters (as The God Particle's);
  2. **drive**: mint power button, an animated cluster of stars ("+" marks with the hi-pass off), a `hi pass`
     toggle, a `color` a / b / c selector;
  3. **harmonics, compression, lift**: three power buttons; above the harmonics knob a circle that deforms with the
     signal, above compression a large numeric GR readout (`-3.6`), above lift a small deforming circle; `freq`
     50Hz / 80Hz and `mode` a / b selectors; three medium knobs;
  4. **harmonic eq**: an outlined power button (off by default), five small knobs (100Hz, 3kHz on top; 40Hz, 1kHz,
     10kHz below); a display appears when it is on;
  5. **parallels**: four power buttons over four vertical faders with a metal cap (`sub`, `low`, `loud`, `grit`);
  6. output meter.
- A **visualiser stripe** across the full width under the columns (38 px tall): coloured particles and white streaks
  while audio plays, dark when idle.
- **Bottom plate** (warm grey): `input` and `output` knobs at the ends, labels `drive`, `harmonic eq`, `parallels`, a
  grille of dots with the product name in spaced letters under it.
- Fonts: the same as The God Particle's (a commercial sans, not shippable, and Source Code Pro).

### Layout (200 % captures)

The editor was measured on 200 % captures (the saved state's UI scale set to 200 % with `nulltest/refstate_lib.py`) with
`tools/measure_ui.py` (filled boxes, outlines, silver regions and their centres) and `tools/measure_ui.py --text` (every
word's box), and compared region by region with Scorpius's snapshots (`tools/compare_ui.py`, `ScorpiusSnapshot`).

| Element | Measured |
|---|---|
| Top bar and window | The God Particle's top bar, with `Compare` and its A / B switch where that one has `Sidechain` (Compare at x 604 … 734); the window 888 × 403.5 design px (403 at 100 %) |
| Columns | divide at x 86, 175, 424, 608, 801 |
| Power buttons, selectors, labels | buttons 72 × 23.5 (the parallels' 38 wide) at y 41.5; selectors are rows of 22.5 px stacked 0.5 apart, each outlined on its own; labels on baseline 263.5 (upper EQ row 192.5, freq / mode 194), mint whether their section runs or not |
| Knobs | the six column knobs one size (r ≈ 20.1), the plate knobs The God Particle's (r 25.06); centres from their silver regions, corrected as on The God Particle's knobs (known exactly), checked against the snapshot to 0.1 px |
| I/O meters | as The God Particle's, lower: LEDs on a 4 px pitch from y 258, readouts at x 30.5 / 60.5 (output 827.5 / 857.5); the input target narrower (lines x 36 … 54) and higher (y 100.5 … 120) |
| Compression readout | a reduction shows as "- 3.6" (a gap after the minus), rest as "0.0"; the sparks, the two circles and the readout are not drawn while their module is off |
| Faders | the cap one image (the four identical), 36.9 × 22.9, drawn 0.12 px left of the track, travelling from y 237.5 (level 0) to 85.5 (level 1); the track mint below the cap while the path is on; level taper (e^(2.188 L) - 1) / (e^2.188 - 1) (MEASUREMENTS.md 5) |
| Fader cap | (`tools/fit_fadercap.py`, a measuring tool: it prints tokens and writes no source) a rounded rectangle 36.9 × 22.9, corner radius ~2, with a thin rim lit from the upper right, a spun-metal face whose grey depends only on the angle round its centre (period 180°: darkest ~92 a little right of up, brightest ~207 a little below the right), a darker ring round the groove, and the groove (grey 45, its edge 58) 32.2 × 2.0 across the middle |
| Plate grille | 19 staggered rows (21 / 20 dots), a halftone of an arch: the dot area follows 0.043 + 0.932 exp(-((d - 239.3) / 26.3)²) of the largest, d the distance from (300, 587.8), fitted to every dot |
| Settings | one row, particle animation ON / OFF, in a 420 × 254 box |

### Animations and displays (RefCapture films at 200 %)

`tools/RefCapture` films with `drag=x,y,0,0,burst,<ms>` (click, then grab the editor as fast as it can, ~70 frames/s,
each frame named with its time since the click) and `rows=<from>,<to>` (only a band of rows); the same scripts run on
the original and on Scorpius.

| Element | Measured |
|---|---|
| Drive marks | each of the five marks keeps its identity and size through a, b and c (a → b → c → a brings every mark home); a new colour moves each in a straight line to its new place, easing in and out (cubic) over 215 ms, their paths crossing; the hi-pass cross-fades the two shapes over ~110 ms (the old one fading out under the new); the drive's power button fades the marks over ~85 ms |
| Module displays | the circles, the GR readout, the EQ display and the marks fade linearly over ~85 ms with their power buttons, also when a preset or a compare slot switches them; knobs, faders and selectors jump |
| Copy message | Compare's arrow (only it) shows "A copied to B." (or "B copied to A.") in a box 200 × 60.5 at (344, 337) over the plate: fill #050607, a 1 px edge #252523, the text as the labels (12 px, baseline 34.25 below the box's top); there at once, holding 0.55 s, then fading out linearly over 1.05 s |
| Mouse | Shift = JUCE's velocity mode (cursor hidden, fine moves), Ctrl = normal speed, Alt-click = default value, on knobs and faders alike |
| Harmonic EQ display | not a response curve: each band its own shape (filled with mint at 18 %, outlined at 37 %; overlaps add up), heights linear in dB (51 … 53 px at 6 dB) over a baseline at y 124.75; the bands evenly spaced across the section: 100 Hz, 1 kHz, 3 kHz are bells exp(-(\|x - c\| / 15.64)^2.47) at x 478.98, 515.48, 551.49; 40 Hz and 10 kHz are shoulders 1 / (1 + e^(±(x - c) / 6.4)) past x 457.97 and 575.05, drawn over x 432.25 … 600.75 (each band alone at 3 and 6 dB, fitted to its outline) |
| Circles | at rest radius 6.43; they follow a band's level: harmonics the lows (flat to 80 Hz, -7 dB at 100 Hz, nothing by 150 Hz), lift the mids (-24 dB at 300 Hz, -15 at 500, most at 1 … 2 kHz, -15 at 3 kHz, -31 at 6 … 8 kHz), measured with a sweep of sines at -12 dBFS; neither the amounts nor the 50 / 80 Hz switch nor anything but the input gain changes them. The level is a sum of spectrum magnitudes (a 4096-point FFT: pink noise at -15 dBFS RMS reads 0.52 in the mids and 0.27 in the lows, where a sine of the same RMS reads its amplitude), so noise and music grow them more than a tone. A new reading about every 85 ms (a 4096-sample spectrum every 4096 samples). Radius, fitted to music films keeping the tone points (9.6 at -50 dBFS, 10.7 at -40, 18 at -10; above -52 dBFS): harmonics 8.29 + 15.80 (a^0.312 - 0.083), up 0.05 s, down 0.3 s at most 24 px/s; lift 3.76 + 19.07 (a^0.168 - 0.083), up 0.22 s, down 0.4 s. Outlines wobble by about 1 px rms in lobes 2 … 12 (most in 2 … 4), morphing in place without turning, and move only as the level changes (a steady tone freezes them) |
| Compression readout | moves towards the gain reduction while there is some (a 1 kHz tone: -1.5 at -10 dBFS, -1.3 at -12, reached in ~0.4 s) and keeps its value while there is little or none, through silence too. Law (20 s of a demo track and a 23 s tone probe: 1 kHz steps of -10, -4, -14, -2, -8 dBFS, then -4 / -14 alternating every 0.25 s, a 1 Hz swing between -14 and -2, a pause, -6; every frame's string read): it holds the highest value of a smoothed gain reduction (times the amount), and every 1.5 s of compression takes the smoothed value again (dropping, then climbing back over 0.2 … 0.4 s); smoothing up 0.25 s, down 0.2 s; the clock runs while the smoothed reduction is over 0.3 dB; about 4.4 changes a second on music; the number centred with the "-" hanging to its left |
| Frame rate | no frame repeats in a 36 fps film: about 37 frames a second |
| Editor CPU | playing at 200 %: 1.36 of a core |

### The stripe (RefCapture films at 200 %)

**Idle.** A divider at y 272.5 … 273.5 (the column dividers run down to it); a capsule outline (grey ~12) x 11.75 …
874.5, y 283.75 … 298.25, radius ~4; a flat grey-27 floor y 290.75 … 297 along its lower half, a little green towards
the right; a short cyan-grey glint (54, 66, 69) inside the left end at y 285.25; a soft highlight (~150) inside the
right end; under it the panel's inner edge as a dim band (~36) at y 303 … 305.5.

**Light** (`tools/fit_stripe.py`; tone steps from -65 to -30 dBFS with stops, pulses fading from -10 to -60 and rising
back, a tone ramp down, a demo track's drop, the same 30 dB quieter and its fade-out, a sparse drum loop at 60 BPM whose
kicks decay below -90 dBFS for ~40 ms before the next hit four times a loop, played twice between 1 s and 3 s of
silence):

| Quantity | Value |
|---|---|
| Brightness | ((dB + 72) / 32)^1.25 of the level the light follows: dark below -72 dBFS, full from -40 (tones: 0.16, 0.29, 0.44, 0.61, 0.81, 1.0 from -65 to -40 dBFS), eased over ~30 ms on screen |
| Jumps | the level is taken when the input jumps, judged per 10 ms of audio: more than 4.5 dB against any chunk of the last 120 ms; smooth changes leave it where it was (a ramp up from -60 dBFS stays dim even after it levels off at -20 for 2 s, then lights fully once it stops; a ramp down from -10 stays full; a steady tone keeps its brightness for as long as it lasts, 6 s tested); music, whose peaks come and go, is followed down (a track's fade-out dims to 0.6 at -47 dBFS peaks) |
| Stops | at a stop the level only rises to the loudest chunk of the last 0.15 s, never drops to it, and otherwise carries on falling from where it was at 50 dB/s (nearer 40 dB/s at the very bottom): after a -10 dBFS tone stops the light stays full 0.6 s and fades over ~0.55 s; after -40 it fades at once; through the sparse loop it stays lit (never below 0.87 of full) and after the loop ends holds ~0.2 s and fades over ~0.6 s |
| Animation off | the stripe stays dark |
| Fit | the light per frame against all four films: rms error 0.039 (music 0.034) |

**Particles** (the 20th percentile of the lit frames for the glow; local maxima per frame for the particles; tracks
linked frame to frame; 20 s of a demo track, rows 0.66 … 0.775 of the editor, for motion and colour):

| Quantity | Value |
|---|---|
| Glow | separable: a profile down the stripe (brightest at y 289, ~0.25 of that above the band, ~0.4 below it, a line on the lower rim at y 306) times a bell along it (centre x ≈ 452, Gaussian width ≈ 227 plus a sharp core) |
| Count and place | ~1600 local maxima per frame, spread almost evenly along x 55 … 815 and across y 272.5 … 306 (dense in 286 … 302); the ends carry ~60 particles per frame each |
| Lanes | dashes in the band keep to three one-pixel lanes (y 289.1, 291.6, 294.25, a weaker one at 302.5); isolated dots are ~1 × 1 px cores with a faint halo |
| Per frame | with the music's own swings taken out (each frame less a Gaussian smooth of it), particles correlate 0.01 from one frame to the next and outlast chance not at all: they are scattered anew every frame (frame-to-frame correlation of the raw particle layer 0.36 at 26 ms, 0.23 at 53 ms) |
| Motion | above the band particles stream outwards from the middle as if coming at the viewer: sideways at sign × (30 + 0.38 × the distance from x 444) px/s (-159 px/s at the left end, +168 at the right), rising 18 … 36 px/s; in the band most twinkle in place (median speed 0), a fifth stream outwards; below it they barely move |
| Flares | rounded, 2 … 3.5 wide, up to ~14 tall, swelling and shrinking within ~0.15 s; ~2.9 tall ones at any time (median height 23 film px, the tallest tenth 42), barely sliding; ~4.8 a frame in all, each showing for 1.7 frames on average (three in four for one frame only) |
| Colours | about half nearly white (mostly white where they overlap in the middle), the rest amber, cyan, blue-violet, red-orange, azure, pink-red in that order of frequency; along the stripe amber the commonest (13 … 22 %), then cyan (9 … 16 %) and red-orange. Saturated hues in 30-degree bins (red-orange, amber, yellow / cyan, azure, blue-violet, violet, pink): .18 .19 .02 / .15 .13 .16 .03 .03 .09; saturated share of the bright pixels .38 |
| Brightness by row (20th / 95th percentiles) | above the band a faint violet haze and particles; below it denser; on the rim the 99th percentile of the rows 66 … 116 |
| Fixed reflections | (the 10th percentile of the lit frames less the idle frame) two dotted lines at y 282.25 and 304, a dot every 3.5 px, made of segments whose bright ends fall at the same x on both (234, 314, 394, 465.5, 529.5, 593.5, 652.5, 698, 744, 790: closer together to the right); bright bumps at both ends of the lower one; three short violet lines across each end cap; the band reflected in the lower rim (y ~306) |

## Scorpius's own editor

The editor keeps the measured positions, sizes, hit areas and behaviours; what is drawn on them is the suite's own
(`shared/ui/Theme.h`): a black panel framed in the palette's lines, violet-black wells and raised boxes,
lavender-white labels, the sun's gold for values, meters, readouts and selections, pearl for the pointers and the
drive's marks. The plate is a theme card showing our own decoration where the original has its grille (the
constellation Scorpius as it lies along the horizon, two faint orbits, a few seeded stars), the spaced name
"S C O R P I U S" (eight letters where the original spaces five) and the suite's mark. The fader caps are the suite's
cap (`theme::drawCap`) at the measured cap's size and place, in slots with a faint scale; the I/O LED ladders are meter
bars in the same columns on the same scale (LED k's threshold -58.5 + 1.5 k dB is k + 1 fortieths up the bar) with the
same ballistics and peak hold; the input and output knobs' arcs run from 0 dB.

| Part | Scorpius |
|---|---|
| Host parameters | the drive colour and the compression mode are host parameters (`Drive Color`, `Comp Mode`) |
| Window | resizable from its corner |
| Top bar | the same as Positron's pixel for pixel (only the preset's name differs): Compare's A / B switch left of `Preset` (no label), a `Sidechain` INT / EXT switch where The God Particle has it, I/O LINK between it and `UI Scale` |
| Side-chain | a stereo side-chain bus (off unless the host enables it); EXT feeds the compressor's detector from it instead of the signal it compresses; with the bus off EXT hears silence; the switch is saved with the host's project and is not part of a preset or a compare setting |
| Knob entry | a double-click opens a field over the knob to type its value (Enter or a click elsewhere sets it, as one host gesture; Escape leaves it); Alt-click resets to the default |
| Compression readout | the original's law run inside the compressor (`dsp/Compressor.h`) on its own gain reduction: 4.3 changes a second on music, within 0.7 … 0.9 dB per frame of the original's on both films |
| Circles | the radius laws above; per-frame radius against the original: harmonics 0.95 px rms, lift 1.5; means and wobble within 0.15 px |
| Stripe light | the light law above, run on the audio thread (`dsp/Light.h`); a frame without a new audio block is not a stop until 0.1 s have passed (the circles keep their last spectrum the same way), so long host buffers do not flicker the light; through the sparse loop it never falls below 0.90, and its end matches the original's to ~0.05 of full brightness (out ~0.07 s sooner at the very bottom) |
| Clock | the stripe, circles and meters move on one 60 Hz clock; the plate's ~400 grille dots drawn once per scale: 0.12 of a core playing at 200 % |

### Particle styles

The settings page offers two styles; both move with the project's tempo and follow the light law above.

**CLASSIC** (`Source/ui/Stripe.cpp`, `StripeGlow.h`): the original's look (its palette, a dense band of streaks through
the middle, streamers flowing outwards, tall coloured pillars, the glass's reflections) with our own take:

- **Glow:** its own analytic shape from the measured tokens: a haze rising towards the band, a flat-topped bump on the
  band with a hot line along its top edge, a lip under it and the rim's line, times a lavender Gaussian and a warm
  exponential core along it; a violet haze above the band and round orbs among the dots there (within a few levels of
  the original from y 274 to 282); light added per physical pixel.
- **Neon:** each particle a hot core a little whiter than its colour in a glow of the pure colour and a wide faint
  bloom, glowing up and dying away over 0.1 … 0.35 s (re-scattering every frame reads as frantic at 60 Hz and, with
  lives shorter than a frame, leaves some frames empty: the band's brightness jumps between ~55 and ~115 frame to
  frame; with lives it holds at 91 … 96). 560 particles and 9 pillars, larger than the original's.
- **Black holes past the ends, off screen:** the whole field drifts outwards (8 px/s plus 0.08 × the distance from
  x 444; streamers 18 px/s plus 0.18 … 0.3 × it); within 80 px of an end it is drawn in, faster the closer
  (4·10⁵ / (d² + 400) px/s²), funnelled to the band's height, the stream pinching thinner and drawn out the closer it
  gets, dimming over the last 40 px and gone past the end.
- **Kept inside the glass:** the particles' light fades out above y 275 and below 304 (the 99th percentile of the rows
  on the rim 44 … 73, the original's 66 … 116).
- **Reflections:** the fixed dotted reflections at the measured positions (`addReflections`), with heights from a few
  tokens (rising to the right on the upper line, falling on the lower, a bright spot at its last spike, one level for
  the end bumps), and the band reflected in the lower rim.
- **Against the original** with the same music: mean brightness 60 (57), hue bins .24 .15 .01 / .16 .16 .13 .03 .03
  .09 (.18 .19 .02 / .15 .13 .16 .03 .03 .09), saturated share .34 (.38).
- **Tempo:** the particles move at the pace above times the beats per second (tempo / 60: twice at 120 BPM; 1 … 3.5
  times; twice when the host gives no tempo), easing to a new tempo over ~0.5 s; the brightness still follows the
  level in real time.

**SCORPIUS** (the default; `Source/ui/Sky.cpp`): two scorpions in neon light, our own drawing.

- **The scorpions:** back to back and mirrored in the middle of the tube, side on, tails arched over their backs
  towards each other, claws outwards (each drawn in its own units, ~145 × 35, scaled 0.84 into the tube, the backs of
  their tails 3 px either side of x 444, y 290; the second a step out of time with the first): seven plates along the
  back and a dashed line along the side, a carapace with a groove and eyes, small jaws, five tail segments each with a
  keel and two grains, a bulb and a curved blade for the sting, jointed legs with claws, and heavy pincers with ridges
  and toothed fingers, resting on the ground.
- **Light:** each stroke lit in three layers by its distance to the pixel (a halo, a glow and a thin core; the suite's
  gold on the body, paler gold towards the claws and the sting), trembling slightly; a faint glow fills the body;
  sparks run along the outline. The light is drawn in a layer of its own, held to white and bloomed at three widths
  (σ 7.3, 2.3 and 0.67 design px; the blurs at half resolution, added up there and brought back up once), over the
  scorpions' span only; reflected in the glass's lower rim as the CLASSIC band is.
- **Motion:** they sway and breathe, their legs stepping a little, at half the CLASSIC style's pace (the tempo). On
  every kick their tails strike forwards over their heads in ~0.06 s and settle back over ~0.25 s (a kick mid-swing
  strikes again from where the tails are), a pulse of light running up them and the stings flaring. Any beat (the
  light's jumps) brightens them.
- **Kicks** (`dsp/Kick.h`), found on the audio thread every 2.5 ms in two bands: the sub (below 90 Hz; its peak over
  25 ms 3 dB above a level that rises over 60 ms and follows a decay within 15 ms, above -28 dBFS) finds a kick or an
  808 out of silence or out of a decayed tail; the punch (70 … 200 Hz; its peak over 10 ms 4 dB above a 30 / 8 ms
  level, above -30 dBFS, confirmed by the sub above -26 dBFS within 20 ms) finds a kick landing on one still ringing,
  whose sub hardly rises (a kick sweeping down from 120 Hz onto a 50 Hz tail rises < 2 dB below 120 Hz). Either way the
  sub must be at least half the punch (a snare's onset leaks to -19 dBFS in the sub but is 11 dB stronger in the
  punch); for 60 ms after a kick both levels follow the peaks up, so a held 808 counts once. ScorpiusTests: 24 of 24
  sixteenth kicks at 140 BPM, also 12 dB quieter; 16 of 16 back-to-back 808s; 16 of 16 kicks with 808s between; a
  held 808 once; hats and snares never.
- **Motes:** ~800 gold motes a second at full brightness (more on a beat, none in silence) shed from the outlines (not
  the details inside), 1.2 … 3 design px across, each one glow drawn out along its way. A map of design pixels,
  rebuilt each frame (1 on the lines and inside the bodies, 0 ~2.5 px out), keeps them off the scorpions: born just
  clear of the outline, pushed round it as they flow, faded where they still cross it. Each keeps the brightness it
  was born with; while the host's transport runs, the shedding and the scorpions' glow follow a level that rises with
  the light at once but fades over ~1.5 s (the stream's brightness holds within ~1 grey level through a beat at
  60 BPM); when the transport stops (or the host stops calling the processor) they follow the light itself, fading as
  fast as the CLASSIC style (both start fading on the same frame and are out ~0.6 s later). Each drifts off for
  0.15 … 0.6 s, then streams out as the CLASSIC streamers do (18 px/s plus 0.3 … 0.46 × the distance from the middle)
  into the black holes past the ends (the CLASSIC pull, funnel and thinning), at three quarters of the CLASSIC pace.
- **Silence and the switch:** with no sound the scorpions stay faintly lit and still (no motes); with the particle
  animation off the stripe is dark.

**Cost at 200 %:** SCORPIUS 4.4 ms a frame at full level, 3.4 ms in silence; CLASSIC 4.3 ms.

## Naming

| Original | Recreation | Product folder / target |
|---|---|---|
| Cradle **Orion** | **Scorpius** | `Scorpius` |

As Positron answers The God Particle with its opposite, Scorpius answers Orion: in the myth the scorpion is the
hunter's opposite, and the constellation Scorpius rises as Orion sets, on the far side of the sky. Cradle's and the
co-designer's names, the maker's logo, the product lettering, the images and the fonts are replaced by our own. The
repository states that it is an independent project, not affiliated with Cradle.
