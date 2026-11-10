#pragma once
#include <juce_gui_basics/juce_gui_basics.h>
#include "shared/ui/Theme.h"

// Wraith's layout, measured on the reference at 100 % (1044 x 406 design pixels) and 150 %: ui_measure.py on the
// default capture, the slots and holes as dark components (x, y, w, h below), and RefCapture films for the behaviour
// (see the editor). All numbers are design pixels. Everything drawn on it is the suite's own look (shared/ui/Theme.h);
// the colours below are the palette's, named for the parts that use them.
namespace wr::look
{
using juce::Colour;

// ---- colours: the palette's (orrery::theme) ----------------------------------------------------------------------
inline const Colour plateMid { orrery::theme::card };                       // character, eq, doubler, reverb
inline const Colour plateIo { orrery::theme::card.interpolatedWith (orrery::theme::raised, 0.5f) };   // input / output: a step up
inline const Colour label { orrery::theme::letteringDim };                  // section and knob labels
inline const Colour labelOff { orrery::theme::letteringFaint };             // the knob labels of a switched-off section
inline const Colour value { orrery::theme::gold };                        // a label showing its knob's value; readouts
inline const Colour rivet { orrery::theme::line };                          // the plates' corner rivets
inline const Colour glow { orrery::theme::gold };                         // the lit edge round a display
inline const Colour glowOff { orrery::theme::line };
inline const Colour pixel { orrery::theme::goldLight };                   // the displays' drawings
inline const Colour floorLine { orrery::theme::pearl };                     // the rider floor while it is dragged

// ---- layout ----------------------------------------------------------------------------------------------------
inline constexpr float designW = 1044.0f, designH = 406.0f, topBarH = 30.0f;
inline constexpr float plateTop = 40.0f, plateBottom = 395.6f;

enum Section { input, character, eq, doubler, reverb, output, numSections };
// plate left / right edges (3 px gaps between them)
inline constexpr float plateX0[numSections] { 10.0f, 138.0f, 486.0f, 614.0f, 742.0f, 870.0f };
inline constexpr float plateX1[numSections] { 135.0f, 483.0f, 611.0f, 739.0f, 867.0f, 995.0f };
inline constexpr bool darkPlate (int s) { return s == input || s == output; }
inline constexpr float centreX (int s) { return (plateX0[s] + plateX1[s]) * 0.5f - 0.5f; }
// the side strip with the name, right of the output plate (its right edge mirrors the input plate's 10 px margin)
inline constexpr float stripX0 = 998.0f, stripX1 = 1034.0f;

// vertical slots: 9 wide, 3 px in from each plate edge (x = plateX0 + 3 and plateX1 - 14), radius 4.5
inline constexpr float slotW = 9.0f;
struct Span { float y, h; };
inline constexpr Span slotsMiddle[] { { 59.5f, 21.5f }, { 88.0f, 100.0f }, { 196.0f, 152.0f }, { 356.0f, 20.5f } };
inline constexpr Span slotsIo[] { { 59.5f, 21.5f }, { 87.5f, 148.5f }, { 243.5f, 21.5f }, { 272.0f, 76.0f }, { 356.0f, 20.5f } };

// wide stadium holes (h 20.5, radius 10.25)
struct Box { float x, y, w, h; juce::Rectangle<float> r() const { return { x, y, w, h }; } };
inline constexpr Box wideHoles[] {
    { 30.0f, 60.0f, 84.0f, 20.5f }, { 30.0f, 356.0f, 84.0f, 20.5f },                                   // input
    { 158.0f, 60.0f, 84.0f, 20.5f }, { 378.0f, 60.0f, 84.0f, 20.5f },                                  // character
    { 158.0f, 356.0f, 84.0f, 20.5f }, { 250.0f, 356.0f, 120.0f, 20.5f }, { 378.0f, 356.0f, 84.0f, 20.5f },
    { 506.0f, 356.0f, 84.0f, 20.5f },                                                                   // eq
    { 633.0f, 356.0f, 84.0f, 20.5f },                                                                   // doubler
    { 890.0f, 60.0f, 84.0f, 20.5f }, { 890.0f, 244.0f, 84.0f, 20.5f }, { 890.0f, 356.0f, 84.0f, 20.5f } // output
};

// pill buttons (in the holes' places)
inline constexpr Box powerPill[4] { { 249.0f, 60.0f, 120.0f, 20.5f }, { 505.0f, 60.0f, 84.0f, 20.5f },
                                    { 633.0f, 60.0f, 84.0f, 20.5f }, { 761.0f, 60.0f, 84.0f, 20.5f } };
inline constexpr Box riderPill { 29.0f, 239.5f, 88.5f, 28.0f };
inline constexpr float riderSplit = 88.5f;                         // the line between "rider" and ">"
inline constexpr Box roomPlatePill { 761.0f, 356.0f, 84.0f, 20.5f };
inline constexpr float roomPlateSplit = 803.5f;

// displays (the lit ring's outer edge) and the knob wells under them
inline constexpr Box display[4] { { 156.0f, 86.0f, 308.0f, 104.0f }, { 504.0f, 86.0f, 88.0f, 104.0f },
                                  { 632.0f, 86.0f, 88.0f, 104.0f }, { 760.0f, 86.0f, 88.0f, 104.0f } };
inline constexpr Box well[4] { { 157.0f, 195.0f, 306.0f, 153.0f }, { 506.0f, 195.0f, 84.0f, 153.0f },
                               { 633.0f, 195.0f, 84.0f, 153.0f }, { 761.0f, 195.0f, 84.0f, 153.0f } };
inline constexpr Box ioWell[2] { { 30.0f, 271.5f, 84.0f, 77.0f }, { 890.0f, 271.5f, 84.0f, 77.0f } };
inline constexpr Box meter[2] { { 29.0f, 86.0f, 87.0f, 151.0f }, { 889.0f, 86.0f, 87.0f, 151.0f } };

// knobs: centre and radius
struct Knob { float x, y, r; };
inline constexpr Knob compressionKnob { 238.0f, 264.0f, 61.8f }, focusKnob { 382.0f, 264.0f, 61.8f };   // point symmetry at 100 %
inline constexpr float smallKnobR = 23.9f, smallKnobTopY = 226.0f, smallKnobBottomY = 302.0f;   // x: the section's centre
inline constexpr Knob gainKnob[2] { { 72.0f, 301.0f, 23.7f }, { 932.0f, 301.0f, 23.7f } };

// label baselines
inline constexpr float knobLabelY = 342.0f, upperLabelY = 266.5f, sectionLabelY = 391.5f;

// the plates' corner rivets (where the reference has screws): 9.5 px in from the plate's sides, at y 49 and 389
inline constexpr float rivetInset = 9.5f, rivetTopY = 49.0f, rivetBottomY = 389.0f, rivetR = 2.0f;

// meters (inside meter[]): the reference's segments, 2 px tall every 5 px from y 225 upwards at x 48 / 86 (input) and
// 905 / 949 (output), segment k lit above -57 + 2.6 k dB (a 50 Hz ramp at 5 dB/s through the reference), are drawn as
// one bar per channel, 10 px wide over the same 112 px column and on the same scale: its top reaches segment k's
// top at k's threshold. The bar falls 48 dB/s (bursts), rises at once, and a held peak shows as a marker above it
inline constexpr int numSegments = 23;
inline constexpr float segBottomY = 225.0f, segPitch = 5.0f, segH = 2.0f, segW = 10.0f;
inline constexpr float segX[2][2] { { 48.0f, 86.0f }, { 905.0f, 949.0f } };
inline float segThresholdDb (int k) { return -57.0f + 2.6f * (float) k; }
inline constexpr float meterTopY = segBottomY - segPitch * (float) (numSegments - 1), meterH = segBottomY + segH - meterTopY;
// the lit height of a bar at db (0 ... meterH): segment k's top at k's threshold, linear in dB between
inline float meterLitPx (float db) { return juce::jlimit (0.0f, meterH, segH + segPitch * (db - segThresholdDb (0)) / 2.6f); }
inline constexpr float meterReleaseDbPerSec = 48.0f;

// the rider panel (opened by ">"): a card over the input section and to its right; the rest of the editor below the
// top bar under black at 89.5 %
inline constexpr Box riderPanel { 7.0f, 37.0f, 215.5f, 361.5f };
inline constexpr float riderKnobX = 179.0f, riderKnobY[3] { 109.0f, 206.0f, 302.0f }, riderKnobR = 23.5f;
inline constexpr float riderLabelY[3] { 145.0f, 242.0f, 338.0f };
inline constexpr float riderDim = 0.895f;

// displays fade in and out linearly over 120 ms when their section is switched (films of the character power)
inline constexpr double fadeMs = 120.0;
}
