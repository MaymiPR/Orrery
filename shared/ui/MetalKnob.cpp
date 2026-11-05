#include "MetalKnob.h"
#include "Theme.h"
#include <cstdint>

using namespace juce;

namespace orrery
{
MetalKnob::MetalKnob (Kind)
{
    setSliderStyle (RotaryVerticalDrag);
    setTextBoxStyle (NoTextBox, false, 0, 0);
    setRotaryParameters (startAngle + MathConstants<float>::twoPi, endAngle + MathConstants<float>::twoPi, true);
    setWantsKeyboardFocus (false);
    setMouseClickGrabsKeyboardFocus (false);
    setPopupMenuEnabled (false);
}

float MetalKnob::designY (const MouseEvent& e) const
{
    return e.position.y * std::abs (getTransform().mat00);    // the knob's own placement transform undone
}

void MetalKnob::mouseDown (const MouseEvent& e)
{
    Slider::mouseDown (e);                       // begins the host gesture; rotary drag modes do not jump on click
    lastY = anchorY = designY (e);
    anchorValue = valueToProportionOfLength (getValue());
    downScreen = e.getScreenPosition().toFloat();
    velocity = false;
    if (e.mods.isAltDown()) setValue (defaultValue, sendNotificationSync);
}

void MetalKnob::mouseDrag (const MouseEvent& e)
{
    if (e.mods.isAltDown()) return;
    const float y = designY (e);
    if (velocityKeys (e.mods))
    {
        const float diff = y - lastY;
        const double speed = jlimit (0.0, 200.0, (double) std::abs (diff));
        if (speed > 0.0)
        {
            double step = 0.2 * (1.0 + std::sin (MathConstants<double>::pi * (1.5 + jmin (0.5, jmax (0.0, speed - 1.0) / 200.0))));
            if (diff > 0.0f) step = -step;                  // up raises the value
            setValue (proportionOfLengthToValue (jlimit (0.0, 1.0, valueToProportionOfLength (getValue()) + step)), sendNotificationSync);
            e.source.enableUnboundedMouseMovement (true, false);
            velocity = true;
        }
    }
    else
    {
        if (velocity) { restoreMouse(); lastY = anchorY; return; }
        setValue (proportionOfLengthToValue (jlimit (0.0, 1.0, anchorValue + (anchorY - y) * 0.01)), sendNotificationSync);
    }
    lastY = y;
}

void MetalKnob::mouseUp (const MouseEvent& e)
{
    if (velocity) restoreMouse();
    Slider::mouseUp (e);
}

void MetalKnob::mouseDoubleClick (const MouseEvent& e)
{
    if (! e.mods.isAltDown()) showValueEntry();
}

void MetalKnob::showValueEntry()
{
    auto* top = getTopLevelComponent();
    if (top == nullptr || entry != nullptr) return;
    // centred on the knob, wide enough for a value with its unit, in the top level's coordinates (the knob may be scaled)
    const auto area = top->getLocalArea (this, getLocalBounds()).toFloat();
    const float k = area.getWidth() / (float) jmax (1, getWidth()) / std::abs (getTransform().mat00);   // top px per design px
    const float w = jmax (area.getWidth() * 1.3f, 64.0f * k), h = 19.0f * k;
    entry = std::make_unique<TextEditor>();
    auto& t = *entry;
    t.setFont (theme::font (12.5f * k));
    t.setJustification (Justification::centred);
    t.setIndents (2, 0);
    t.setColour (TextEditor::backgroundColourId, theme::boxFill.withAlpha (0.96f));
    t.setColour (TextEditor::textColourId, theme::text);
    t.setColour (TextEditor::outlineColourId, theme::boxLine);
    t.setColour (TextEditor::focusedOutlineColourId, theme::mint);
    t.setColour (TextEditor::highlightColourId, theme::mint.withAlpha (0.35f));
    t.setColour (CaretComponent::caretColourId, theme::mint);
    t.setSelectAllWhenFocused (true);
    t.setText (getTextFromValue (getValue()), false);
    t.onReturnKey = [this] { closeValueEntry (true); };
    t.onEscapeKey = [this] { closeValueEntry (false); };
    t.onFocusLost = [this] { closeValueEntry (true); };
    top->addAndMakeVisible (t);
    t.setBounds (Rectangle<float> (w, h).withCentre (area.getCentre()).getSmallestIntegerContainer()
                     .constrainedWithin (top->getLocalBounds()));
    t.grabKeyboardFocus();
    t.selectAll();
}

void MetalKnob::closeValueEntry (bool apply)
{
    if (entry == nullptr) return;
    auto e = std::move (entry);          // (closing changes focus, which calls back here: entry is already gone)
    const auto text = e->getText().trim();
    e->setVisible (false);
    if (auto* p = e->getParentComponent()) p->removeChildComponent (e.get());
    if (! apply || text.isEmpty()) return;
    const double v = getValueFromText (text);
    if (! std::isfinite (v)) return;
    if (onGesture) onGesture (true);
    if (onDragStart) onDragStart();
    setValue (jlimit (getMinimum(), getMaximum(), v), sendNotificationSync);
    if (onDragEnd) onDragEnd();
    if (onGesture) onGesture (false);
}

void MetalKnob::modifierKeysChanged (const ModifierKeys& m)
{
    if (velocity && isMouseButtonDown() && ! velocityKeys (m)) restoreMouse();
    Slider::modifierKeysChanged (m);
}

// as JUCE's slider: the cursor reappears where an absolute drag from the press point would have put it for the
// current value, kept inside the knob, and the drag continues absolutely from there
void MetalKnob::restoreMouse()
{
    velocity = false;
    auto src = Desktop::getInstance().getMainMouseSource();
    src.enableUnboundedMouseMovement (false);
    const double now = valueToProportionOfLength (getValue());
    const float screenPerDesign = getScreenBounds().toFloat().getHeight() / ((float) getHeight() * std::abs (getTransform().mat00));
    auto pos = downScreen.translated (0.0f, (float) ((anchorValue - now) * 100.0) * screenPerDesign);
    pos = getScreenBounds().reduced (4).toFloat().getConstrainedPoint (pos);
    src.setScreenPosition (pos);
    anchorY = getLocalPoint (nullptr, pos).y * std::abs (getTransform().mat00);
    anchorValue = now;
    downScreen = pos;
}

void MetalKnob::paint (Graphics& g)
{
    const auto b = getLocalBounds().toFloat();
    const float p = (float) valueToProportionOfLength (getValue());
    const float angle = startAngle + p * (endAngle - startAngle);
    const float from = startAngle + arcOrigin * (endAngle - startAngle);
    theme::drawKnob (g, b, angle, startAngle, endAngle, from, isEnabled());
}
}
