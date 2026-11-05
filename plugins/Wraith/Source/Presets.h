#pragma once
#include <juce_audio_processors/juce_audio_processors.h>

// Presets as the references have them: factory presets (our names for the reference's factory presets, each
// nulled from its own state) and user presets saved by name as .wraith files. A preset holds every
// parameter but the host's bypass (Params.h presetIds).
namespace wr
{
class PresetManager
{
public:
    explicit PresetManager (juce::AudioProcessorValueTreeState& s) : apvts (s) {}

    struct Entry { juce::String name; bool factory; juce::File file; };

    static juce::File userFolder();                      // Documents/Wraith/Presets
    std::vector<Entry> list() const;                     // factory first, then user presets by name
    juce::String currentName() const { return current; }
    void setCurrentName (const juce::String& n) { current = n; }

    void load (const Entry&);
    void step (int delta);                               // the arrows: previous / next in list(), wrapping
    bool save (const juce::String& name);                // writes userFolder()/name.wraith; false on failure
    bool exists (const juce::String& name) const { return fileFor (name).existsAsFile(); }

private:
    juce::File fileFor (const juce::String& name) const { return userFolder().getChildFile (juce::File::createLegalFileName (name) + ".wraith"); }
    juce::AudioProcessorValueTreeState& apvts;
    juce::String current { "lead" };
};
}
