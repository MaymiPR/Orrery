#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "PluginProcessor.h"
#include "shared/ui/Theme.h"
#include "shared/ui/Widgets.h"
#include "shared/ui/HostFocus.h"
#include "ui/Theme.h"
#include "ui/Controls.h"
#include "ui/Displays.h"

// The editor is laid out in the reference's design pixels (1044 x 406 at 100 %) and scaled as a whole: by the UI
// Scale menu (50 ... 200 %, remembered in the state) or by dragging the bottom-right corner (the proportions stay).
// Every child is placed in design pixels on `content`; only `content` carries the scale transform.
class WraithEditor : public juce::AudioProcessorEditor,
                      private juce::Timer,
                      private juce::AudioProcessorValueTreeState::Listener
{
public:
    explicit WraithEditor (WraithProcessor&);
    ~WraithEditor() override;

    void resized() override;
    void setUiScale (float);

    static constexpr float designW = wr::look::designW, designH = wr::look::designH;
    static constexpr float scales[] { 0.5f, 0.75f, 1.0f, 1.25f, 1.5f, 2.0f };

    // snapshot tool: freeze the meters at given levels (dB; below -100 = silence)
    void setTestLevels (float inDb, float outDb, float inBarDb, float outBarDb);
    // snapshot tool: the design-pixel component under a point, and the content component (for simulated mouse events)
    juce::Component* componentAtDesign (juce::Point<float>);
    juce::Component& contentComponent() { return content; }

private:
    class Content : public juce::Component
    {
    public:
        explicit Content (WraithEditor& e) : ed (e) {}
        void paint (juce::Graphics&) override;
        void mouseDown (const juce::MouseEvent&) override;
        WraithEditor& ed;
    };

    // the rider panel: over everything below the top bar but the input section, which stays as it is
    class RiderPanel : public juce::Component
    {
    public:
        explicit RiderPanel (WraithEditor& e) : ed (e) {}
        void paint (juce::Graphics&) override;
        bool hitTest (int x, int y) override;
        void mouseDown (const juce::MouseEvent&) override;
        WraithEditor& ed;
    };

    void timerCallback() override;
    void parameterChanged (const juce::String&, float) override;
    void updateFromParams();
    void toggleParam (const char* pid);
    void setRiderPanel (bool open);
    void showPresetList();
    void showScaleList();
    void closePopups();
    void showSavePreset();
    void showAboutMenu();
    void showDialog (std::unique_ptr<juce::Component>);
    void paintTopBar (juce::Graphics&);
    void paintCaptions (juce::Graphics&);
    juce::String caption (const wr::ui::Knob&) const;
    void drawCharacter (juce::Graphics&);
    void drawEq (juce::Graphics&);
    void drawDoubler (juce::Graphics&);
    void drawReverb (juce::Graphics&);
    void stepMeters (float dt);
    float param (const char* pid) const { return proc.apvts.getRawParameterValue (pid)->load(); }

    WraithProcessor& proc;
    Content content { *this };
    float scale = 1.0f;

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

    // top bar (the suite's shared controls)
    orrery::Logo logo;
    orrery::DropBox presetBox, scaleBox;
    orrery::IconButton prevButton { orrery::IconButton::Icon::left }, nextButton { orrery::IconButton::Icon::right },
        saveButton { orrery::IconButton::Icon::save };
    // ours, as the suite's other plug-ins: Compare A -> B, the side-chain switch and the I/O link
    orrery::CompareToggle compare;
    orrery::SegmentToggle sidechain;
    orrery::LinkButton ioLinkButton;
    orrery::Toast toast;

    // I/O link: while linked the output gain is always the input gain's opposite. A gesture on either knob moves the
    // other (as one host gesture each); changes from the host are mirrored too
    void beginLink (juce::Slider&);
    void endLink (juce::Slider&);
    void mirror (bool fromInput);
    juce::Slider* linkSource = nullptr;
    bool mirroring = false;

    // sections
    wr::ui::PowerPill power[4];                 // character, eq, doubler, reverb
    wr::ui::SectionDisplay displays[4];
    wr::ui::RiderPill riderPill;
    wr::ui::RoomPlate roomPlate;
    wr::ui::LevelMeter inMeter { true }, outMeter { false };
    using Kind = wr::ui::Knob::Kind;
    wr::ui::Knob compression { Kind::groove }, focus { Kind::groove }, eqHigh { Kind::groove }, eqLow { Kind::groove },
        stereo { Kind::groove }, doublerMix { Kind::groove }, filter { Kind::groove }, reverbMix { Kind::groove },
        inGain { Kind::gain }, outGain { Kind::gain }, riderSpeed { Kind::rider }, riderAmount { Kind::rider }, riderFloor { Kind::rider };
    RiderPanel riderPanel { *this };
    bool riderOpen = false;
    // the two knobs of a switchable section (0 character, 1 eq, 2 doubler, 3 reverb)
    std::array<wr::ui::Knob*, 2> sectionKnobs (int i)
    {
        switch (i)
        {
            case 0: return { &compression, &focus };
            case 1: return { &eqHigh, &eqLow };
            case 2: return { &stereo, &doublerMix };
            default: return { &filter, &reverbMix };
        }
    }
    bool sectionOn (const wr::ui::Knob& k) const
    {
        const char* pid = (&k == &compression || &k == &focus) ? wr::id::characterOn : (&k == &eqHigh || &k == &eqLow) ? wr::id::eqOn
                        : (&k == &stereo || &k == &doublerMix) ? wr::id::doublerOn : (&k == &filter || &k == &reverbMix) ? wr::id::reverbOn : nullptr;
        return pid == nullptr || param (pid) >= 0.5f;
    }

    std::vector<std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment>> attachments;
    std::unique_ptr<orrery::DropList> dropList;
    std::unique_ptr<juce::Component> dialog;
    std::unique_ptr<orrery::HostFocus> hostFocus;      // the host's keys after a click (FL Studio)

    // a knob's label shows its value while the mouse is over it or drags it (as the reference)
    struct HoverTracker : juce::MouseListener
    {
        explicit HoverTracker (WraithEditor& e) : ed (e) {}
        void mouseMove (const juce::MouseEvent&) override { ed.updateHover(); }
        void mouseEnter (const juce::MouseEvent&) override { ed.updateHover(); }
        void mouseExit (const juce::MouseEvent&) override { ed.updateHover(); }
        void mouseDrag (const juce::MouseEvent&) override { ed.updateHover(); }
        void mouseUp (const juce::MouseEvent&) override { ed.updateHover(); }
        void mouseDown (const juce::MouseEvent& e) override { ed.clickedAnywhere (e); }
        WraithEditor& ed;
    } hoverTracker { *this };
    void clickedAnywhere (const juce::MouseEvent&);
    void updateHover();
    const wr::ui::Knob* hovered = nullptr;

    // meters (display side: dB)
    float barDb[4] { -200.0f, -200.0f, -200.0f, -200.0f }, holdDb[4] { -200.0f, -200.0f, -200.0f, -200.0f };
    float barHold[4] {};
    float targetFill = 0.0f, riderDb = 0.0f;
    float barPx = 0.0f, basePx = 0.0f;       // the character display's compression bar and base, design px down from rest
    bool barFell = false, barRising = false;
    float revMorph = -1.0f;                  // the reverb triangle between room (0) and plate (1); -1 until first shown
    float peakSinceFall = 0.0f;
    std::pair<double, float> barDelay[6] {};
    int barDelayPos = 0;
    void stepCompressionBars (float dt);
    float lastMeanSquare = 0.0f, slowMeanSquare = 0.0f;
    float noBlockSeconds = 0.0f;
    double lastTick = 0.0;
    bool frozen = false, animate = false;

    juce::Image faceplate;
    float faceplateScale = 0.0f;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (WraithEditor)
};
