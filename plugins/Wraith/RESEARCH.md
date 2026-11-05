# Wraith: research

What the original does and how its controls and presets are measured. Wraith is an open-source recreation of
Cradle's **The Spirit**, a vocal chain made with producer Louis Bell. Its audio behaviour is in
[MEASUREMENTS.md](MEASUREMENTS.md).

Local sources are an installed copy of the original. Nothing from it (images, scripts, fonts, presets, renders,
screenshots) is in this repository: those files stay in the git-ignored `reference/` folder. The one exception is the
reverb: the room and plate responses are measured from the original's output with impulses and shipped in `ir/` on
recorded approval (MEASUREMENTS.md 6); the original's own files are not copied. Behaviour is found by measuring the
plug-in from the outside.

## Sources

| Id | Source | What it gives |
|---|---|---|
| **W1** | Official product page: [cradle.app/products/the-spirit](https://cradle.app/products/the-spirit) | positioning, "two of his favorite reverbs and a tasteful doubler", "auto-rider", zero latency, formats, price |
| **W2** | Support article [GUI Overview](https://support.cradle.app/hc/en-us/articles/10677127930260-GUI-Overview) | every section described |
| **W3** | [How do I use The Spirit?](https://support.cradle.app/hc/en-us/articles/10677163829396-How-do-I-use-The-Spirit) | intended use: any vocal, also other instruments (the doubler as a stereo imager, the rider for levels) |
| **W4** | [What Is The Spirit?](https://support.cradle.app/hc/en-us/articles/10677110187156-What-Is-The-Spirit) | positioning |
| **L1** | The installed plug-in (VST3) | version 1.0.3 (built in February 2023), category Fx, stereo in and out |
| **L2** | `tools/ParamDump` on L1, 41 points per parameter (`reference/Wraith/paramdump.txt`) | 19 host parameters with their display text, latency 0 at 48 kHz, no programs, editor 1044 x 406, not resizable by the host |
| **L3** | The plug-in's default state from L2 | the start-up preset and the settings the host cannot see |
| **L4** | Screenshots of the editor (`tools/RefCapture`): default, 150 %, plate selected, character off (`reference/Wraith/ui/`) | layout, displays, what each switch shows |
| **L5** | Renders through L1 with `tools/RefRender` and the measurement battery (MEASUREMENTS.md) | the stage facts |

## Product facts (W1 to W4)

- Cradle, $119. Formats: macOS AU / VST3 / AAX, Windows VST3 / AAX (no CLAP, no Linux). Licensing through Cradle Hub.
- The co-designer's signature vocal sound in one plug-in: an EQ and compression chain distilled into a few controls,
  with a doubler, two reverbs (room and plate) and an auto-rider (W1).
- Zero latency and low CPU use, for recording through it (W1, W3); L2 confirms latency 0.
- No oversampling options, no side-chain, no tempo sync.

## Signal flow

The panel reads left to right: **input (gain, rider) → character (compression, focus) → eq (high, low) → doubler
(stereo, mix) → reverb (filter, mix, room / plate) → output (gain)**. W2 describes the rider as acting on the input
signal and the input meter as showing the level after the rider and the gain knob. Measured, the reverb runs before
the doubler: input gain → rider → character → eq → reverb → doubler → output gain (MEASUREMENTS.md 1, 6.1).

## Controls (W2, with L2 for the numbers and L3 for the start-up values)

The host parameters, in the original's order. "Preset" is the value the factory preset "lead" loads at start-up
(L3); the plug-in opens with it, not with the host defaults.

| # | Control (UI) | Host name (L2) | Range / display (L2) | Taper (taper_fit) | Host default | Preset | Documented behaviour (W2) |
|---|---|---|---|---|---|---|---|
| 0 | input **gain** knob | `Input Gain` | -12 ... +12 dB, three decimals | linear | 0 dB | 0 dB | input gain; a yellow band on the knob shows the rider's gain in real time |
| 1 | rider **speed** (behind ">") | `Gain Rider Speed` | 0.001 ... 0.010 | linear | 0.003 | 0.003 | the rate at which the riding is applied |
| 2 | rider **amount** | `Gain Rider Amount` | 0 ... 1 | linear | 0.70 | 0.70 | the amount of gain compensation |
| 3 | rider **floor** | `Gain Rider Floor` | -50 ... -18 dB | linear | -30 | -30 | below this input level the rider stays inactive; drawn as a red line on the input meter |
| 4 | **rider** button | `Gain Rider State` | off / on | switch | off | off | turns the rider on |
| 5 | **compression** knob | `Compression` | -50 ... +50, 101 steps | linear | 0 | 0 | the amount of compression; the co-designer's setting is the centre |
| 6 | **focus** knob | `Focus` | -50 ... +50, 101 steps | linear | 0 | +8 | the amount of the co-designer's vocal EQ curves; his preferred setting is the centre |
| 7 | character power | `Character State` | off / on | switch | off | on | |
| 8 | eq **low** knob | `EQ Low Gain` | -12 ... +12 dB | linear | 0 | +4.10 | gain of a low shelf: warmth and body |
| 9 | eq **high** knob | `EQ High Gain` | -12 ... +12 dB | linear | 0 | +0.03 | gain of a high shelf: air and sibilance |
| 10 | eq power | `EQ State` | off / on | switch | off | on | |
| 11 | doubler **stereo** | `Doubler Stereo` | 0 ... 1 | linear | 0.5 | 1.0 | spreads the voices in the stereo field |
| 12 | doubler **mix** | `Doubler Mix` | 0 ... 1 | v = n / (4 - 3n) | 0.10 | 0.10 | the intensity of the chorus-like doubling |
| 13 | doubler power | `Doubler State` | off / on | switch | off | off | |
| 14 | reverb **filter** | `Reverb Filter` | 2000 ... 20000 Hz | 41-point table | 20000 | 9845 | a high cut on the wet signal to trim sibilance |
| 15 | reverb **mix** | `Reverb Mix` | 0 ... 1 | v = n / (4 - 3n) | 0.10 | 0.079 | dry / wet blend |
| 16 | reverb power | `Reverb State` | off / on | switch | off | on | |
| 17 | output **gain** knob | `Output Gain` | -12 ... +12 dB | linear | 0 | 0 | final trim |
| 18 | (host) | `Bypass` | Off / On | switch | Off | Off | the host's bypass |

The two Mix tapers are checked at four points (n = 0.25, 0.3077, 0.5, 0.75 give 0.077, 0.100, 0.200, 0.429). The State
parameters are the power buttons (1 = on); all five off pass the input through bit for bit (MEASUREMENTS.md 1).

Not host parameters (L3, L4):

- **room / plate** (reverb): which of the two reverbs plays. The preset stores it; the host cannot automate it.
- The preset itself (11 factory presets in the menu, a save button, previous / next arrows) and the UI scale (100 % in
  the menu; 150 % read from a capture with the state edited).

## Presets

- 11 factory presets, chosen from the top bar. The plug-in starts with "lead" (L3), which turns character, eq and
  reverb on, doubler and rider off, and sets the values in the Preset column above.
- They store values the knobs show rounded (EQ Low 4.0975 dB, Reverb Filter 9845.186 Hz), so they are nulled by
  loading the original's own preset state, never by typing the knob values (MEASUREMENTS.md 8).
- Ours ship under our own names (no artist or product names), with the original's values.

## Editor (W2, L4)

- 1044 x 406 px at 100 %; a top bar (logo, preset box with arrows and save, UI Scale menu) over a brushed-metal plate
  with six sections, each with a lit display above its knobs.
- **input**: a meter with two readouts (dB) and a yellow target bracket (where the co-designer's input level lands),
  the rider button with a ">" that opens speed / amount / floor, the gain knob.
- **character**: a wide display (compression bars and a focus shape that move with the audio), two large knobs.
- **eq**: a small display with the shelf curve, two knobs. **doubler**: a display, two knobs. **reverb**: a display (a
  triangle that follows the filter and mix), two knobs, room / plate buttons. **output**: a meter with readouts and the
  gain knob. A power button above each of character, eq, doubler, reverb.
- A switched-off section goes dark (L4: character off).
- Ours keeps this layout (positions, sizes and hit areas measured on L4, `Source/ui/Look.h`) and draws every part in
  code in the suite's own look (`shared/ui/Theme.h`): violet-black cards on true black for the plates, wells for the
  slots, holes and screens, the suite's knob (a gold value arc, a pearl pointer) for every knob, gold-to-pearl bars for
  the meters on the original's scale, gold toggles for the power, rider and room / plate buttons, and the displays'
  drawings as smooth light-gold strokes (rounded, with a soft glow).

## Measured, not documented

The manual leaves these out; each is measured in MEASUREMENTS.md:

| Topic | Section |
|---|---|
| The order of the stages, and where input and output gain sit | 1, 6.1 |
| Parameter smoothing | 2 |
| Rider: detector, target level, how speed, amount and floor act | 3 |
| Character: the compressor law, detector, time constants, the Focus EQ curves, the shaper, and why compression's range is centred on 0 (the knob is a drive) | 4 |
| EQ: shelf frequencies and slopes per sample rate | 5 |
| Reverb: the two responses (length, decay per band, stereo), the filter's type and slope, the mix law | 6 |
| Doubler: voices, delays, modulation, how stereo spreads them, the mix law | 7 |
