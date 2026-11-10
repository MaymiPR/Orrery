#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include <optional>
#include "PluginProcessor.h"
#include "shared/ui/MetalKnob.h"
#include "ui/Visualizer.h"
#include "shared/ui/Widgets.h"
#include "shared/ui/HostFocus.h"

// The editor is laid out in the reference's design pixels (888 x 359.5 at 100 %) and scaled as a whole by the
// UI Scale menu (50 ... 200 %), or freely by dragging its bottom-right corner (ours; the proportions stay).
class PositronEditor : public juce::AudioProcessorEditor,
                             public orrery::SnapshotHooks,
                             private juce::Timer,
                             private juce::ChangeListener,
                             private juce::AudioProcessorValueTreeState::Listener
{
public:
    explicit PositronEditor (PositronProcessor&);
    ~PositronEditor() override;

    void resized() override;
    void setUiScale (float);

    static constexpr float designW = 888.0f, designH = 359.5f;
    static constexpr float scales[] { 0.5f, 0.75f, 0.85f, 1.0f, 1.25f, 1.5f, 2.0f };

    // snapshot tool: freeze meters and visualiser to a given state
    void setTestLevels (float inDb, float outDb, bool audio);
    // the suite's snapshot tool (tools/Snapshot.cpp): --levels, and the options --audio (the particles as for that
    // input level), --ext (the side-chain source external), --anti or --classic (the particle style, for this run only)
    void setTestLevels (float inDb, float outDb) override;
    bool snapshotOption (const juce::String&) override;

private:
    struct Meter                                     // one channel of an I/O meter as drawn
    {
        float peakHoldDb = -200.0f;                         // peak readout (held until clicked)
        float rmsDb = -200.0f, rmsMeanSquare = 0.0f;        // RMS readout (live) and the mean square it shows
        float lufsDb = -200.0f, lufsMeanSquare = 0.0f;      // the same box in LUFS mode: short-term loudness
        float lufsStopMeanSquare = 0.0f;                    //   (what it showed when the host stopped calling)
        float barDb = -200.0f;                              // the bar's solid part (RMS, 150 ms)
        float fastDb = -200.0f;                             // top of its lighter run (fast peak); drives the input target
        float rawPeakDb = -200.0f;                          // this frame's sample peak (is audio playing?)
    };
    class Content : public juce::Component
    {
    public:
        explicit Content (PositronEditor& e) : ed (e) {}
        void paint (juce::Graphics&) override;
        void mouseDown (const juce::MouseEvent&) override;
        PositronEditor& ed;
    };

    void timerCallback() override;
    void changeListenerCallback (juce::ChangeBroadcaster*) override;
    void parameterChanged (const juce::String&, float) override;
    void updateFromParams();
    void showPresetList();
    void showScaleList();
    void closePopups();
    void showSettings();
    void showSavePreset();
    void showAboutMenu();
    void showDialog (std::unique_ptr<orrery::Dialog>);
    void updateMeter (Meter&, po::LevelTap&);
    void sampleReadouts();

    // the I/O readouts update on the reference's own clock (MEASUREMENTS.md 6), apart from the 30 Hz repaint: every
    // 46 ms the peak readout takes the latest block's peak, every fifth time the RMS readout takes the mean square
    struct ReadoutClock : juce::Timer
    {
        explicit ReadoutClock (PositronEditor& e) : ed (e) {}
        void timerCallback() override { ed.sampleReadouts(); }
        PositronEditor& ed;
    } readoutClock { *this };
    int readoutTicks = 0, readoutBlocks = 0, loudnessTicks = 0;

    void paintTopBar (juce::Graphics&);
    void paintPanel (juce::Graphics&);
    void paintPlate (juce::Graphics&);
    void paintIoMeter (juce::Graphics&, float x0, const Meter (&m)[2], bool target);
    void paintGainReduction (juce::Graphics&);
    void paintLimiter (juce::Graphics&);
    void paintAmountText (juce::Graphics&);

    // a knob's caption shows its value (as the reference: "%.1f dB") while the mouse is over the knob's cell or the
    // knob is being dragged
    struct HoverTracker : juce::MouseListener
    {
        explicit HoverTracker (PositronEditor& e) : ed (e) {}
        void mouseMove (const juce::MouseEvent& e) override { ed.updateReadout (e, false); }
        void mouseEnter (const juce::MouseEvent& e) override { ed.updateReadout (e, false); }
        void mouseExit (const juce::MouseEvent& e) override { ed.updateReadout (e, false); }
        void mouseDrag (const juce::MouseEvent& e) override { ed.updateReadout (e, false); }
        void mouseUp (const juce::MouseEvent& e) override { ed.updateReadout (e, true); }
        PositronEditor& ed;
    } hoverTracker { *this };
    void updateReadout (const juce::MouseEvent&, bool released);
    juce::String captionText (const orrery::MetalKnob&, const char* name) const;
    const orrery::MetalKnob* readoutKnob = nullptr;

    // I/O link (ours): while linked the output gain is always the input gain's opposite. A gesture on either knob
    // moves the other (as one host gesture each); changes from the host are mirrored too
    void beginLink (orrery::MetalKnob&);
    void endLink (orrery::MetalKnob&);
    void mirror (bool fromInput);
    orrery::MetalKnob* linkSource = nullptr;
    bool mirroring = false;

    PositronProcessor& proc;
    Content content { *this };
    float scale = 1.0f;
    // resizing from the bottom-right corner: proportions fixed, 50 ... 200 %; the grip is drawn as grooves in the plate
    struct Grip : juce::ResizableCornerComponent
    {
        Grip (juce::Component* c, juce::ComponentBoundsConstrainer* k) : juce::ResizableCornerComponent (c, k) { setRepaintsOnMouseActivity (true); }
        void paint (juce::Graphics&) override;
        void mouseUp (const juce::MouseEvent&) override;
    };
    juce::ComponentBoundsConstrainer constrainer;
    std::unique_ptr<Grip> grip;
    juce::uint32 lastResizeMs = 0;
    void endLiveResize();

    orrery::Logo logo;
    orrery::DropBox presetBox, scaleBox;
    orrery::IconButton prevButton { orrery::IconButton::Icon::left }, nextButton { orrery::IconButton::Icon::right },
        saveButton { orrery::IconButton::Icon::save };
    orrery::SegmentToggle sidechain;
    orrery::GearButton gear;

    orrery::PowerButton eqPower, amountPower, limiterPower;
    orrery::MetalKnob eqHigh { orrery::MetalKnob::Kind::small }, eqMid { orrery::MetalKnob::Kind::small }, eqLow { orrery::MetalKnob::Kind::small };
    orrery::MetalKnob amount { orrery::MetalKnob::Kind::large };
    orrery::MetalKnob inputKnob { orrery::MetalKnob::Kind::plate }, limiterKnob { orrery::MetalKnob::Kind::plate },
        outputKnob { orrery::MetalKnob::Kind::plate };
    po::Visualizer visualizer;
    orrery::LinkButton ioLinkButton;
    orrery::CompareToggle compare;         // ours (as Scorpius's reference has it): A / B settings, left of the preset menu
    orrery::Toast toast;                   // "A copied to B.", over the plate
    struct PaintOverlay : juce::Component
    {
        std::function<void (juce::Graphics&)> paintFn;
        void paint (juce::Graphics& g) override { if (paintFn) paintFn (g); }
    } amountText;
    std::vector<std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment>> attachments;

    std::unique_ptr<orrery::DropList> dropList;
    std::unique_ptr<juce::Component> dialog;
    std::unique_ptr<orrery::HostFocus> hostFocus;      // the host's keys after a click (FL Studio)
    bool snapshotAudio = false;                         // snapshot tool: --audio
    std::optional<po::Settings::Particles> snapshotStyle;   // the global style a snapshot run changed, put back on close

    Meter inMeter[2], outMeter[2];
    float bandGrDb[3] {}, limGrDb[2] {};                     // now (the bars)
    float bandGrHold[3] {}, limGrHold[2] {};                 // deepest since the last click (the readouts)
    bool eqOn = true, characterOn = true, limiterOn = true;
    float characterValue = 0.5f;
    bool frozen = false;
    juce::Image knobShadow;               // plate knobs' shadow, per physical scale
    float knobShadowScale = 0.0f;
    int lastBlocks = 0;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (PositronEditor)
};
