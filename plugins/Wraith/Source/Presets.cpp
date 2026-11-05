#include "Presets.h"
#include "Params.h"

using namespace juce;

namespace wr
{
namespace
{
struct Factory { const char* name; std::vector<std::pair<const char*, float>> values; };

// the reference's factory presets in its menu's order, read from its own saved states (nulltest/read_presets.py,
// MEASUREMENTS.md "Presets"): each lists the values that differ from the host defaults, exact where the reference stores
// more digits than it shows
const std::vector<Factory>& factory()
{
    static const std::vector<Factory> f {
        { "backing stack", { { id::focus, 8.0f }, { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::eqLow, -5.0385f }, { id::doublerOn, 1.0f }, { id::doublerMix, 0.2075f }, { id::doublerStereo, 0.3211f }, { id::reverbOn, 1.0f }, { id::reverbMix, 0.3603f }, { id::reverbFilter, 9845.186f }, { id::reverbType, 1.0f } } },
        { "big cave", { { id::focus, 3.0f }, { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::eqLow, -2.0122f }, { id::eqHigh, 1.0744f }, { id::doublerOn, 1.0f }, { id::doublerMix, 0.4344f }, { id::doublerStereo, 0.6166f }, { id::reverbOn, 1.0f }, { id::reverbMix, 0.2818f }, { id::reverbFilter, 5206.4943f }, { id::reverbType, 1.0f } } },
        { "doubler alone", { { id::outputGain, -3.0315f }, { id::doublerOn, 1.0f }, { id::doublerMix, 1.0f }, { id::doublerStereo, 0.7499f }, { id::reverbType, 1.0f } } },
        { "soft room", { { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::eqLow, -1.6137f }, { id::eqHigh, 3.0079f }, { id::reverbOn, 1.0f }, { id::reverbMix, 0.0778f }, { id::reverbFilter, 5037.8924f } } },
        { "hard squeeze", { { id::outputGain, -3.0315f }, { id::riderOn, 1.0f }, { id::riderAmount, 0.9657f }, { id::riderSpeed, 0.002f }, { id::compression, 50.0f }, { id::focus, 50.0f }, { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::eqLow, -2.0122f }, { id::eqHigh, 1.8863f }, { id::reverbType, 1.0f } } },
        { "lead", { { id::focus, 8.0f }, { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::eqLow, 4.0975f }, { id::eqHigh, 0.0336f }, { id::doublerStereo, 1.0f }, { id::reverbOn, 1.0f }, { id::reverbMix, 0.0791f }, { id::reverbFilter, 9845.186f } } },
        { "up front", { { id::focus, 3.0f }, { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::eqLow, -2.9647f }, { id::eqHigh, 3.4729f } } },
        { "wide image", { { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::eqLow, 1.4591f }, { id::eqHigh, 3.0079f }, { id::doublerOn, 1.0f }, { id::doublerMix, 0.5762f }, { id::doublerStereo, 0.7928f } } },
        { "short phase", { { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::eqLow, -2.2376f }, { id::eqHigh, 3.2332f }, { id::doublerOn, 1.0f }, { id::doublerMix, 1.0f }, { id::doublerStereo, 0.0425f } } },
        { "wide and wet", { { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::doublerOn, 1.0f }, { id::doublerMix, 0.350100027f }, { id::doublerStereo, 0.710500002f }, { id::reverbOn, 1.0f }, { id::reverbMix, 0.453999985f }, { id::reverbFilter, 11424.8064f }, { id::reverbType, 1.0f } } },
        { "wide lead", { { id::characterOn, 1.0f }, { id::eqOn, 1.0f }, { id::doublerOn, 1.0f }, { id::doublerMix, 0.2075f }, { id::doublerStereo, 0.3211f }, { id::reverbOn, 1.0f }, { id::reverbFilter, 11941.385f }, { id::reverbType, 1.0f } } },
    };
    return f;
}
}

File PresetManager::userFolder()
{
    return File::getSpecialLocation (File::userDocumentsDirectory).getChildFile ("Wraith").getChildFile ("Presets");
}

std::vector<PresetManager::Entry> PresetManager::list() const
{
    std::vector<Entry> out;
    for (auto& f : factory()) out.push_back ({ f.name, true, {} });
    auto files = userFolder().findChildFiles (File::findFiles, false, "*.wraith");
    files.sort();
    for (auto& f : files) out.push_back ({ f.getFileNameWithoutExtension(), false, f });
    return out;
}

void PresetManager::load (const Entry& e)
{
    if (e.factory)
    {
        for (auto* pid : presetIds)
            if (auto* p = apvts.getParameter (pid)) p->setValueNotifyingHost (p->getDefaultValue());
        for (auto& f : factory())
            if (e.name == f.name)
                for (auto& [pid, value] : f.values)
                    if (auto* p = dynamic_cast<RangedAudioParameter*> (apvts.getParameter (pid)))
                        p->setValueNotifyingHost (p->convertTo0to1 (value));
    }
    else
    {
        auto xml = parseXML (e.file);
        if (xml == nullptr || ! xml->hasTagName ("WraithPreset")) return;
        for (auto* pid : presetIds)
            if (auto* p = dynamic_cast<RangedAudioParameter*> (apvts.getParameter (pid)))
                if (xml->hasAttribute (pid))
                    p->setValueNotifyingHost (p->convertTo0to1 ((float) xml->getDoubleAttribute (pid)));
    }
    current = e.name;
}

void PresetManager::step (int delta)
{
    const auto all = list();
    int i = 0;
    for (int k = 0; k < (int) all.size(); ++k)
        if (all[(size_t) k].name == current) i = k;
    i = (i + delta + (int) all.size()) % (int) all.size();
    load (all[(size_t) i]);
}

bool PresetManager::save (const String& name)
{
    if (name.trim().isEmpty()) return false;
    XmlElement xml ("WraithPreset");
    for (auto* pid : presetIds)
        if (auto* p = dynamic_cast<RangedAudioParameter*> (apvts.getParameter (pid)))
            xml.setAttribute (pid, (double) p->convertFrom0to1 (p->getValue()));
    const auto f = fileFor (name.trim());
    if (! f.getParentDirectory().createDirectory() || ! xml.writeTo (f)) return false;
    current = name.trim();
    return true;
}
}
