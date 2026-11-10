# Positron: research

What the original does and how its controls and editor are measured. Positron is an open-source recreation of
Cradle's **The God Particle**, a mix-bus and master-channel processor made with mix engineer Jaycen Joshua. Its audio
behaviour is in [MEASUREMENTS.md](MEASUREMENTS.md).

Local sources are an installed copy of the original. Nothing from it (images, scripts, fonts, presets, renders,
screenshots) is in this repository: those files stay in the git-ignored `reference/` folder. Behaviour is found by
measuring the plug-in from the outside.

## Sources

| Id | Source | What it gives |
|---|---|---|
| **W1** | Official product page: [cradle.app/products/the-god-particle](https://cradle.app/products/the-god-particle) | description, formats, system requirements, price |
| **W2** | Support article [GUI Overview](https://support.cradle.app/hc/en-us/articles/4411750433044-GUI-Overview), with an annotated 200 % screenshot | every control described |
| **W3** | [How do I use The God Particle?](https://support.cradle.app/hc/en-us/articles/6423895706004-How-do-I-use-The-God-Particle) | intended use, meaning of the green targets |
| **W4** | [What Is The God Particle?](https://support.cradle.app/hc/en-us/articles/4411773820692-What-Is-The-God-Particle) | positioning |
| **W5** | [Updates and Release notes](https://support.cradle.app/hc/en-us/articles/6423691528468-Updates-and-Release-notes) | version history 1.0.2 → 1.2.5, the settings page added in 1.2.2 |
| **W6** | [Oversampling](https://support.cradle.app/hc/en-us/articles/15947880896532-Oversampling) | 1x / 2x / 4x / 8x, latency grows with oversampling |
| **W7** | [LUFS Metering](https://support.cradle.app/hc/en-us/articles/15947889022484-LUFS-Metering) | RMS & Peak or Short-term LUFS & Peak readouts |
| **W8** | [How do I export stems using The God Particle?](https://support.cradle.app/hc/en-us/articles/12637616897940-How-do-I-export-stems-using-The-God-Particle) | what the side-chain drives and what it does not |
| **W9** | FAQ: [targets](https://support.cradle.app/hc/en-us/articles/6424147405076-Why-doesn-t-my-track-hit-all-of-the-gain-reduction-targets), [inner workings](https://support.cradle.app/hc/en-us/articles/6424232645908-Can-you-tell-me-more-about-what-s-going-on-inside-The-God-Particle), [presets](https://support.cradle.app/hc/en-us/articles/6424187550868-Are-there-any-presets-included-in-The-God-Particle) | the defaults are the co-designer's settings; internals are not published; preset save and load |
| **W10** | [KVR product page](https://www.kvraudio.com/product/the-god-particle-by-cradle/details) (secondary) | version 1.2.4, formats, price; nothing beyond W1 |
| **L1** | The installed plug-in (VST3) and the version information it carries | version 1.2.4, VST 3.7.8 SDK, category Fx; built in July 2024 |
| **L2** | `tools/ParamDump.cpp` run on L1 (`reference/params_48k.txt`, `reference/params_41pt.txt`) | every host parameter: names, ranges, defaults, display text; buses, latency, editor size |
| **L3** | The plug-in's default saved state, from L2 | how its settings are grouped |
| **L5** | Screenshots of the editor at 100 % and 200 % (the MeterCapture host and `tools/RefCapture`, 50 Hz tone bursts; `reference/editor_f*.png`) | the 1.2.4 layout, 888 × 359 px |

## Product facts (W1, W3, W4, W9, W10)

- Cradle, $119. Formats: macOS AU / VST3 / AAX, Windows VST3 / AAX (no CLAP, no Linux). Licensing through Cradle Hub,
  internet needed. Version 1.2.4 measured; 1.2.5 changed only the macOS certificates and still reports 1.2.4 (W5).
- A whole master-channel chain in one plug-in: several processing algorithms, harmonic processing, an adaptive
  limiter that keeps dynamics and transients at commercial loudness, and input and gain-reduction targets for gain
  staging and a balanced EQ (W1).
- For the master bus, also drum and instrument busses and single tracks (W3, W4).
- The defaults are the co-designer's own settings, used unchanged on every mix since 2021; adjustments go before the
  plug-in's input (W3, W9).

## Controls (W2, with L2 for the numbers)

Signal order, from W2 and the state's grouping (L3), confirmed by measurement (MEASUREMENTS.md 1):
**input gain → EQ (low / mid / high) → character (the amount: multiband dynamics and its processing chain) → limiter →
output gain**.

| Control (UI) | Host parameter (L2) | Range / display (L2) | Default | Documented behaviour (W2 unless noted) |
|---|---|---|---|---|
| **input** knob (bottom left) | `Input Gain` | -12 … +12 dB, linear in the normalised value (2.4 dB per 0.1) | 0 dB | level into the plug-in; meter with peak readout (red above 0 dBFS) and RMS readout, both reset by clicking; the green target is where the co-designer's mix input lands |
| **eq high / mid / low** knobs | `EQ High Gain`, `EQ Mid Gain`, `EQ Low Gain` | -6 … +6 dB, linear | 0 dB | air, body and low-end warmth; meant to steer each band to its gain-reduction target before the character section |
| eq power button | `EQ Bypass` | 2 steps (0 = active) | active | bypasses the EQ |
| **amount** knob (large, centre) | `Character` | 0 … 1 in the host; the UI shows 0 … 200 % (0.5 = 100 %) | 100 % | how much character is applied: the processing chain whose key part is a 3-band (high / mid / low) dynamics processor |
| amount power button | `Character Bypass` | 2 steps | active | bypasses the character section; lower CPU while bypassed (W5, 1.2.2) |
| gain-reduction meters and readouts (high / mid / low) | none | dB | | attenuation per band; a green target per band |
| **Sidechain INT / EXT** (top bar) | none: host-only, saved with the host's project, not in presets (L3) | INT / EXT | INT | EXT: the side-chain bus drives the multiband dynamics; the limiter always detects its own input (W8) |
| **limiter** knob (bottom) | `Limiter Input Gain` | 0 … +12 dB, non-linear taper (below) | +5 dB (0.494206) | gain into an adaptive limiter: louder with more gain, never above 0 dBFS; two readouts show the limiter's reduction (L / R) |
| limiter power button | `Limiter Bypass` | 2 steps | active | bypasses the limiter |
| **output** knob (bottom right) | `Output Gain` | -12 … +12 dB, linear | 0 dB | final level after the limiter (kept at 0 dB to avoid clipping); meter as the input's |
| preset menu, ← →, disk icon | none | factory "default", user presets | default | save with the disk icon; user presets under "user" (W9) |
| UI Scale menu | none (in the saved state) | 50 … 200 % | 100 % | window zoom |
| settings (gear, since 1.2.2) | none (a global setting) | oversampling 1x / 2x / 4x / 8x; meters RMS or Short-term LUFS; animation on / off | 1x, RMS & Peak, on | W5, W6, W7; oversampling adds latency (W6) |
| none | `Bypass` | Off / On | Off | the host bypass |

**Limiter Input Gain taper** (L2, 41 points). Normalised → dB: 0 → 0.000, 0.25 → 2.351, 0.494206 → 5.000 (default), 0.5
→ 5.068, 0.75 → 8.242, 1 → 12.000. Not a power law (a JUCE skew fits only to ±0.21 dB); `13.96 · (e^(0.6193 · p) - 1)`
fits to ±0.025 dB and the cubic `8.830p + 2.038p² + 1.126p³` to ±0.006 dB (the display's precision is 0.001). The
41-point table itself, linear between points, is the taper (`Source/Params.h`).

**Host-level facts (L1, L2).**

- One effect class, vendor Cradle.
- Buses: stereo in, stereo out, a side-chain input bus (off by default). Mono to mono is not supported.
- Reported latency at the defaults: 179 samples at 44.1 kHz, 189 at 48 kHz, 357 at 96 kHz (not a fixed time: about
  4.0 / 3.9 / 3.7 ms); per rate and oversampling factor in MEASUREMENTS.md 1 and 7. Tail: 0.
- No VST programs; the state is about 2.5 kB.
- Editor: 888 × 359 px at 100 %, not resizable by dragging (scale menu only).
- The saved state places the EQ and the character section in the oversampled block and the limiter after it; input
  and output gain and the side-chain switch sit outside the preset, so loading a preset keeps them (L3).

## Editor (W2, L5)

Layout at 100 % (888 × 359), version 1.2.4:

- **Top bar** (black): the maker's logo (left), `Preset` label and drop-down (`default`), ← / → arrows, disk (save)
  icon, `Sidechain` label and an `INT | EXT` segmented toggle (the selected segment white), `UI Scale` drop-down
  (`100%`), settings gear (right).
- **Main panel** (black, light-grey rounded outline), six columns separated by thin vertical lines:
  1. input meter: peak readouts L/R (top), RMS readouts L/R, a bracket-shaped green target, two green LED bar meters;
  2. EQ: mint-green power button, three small knobs `high`, `mid`, `low`;
  3. the particle visualiser (a rounded stadium shape with animated coloured particles) with the large `amount` knob,
     its caption, a big `100%` readout (mint) and a mint power button;
  4. gain reduction: per band a label (`high` / `mid` / `low`), a GR readout, green target brackets and small
     horizontal LED meters;
  5. limiter: mint power button, GR readouts L/R and meters;
  6. output meter, as the input one.
- **Bottom plate** (dark warm grey, baked shadows): knobs `input`, `limiter`, `output`; labels `eq` and
  `gain reduction` over their columns; a grille of horizontal slots with the product name in spaced letters in the
  middle.
- Fonts: a commercial sans in Regular, Light and Light Italic (not shippable) and Source Code Pro Regular (SIL OFL).
- The editor is dark; its only alternate appearance is the visualiser (colour / white / off; the animation toggle).
- The W2 screenshot (version 1.2.1, 200 %) shows the same layout without the gear and with a static visualiser; the
  1.2.4 layout is the one recreated.

### Editor measurements (L5, `tools/RefCapture`, 200 % screenshots)

All numbers in design pixels (pixels at 100 %): the original renders vector-sharp at 200 %, so everything is measured
there and halved. Positron's editor is compared with `PositronSnapshot` and `tools/compare_ui.py` (mean absolute RGB
difference over the window: 8.4 / 255 at 200 %, most of it in the animated and photographic parts and in anti-aliased
text edges).

| Element | Measured |
|---|---|
| Window | 888 × 359.5 (heights truncate: 359 at 100 %, 719 at 200 %); UI Scale 50 / 75 / 85 / 100 / 125 / 150 / 200 %, saved per instance |
| Top bar | 0 … 30.5, #050607. Text #E7F1F4, 12 px. Preset box (176, 3, 193 × 24.5) fill #121211, 1 px #7F7E7A; ← → and save boxes 24 × 24.5 with a #E7F1F4 frame; INT/EXT (560, 3, 85 × 24.5), the selected half filled #E7F1F4; UI Scale box (794, 3, 66 × 24.5); gear #7F7E7A |
| Main panel | rounded outline r ≈ 15, 2 px #C0C0C0, black inside; column dividers at x 89 / 176 / 559 / 711 / 798, 1 px #3C3C3C |
| Mint | #8EDBC4: readouts, labels, power buttons (72 × 24.5, filled = on, 1 px outline = bypassed) |
| I/O meters | readouts at x 28.75 / 65.25 (input) and 824.75 / 861.25 (output), peak baseline 56.5, RMS 79.5. 40 LEDs per channel, 8 × 1 on a 4 px pitch, bottom LED at y 248; LED k lights above -58.5 + 1.5 k dB (strictly above: a -6.0 dB sine peak lights LED 34, not 35). Green #00824B bar = plain RMS (150 ms; a sine reads 3 dB under its peak); above it a mint run up to the fast peak (1 ms / 50 ms follower); one mint LED at the peak readout's held value, not drawn above 0 dBFS (MEASUREMENTS.md 6). Input target: brackets at x 15 / 71, 8 wide, 1 px strokes centred on y 103.75 / 122.75, corner radius 2.5, and a 1 px line pair (x 35 … 59) on the same lines, #00824B; lit, the brackets become solid blocks (y 103.25 … 123.25) rounded on their outer corners and the line pair a solid block; it fills with the fast peak (the top of the mint run, either channel), fully from -12 to -3 dBFS, fading over 1.5 dB (one LED) at each end; all three parts fill together |
| EQ | knobs R 20.375 at (133.375, 90.75 / 155.75 / 220.75) (outer edge, found by maximising inside/outside contrast along the circle); labels 11.25 px at baselines 125.5 / 190.5 / 255.5; labels #BCBABB while the EQ is bypassed |
| Amount | knob R 50.875 at (292.875, 148.25); "amount" 16.75 px at (364, 120.5); value in 40 px-class digits at baseline 159.5, 0 … 200 %; text #BCBABB while bypassed |
| Gain reduction | labels at x 571, values right-aligned at 701.5 (the EQ's baselines); meters = 1 × 8.5 bars on a 4 px pitch growing left from x 700 at y 86 / 151 / 216; targets 19 wide at x 681 (high), 621 (mid), 653 (low), 1 px strokes centred on meterY - 9.25 / + 17.75, corner radius 3.5; bars = floor(5.5 × GR) plus one marker bar at the readout's held deepest GR on a 20 dB scale (1.65 bars / dB); each target fills with the band's GR, fully over 0.34 … 1.38 / 2.45 … 3.98 / 0.97 … 2.46 dB (high / mid / low), fading over ~0.22 dB at each end; lit, the upper and lower U fill separately and the bars pass between (MEASUREMENTS.md 6); labels, values and targets #808080 while the character section is bypassed |
| Limiter | readouts at 737.5 / 774 (baseline 80), mint dashes at y 90; #808080 while bypassed |
| Visualiser glass | racetrack centred (367.75, 148.25), straight half-length 75.25, out to r 113; its lighting measured as a field over the track (`tools/fit/fit_glass.py`: 25 stations per straight, 144 per end (1.25°), 0.5 px radial steps; the lit glass as the median of the active frames, ≈ grey 37 near the pill, 15 at the outer edge) |
| Amount pill | centre (368.1, 148.9), half-length 74.7, r 49.75 (not concentric with the glass), black inside, ~0.7 px edge of grey ≈ 130 |
| Sparks | filmed with RefCapture and tracked frame to frame: a free-running 1 s loop at 30 frames/s that does not restart with the audio (its motion does not follow the level; how many are lit does); ~290 sparks per frame at 100 %; counter-clockwise drift, faster further out (-70 / -89 / -108 px/s at r 53 to 70 / 70 to 90 / 90 to 112) with large scatter, outer sparks pulled inwards; lifetimes mostly under 0.2 s (up to ~0.5 s); hue shares white 34 %, yellow 20 %, cyan-blue 16 %, blue 10 %, orange 9 %, violet 7 %, magenta/red 4 %; size (blob area at 100 %) quartiles 1 / 3 / 9 px², 90th percentile 27 |
| Visualiser light | follows the input level after the input gain (the output gain has no effect), filmed with sine and pink-noise staircases, a 32 s fade, stops from -6, -30, -45, -55 and -65 dBFS and the end of a mastered track: a peak meter that jumps up at once and falls ~90 dB/s, no hold; full brightness down to -40 dBFS, dark at -75. With v = (meter + 75) / 35, the glass glow is v^1.6 of full (sine steps: 78 % at -45, 59 % at -50, 43 % at -55, 28 % at -60, 15 % at -65); the sparks go out sooner (about half lit at -55, nearly none at -60). After a stop the light holds while the meter falls to -40 (0.40 s from -6 dBFS, 0.12 s from -30, none from -45), then both layers fade over ~0.4 s (sparks ~0.25 s; the glow 69 % after 0.08 s, 36 % after 0.18 s, 17 % after 0.28 s). The meter reads the frame's raw input samples, not the slowly falling meters; the colour mix = amount / 100 % (white at 0 % or bypassed); animation off = a static frame |
| Plate | rounded panel x 0.5 … 887.5, y 266.5 … 358.75, corner radius 11, on black; #46453F with an embossed leather grain at the device pixel (std ≈ 3.9 grey levels, lag-1 correlation ≈ -0.3); labels #BCBABB 12 px at baseline 280; knobs R 25.06 at y 313.11 (x 45.755 / 754.745 / 841.74); their shadow (light from the upper right, darkest toward 240°, factor ~0.3 at the edge, 0.57 at 16 px, 0.72 at 24 px, 0.86 at 40 px); grille 19 staggered rows on a 24 px pitch, bar length 21 → 7 |
| Knobs | brushed metal, light fixed, pointer turning -135 … +135°; per knob size: mean grey ~150, a highlight pair at ~67° from up, the rim's light and dark greys, the pointer's length and width |
| Mouse | JUCE's slider behaviour (RefCapture drag scripts, `nulltest/compare_ui.py --knobs`). Vertical drag, absolute from the press point: 1 % of the range per design pixel (the full range in 100 px at every UI scale), so after overshooting an end the mouse comes back that far before the value moves (up 80 px then back 40 from 0 dB: +9.6 dB). Shift: velocity mode, cursor hidden: each mouse move of d px changes the value by 0.2 · (1 + sin(π (1.5 + min(0.5, max(0, d - 1) / 200)))) of the range (JUCE's defaults: sensitivity 1, threshold 1, offset 0; d = 2 … 200 px per move matches to 0.001 dB), so slow moves fine-tune and fast ones jump, at most 20 % per move. Ctrl: the normal speed (pressed before or during the drag). Double-click or Alt-click: the default value |
| Value readout | while the mouse is over a knob's cell, or the knob is dragged (wherever the mouse goes), its caption shows the value instead of its name: `%.1f dB` (`3.6 dB`, `-3.6 dB`, `-0.0 dB` for -0.006, no plus sign), in the caption's font, colour, size and baseline, centred the same way; it switches within one repaint (< 12 ms) both ways, no fade. Cells: the knob's column, 87 px wide centred on the knob; on the plate its full height (from y 266.5), for the EQ knobs from 20.5 px above the knob centre to 45 px below. The amount knob keeps its own readout |
| Settings dialog | (234, 50.5, 420 × 255.5); oversampling 1 / 2 / 4 / 8, I/O metering RMS & Peak / Short-term LUFS & Peak, particle animation ON / OFF; defaults 1, RMS & Peak, ON; global (all instances) |
| Save dialog | (240, 74, 408 × 209): a "preset name" field, save / cancel |
| Preset list | FACTORY / USER captions (spaced capitals, #C8785A), factory "default", user presets by name |
| RMS readout | live, not held (a step from -6 to -20 dB reads -20.9 after 2.5 s); a -6 dBFS sine reads -7.1 (20 to 100 Hz: -6.9 … -7.1), -7.2 (1 kHz), -8.1 (2, 5, 20 kHz), -7.4 (8, 16 kHz, where the sampled peak is -7.3), -8.7 (12 kHz); noise at RMS -12 dB reads -10.4; the law: MEASUREMENTS.md 6 |
| Faint backgrounds | with the dark levels lifted ×12: the I/O columns, the limiter's two GR tracks (x 732 to 744, 768 to 780) and the three band GR tracks (x 572 to 702) are one grey level above the panel |

## Positron's own editor

The layout (positions, sizes, hit areas) is the measured one; everything drawn on it is Orrery's own look
(`shared/ui/Theme.h`): a violet-black panel and plate on true black, lavender-white lettering, gold values, meters,
targets and power buttons, pearl pointers.

| Part | Positron |
|---|---|
| Knobs | the suite's knob at the measured sizes and pointer travel (a violet-black disc, a gold value arc from 0 dB on the bipolar gains, a pearl pointer; `theme::drawKnob`); the plate knobs' shadow drawn from the measured numbers as tokens (`shared/ui/KnobShadow.h`: the disc swept away from the light with a soft edge, plus a contact shadow) |
| Meters | the suite's meter bars, lit in whole cells on the LED scales above so they move at the same thresholds |
| Plate | a card with a small orrery (four slanted orbits round the suite's mark, a few seeded stars) in place of the leather and grille; "POSITRON" lettering centred on the sixteen letter slots |
| Maker's mark | the Orrery mark (a sun on its orbit, the orbit's lower arc lit as a crescent and a planet) in the logo's place and size; the logo opens a menu drawn as the editor's own drop list: version header, About panel, repository, Report an Issue, License (AGPL-3.0) |
| Font | Instrument Sans Regular (SIL OFL, `resources/fonts`), the closest in widths and shapes of five candidates on rendered words ("amount", "Sidechain", "high", "Preset") |
| Glass | a procedural drawing at the measured layout (`tools/fit/make_glass.py`, `glass_params.json` → `resources/glass/*.png`): two rim lines and faint sheen lines, each a base level with a few soft highlights at measured stations; the reflections as soft-edged bands between cubic edge curves (four radii per piece, one to three pieces per edge) with our own shading (a highlight across the band over a floor, a rise and a fall along it) in the measured peak colours; for the lit glass the sparks' light as coloured vertical streaks from seeded noise, fading outwards along an exponential set to the measured falloff, held back by the reflections; positions, sizes and colours are measured tokens (radii to 0.5 px); Catmull-Rom interpolation keeps the reflections' slanted edges smooth; a greyscale version when the sparks are white |
| Visualiser light | the same meter, glow v^1.6, sparks ((v - 0.4) / 0.6)^0.7, falling with real elapsed time: the glow within ~1 grey level of the original at every step and the track's ending, stops within a frame |
| Resizing | also by dragging the bottom-right corner (three light grooves cut into the plate, brighter under the mouse) or the host's window edge: proportions fixed, 50 … 200 %, the UI Scale box shows the result; while the size changes the per-scale images (glass, the plate knobs' shadow) are drawn stretched and rendered sharp again once it settles (150 ms or on release): about 9 ms a frame instead of 107 (`PositronSnapshot --bench`) |
| Knob entry | a double-click opens a field to type the value; Alt-click resets |
| I/O LINK | a toggle in the top bar (664, 3, 64 × 25), centred between the side-chain switch and the `UI Scale` label, drawn like a segment of INT / EXT (filled while linked), saved with the host's project. Linked, the output gain is always the input gain's opposite: linking snaps the output to -input, a gesture on either knob moves the other (both captions show their values, host gestures for both), host automation and presets are mirrored by the editor, and the processor applies output = -input while linked (automating only the input keeps the output mirrored with the editor closed) |
| Particle style | a settings row "particle style": CLASSIC (the original's sparks: hue shares and colours fitted per group, crisp points with a moderate glow, the fastest blurred into short dashes over 1/120 s) or POSITRON (a bubble chamber: gamma rays turn into electron / positron pairs whose tracks curl apart and spiral in, cyan and magenta; pairs annihilate in a flash with two back-to-back gamma rays; a counter-flow of matter and antimatter specks; violet glass; a 3 s loop; white at amount 0 %) |

**Tempo (both styles).** The animation's clock runs at its pace times tempo / 120 (once at 120 BPM; 0.5 … 1.75 times;
once when the host gives no tempo), easing to a new tempo over ~0.5 s, drawn at 60 frames/s by the visualiser's own
timer (the original's sprite is a fixed 1 s loop at 30 frames/s). The light still follows the input's level in real
time. Scorpius does the same (its RESEARCH.md).

**Neon.** Each spark is a core a little whiter than its colour, in a halo of the pure colour and a wide faint bloom
(Gaussians of 0.3 + 0.4 × its size, 1.1 + 0.9 × it and 3.5 + 1.5 × it px), their light added in a buffer as light is
(burning whiter where they crowd; past white it spills into the other channels) and laid over the glass as opaque as
it is bright, glowing up and dying away smoothly (sin^0.6 over its life). Lives 0.1 … 0.9 s, over a 4 s loop of 4400
sparks, so about as many show at once as in the original.

**The black hole.** The amount pill. Each spark's path is worked out when the loop is made (every 1/120 s): drawn in at
7·10⁵ / (distance + 8)² px/s² and along the flow half as much, so the ones within ~25 px spiral in, faster the closer,
thinner as they go (down to a third), and are gone at its edge. A soft warm glow round the pill and a thin ring of bent
light hugging it, brighter on one side, turning with the flow.

**Clearer glass (both styles).** The lit haze at 0.65 of the original's strength, and over everything (lit or not) a
faint sheen across the top of the ring (white 7.5 % fading to nothing by the pill's top; 3 % along the bottom), a
streak of light along the upper outer curve (white 30 % up and to the left, fading across), and thin bright edges at
the outer and inner rims (10 / 7 %, up to 20 / 15 % while lit).

**Reflections of the sparks.** The rims are curved mirrors, so each spark shows there squeezed against the rim (at a
tenth of its distance from it) and drawn out along it over ~5 px, at 0.7 (outer) / 0.55 (inner) of its brightness,
fading as e^(-distance / 40 px).

## Naming

| Original | Recreation | Product folder / target |
|---|---|---|
| Cradle **The God Particle** | **Positron** | `Positron` |

Cradle's and the co-designer's names, the maker's logo, the product lettering and all shipped images and fonts are
replaced by our own. The repository states that it is an independent project, not affiliated with Cradle.
