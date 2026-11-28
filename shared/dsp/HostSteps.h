#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

// A float parameter of whole steps (its range has an interval) that tells a VST3 host its step count, as the
// references' VST3s do (each plug-in's nulltest/paramdump.txt: 2 steps for a switch, 101 for Wraith's Compression and
// Focus). Only a VST3 host is told: an AU scales a discrete parameter by its steps and not from 0 to 1, which would
// move the automation a saved project holds, and the references were measured as VST3s. The values, the range a host
// automates and the state are those of a plain float parameter.
namespace orrery
{
struct HostSteps final : juce::AudioParameterFloat
{
    using juce::AudioParameterFloat::AudioParameterFloat;
    bool isDiscrete() const override { return juce::PluginHostType::getPluginLoadedAs() == juce::AudioProcessor::wrapperType_VST3; }
    int getNumSteps() const override { return isDiscrete() ? juce::RangedAudioParameter::getNumSteps() : juce::AudioProcessor::getDefaultNumParameterSteps(); }
};
}
