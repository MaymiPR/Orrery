#pragma once
#include <juce_gui_basics/juce_gui_basics.h>

// The static faceplate behind the controls, in the suite's own look (shared/ui/Theme.h): true black behind, six plates
// as violet-black cards (input and output a step up from the four in the middle), their slots, holes, knob wells and
// meter wells as wells, a small rivet in each plate's corner, the section labels, and the side strip with the name
// and the mark. The shapes sit at their measured positions and sizes (ui/Look.h).
namespace wr::ui
{
// renders the faceplate below the top bar (design y 30 ... 406) into an RGB image of (1044 x 376) x dpx pixels
juce::Image renderFaceplate (float dpx);

// the suite's mark (the top bar's logo, shared/ui/Widgets.cpp) centred at c, its orbit's radius r
void paintMark (juce::Graphics&, juce::Point<float> c, float r);
}
