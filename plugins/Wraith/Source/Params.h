#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

// Host parameters, identical to the reference's list (names, order, ranges, tapers, defaults and display text:
// RESEARCH.md "Controls", built from ParamDump), plus Reverb Type (room / plate), which the reference keeps in its
// preset only (as Scorpius does with Comp Mode). The IDs are ours, camelCase, and never change once released (saved
// projects find parameters by them); the names are what hosts show, spelled as the reference spells them.
namespace wr
{
namespace id
{
inline constexpr const char* inputGain = "inputGain";
inline constexpr const char* riderSpeed = "riderSpeed";
inline constexpr const char* riderAmount = "riderAmount";
inline constexpr const char* riderFloor = "riderFloor";
inline constexpr const char* riderOn = "riderOn";
inline constexpr const char* compression = "compression";
inline constexpr const char* focus = "focus";
inline constexpr const char* characterOn = "characterOn";
inline constexpr const char* eqLow = "eqLow";
inline constexpr const char* eqHigh = "eqHigh";
inline constexpr const char* eqOn = "eqOn";
inline constexpr const char* doublerStereo = "doublerStereo";
inline constexpr const char* doublerMix = "doublerMix";
inline constexpr const char* doublerOn = "doublerOn";
inline constexpr const char* reverbFilter = "reverbFilter";
inline constexpr const char* reverbMix = "reverbMix";
inline constexpr const char* reverbOn = "reverbOn";
inline constexpr const char* outputGain = "outputGain";
inline constexpr const char* bypass = "bypass";              // host bypass, Off / On
inline constexpr const char* reverbType = "reverbType";      // room / plate
}

// the parameters in the order the processor caches them (PluginProcessor.cpp raw[]); the index names below follow it
inline constexpr const char* const allIds[] { id::inputGain, id::riderSpeed, id::riderAmount, id::riderFloor, id::riderOn,
                                              id::compression, id::focus, id::characterOn, id::eqLow, id::eqHigh, id::eqOn,
                                              id::doublerStereo, id::doublerMix, id::doublerOn, id::reverbFilter, id::reverbMix,
                                              id::reverbOn, id::outputGain, id::bypass, id::reverbType };
inline constexpr int numParams = (int) (sizeof (allIds) / sizeof (allIds[0]));
enum Index { iInputGain, iRiderSpeed, iRiderAmount, iRiderFloor, iRiderOn, iCompression, iFocus, iCharacterOn, iEqLow,
             iEqHigh, iEqOn, iDoublerStereo, iDoublerMix, iDoublerOn, iReverbFilter, iReverbMix, iReverbOn, iOutputGain,
             iBypass, iReverbType };

// what a preset stores: every parameter but the host's bypass (as the reference does)
inline constexpr const char* const presetIds[] { id::inputGain, id::riderSpeed, id::riderAmount, id::riderFloor, id::riderOn,
                                                 id::compression, id::focus, id::characterOn, id::eqLow, id::eqHigh, id::eqOn,
                                                 id::doublerStereo, id::doublerMix, id::doublerOn, id::reverbFilter, id::reverbMix,
                                                 id::reverbOn, id::outputGain, id::reverbType };

// Both Mix controls: value = n / (4 - 3 n) for the normalised position n (exact at every ParamDump point).
inline float mixFromNorm (float n) { return n / (4.0f - 3.0f * n); }
inline float mixToNorm (float v) { return 4.0f * v / (1.0f + 3.0f * v); }

// Reverb Filter: ParamDump's 41 points (Hz at n = 0, 1/40, ... 1), linear between them.
inline constexpr float reverbFilterTaper[41] { 2000.0f, 2230.2f, 2466.24f, 2708.34f, 2956.74f, 3211.69f, 3473.46f, 3742.32f,
    4018.55f, 4302.48f, 4594.42f, 4894.72f, 5203.75f, 5521.89f, 5849.54f, 6187.15f, 6535.17f, 6894.09f, 7264.44f, 7646.76f,
    8041.65f, 8449.73f, 8871.69f, 9308.23f, 9760.14f, 10228.2f, 10713.4f, 11216.6f, 11738.8f, 12281.2f, 12844.9f, 13431.2f,
    14041.5f, 14677.3f, 15340.3f, 16032.2f, 16755.0f, 17510.8f, 18301.8f, 19130.6f, 20000.0f };
float filterFromNorm (float n);
float filterToNorm (float hz);

// Display text as the reference prints it: three decimals, no unit (ParamDump).
inline juce::String threeDecimals (float v, int) { return juce::String (v, 3); }

juce::AudioProcessorValueTreeState::ParameterLayout createLayout();
}
