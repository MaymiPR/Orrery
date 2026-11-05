#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <atomic>
#include "Params.h"
#include "Presets.h"
#include "dsp/Engine.h"

namespace wr
{
// Levels the editor reads (audio thread writes, message thread reads and resets): the highest sample since the
// editor last took it. Phase 2 extends it with what the reference's meters show (RMS, fast peak, held peak).
struct LevelTap
{
    std::atomic<float> peak { 0.0f };
    void push (float blockPeak)
    {
        float p = peak.load();
        while (blockPeak > p && ! peak.compare_exchange_weak (p, blockPeak)) {}
    }
    float take() { return peak.exchange (0.0f); }
};

// ---- editor hook (Phase 2 round 2): the mean square the character display's compression bars read ----------------
// What the character section's detector hears (the input, or the side-chain when EXT is on and connected), as a
// sum of squares and a sample count since the editor last took them. Audio thread: push() once per block, lock-free,
// no allocation; message thread: take() returns the mean square (-1 when no block came) and starts again. Only reads.
struct MeanSquareTap
{
    std::atomic<double> sum { 0.0 };
    std::atomic<int> count { 0 };
    void push (double blockSumOfSquares, int samples)
    {
        double s = sum.load();
        while (! sum.compare_exchange_weak (s, s + blockSumOfSquares)) {}
        count.fetch_add (samples);
    }
    float take()
    {
        const int n = count.exchange (0);
        const double s = sum.exchange (0.0);
        return n > 0 ? (float) (s / (double) n) : -1.0f;
    }
};
}

class WraithProcessor : public juce::AudioProcessor
{
public:
    WraithProcessor();
    ~WraithProcessor() override = default;

    void prepareToPlay (double, int) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported (const BusesLayout&) const override;
    void processBlock (juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    using juce::AudioProcessor::processBlock;       // (the double version stays the base class's)
    juce::AudioProcessorParameter* getBypassParameter() const override { return bypassParam; }

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }
    const juce::String getName() const override { return JucePlugin_Name; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    double getTailLengthSeconds() const override { return 0.0; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram (int) override {}
    const juce::String getProgramName (int) override { return {}; }
    void changeProgramName (int, const juce::String&) override {}
    void getStateInformation (juce::MemoryBlock&) override;
    void setStateInformation (const void*, int) override;

    juce::AudioProcessorValueTreeState apvts;
    wr::PresetManager presets { apvts };

    // Compare A -> B (ours, as the suite's other plug-ins; the reference has none): two complete settings in one
    // instance. The active one lives in the parameters, the other is kept here. Switching stores the active one and
    // loads the other; copyCompareSlot() copies the active one over the other. A setting never used yet starts as a
    // copy of the one in use when it is first selected.
    int compareSlot() const { return slot; }
    void selectCompareSlot (int);
    void copyCompareSlot();

    // host-only state (saved with the session, not part of presets): the editor's zoom
    std::atomic<float> uiScale { 1.0f };
    std::atomic<bool> ioLink { false };      // I/O link (ours): the output gain mirrors the input gain
    // Sidechain INT / EXT (ours; the reference has no side-chain): EXT takes the character section's detector (its
    // expander and compressor) from the side-chain bus; with the bus not connected it keeps listening to the input
    std::atomic<bool> sidechainExternal { false };
    std::atomic<float> hostBpm { 0.0f };     // the project's tempo, as the host last gave it (0: it gives none)

    // meters: input and output L R
    wr::LevelTap inL, inR, outL, outR;
    wr::MeanSquareTap detectorIn;           // editor hook: what the character section hears (see MeanSquareTap)
    std::atomic<int> blocksProcessed { 0 };

private:
    juce::ValueTree captureSlot() const;
    void applySlot (const juce::ValueTree&);
    juce::ValueTree slots[2];
    bool slotUsed[2] { true, false };
    int slot = 0;
    juce::AudioProcessorParameter* bypassParam = nullptr;
    std::atomic<float>* raw[wr::numParams] {};    // every parameter's current value, in wr::allIds order
    wr::dsp::Engine engine;
    double preparedRate = 0.0;
    int preparedBlock = 0;
    static void measure (const juce::AudioBuffer<float>&, wr::LevelTap&, wr::LevelTap&);

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (WraithProcessor)
};
