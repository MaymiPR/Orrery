// Renders Wraith's editor to a PNG for the visual comparison with the reference (ui_overlay.py):
//   WraithSnapshot out.png [--scale=1.5] [--size=W] [paramID=value ...] [--preset=name] [--levels=inDb,outDb[,inBarDb,outBarDb]]
//                   [--click=x,y[,alt|shift|ctrl|dbl]] [--drag=x,y,dx,dy[,shift]] [--hover=x,y] ...
// --size resizes the open editor to W px wide as a host or the corner grip would (the constrainer keeps the
// proportions). Parameter values are in real units (dB, 0 ... 1, Hz; reverbType 0 room, 1 plate); --levels
// freezes the meters. --click / --drag / --hover send mouse events to the component under a design-pixel point (in
// the order given, before the picture is taken) and print every parameter after each, for the behaviour checklist.
#include <juce_audio_processors/juce_audio_processors.h>
#include "../Source/PluginProcessor.h"
#include "../Source/PluginEditor.h"
#include <iostream>

namespace
{
void dump (juce::AudioProcessor& p, const juce::String& what)
{
    std::cout << what << ":";
    for (auto* prm : p.getParameters())
        if (auto* r = dynamic_cast<juce::RangedAudioParameter*> (prm))
            std::cout << " [" << r->getName (32) << "=" << juce::String (r->convertFrom0to1 (r->getValue()), 3) << "]";
    std::cout << std::endl;
}

// a mouse event at a design point for the component under it
struct Mouse
{
    WraithEditor& ed;
    juce::Component* target = nullptr;
    juce::Point<float> down;
    juce::MouseEvent make (juce::Point<float> designPos, juce::ModifierKeys mods, int clicks, bool dragged) const
    {
        auto& src = juce::Desktop::getInstance().getMainMouseSource();
        auto& content = ed.contentComponent();
        const auto local = target->getLocalPoint (&content, designPos);
        const auto downLocal = target->getLocalPoint (&content, down);
        const auto now = juce::Time::getCurrentTime();
        return juce::MouseEvent (src, local, mods, juce::MouseInputSource::defaultPressure, 0.0f, 0.0f, 0.0f, 0.0f, target, target,
                                 now, downLocal, now, clicks, dragged);
    }
    bool at (juce::Point<float> p)
    {
        down = p;
        target = ed.componentAtDesign (p);
        if (target == nullptr) { std::cout << "nothing at " << p.toString() << std::endl; return false; }
        return true;
    }
};
}

int main (int argc, char** argv)
{
    if (argc < 2) { std::cerr << "usage: WraithSnapshot out.png [--scale=1.5] [--size=W] [paramID=value ...] [--levels=inDb,outDb] [--click=x,y]\n"; return 2; }
    juce::ScopedJuceInitialiser_GUI init;
    auto proc = std::make_unique<WraithProcessor>();
    float scale = 1.0f, inDb = -200.0f, outDb = -200.0f, inBar = -200.0f, outBar = -200.0f;
    int sizeW = 0;
    bool levels = false;
    for (int i = 2; i < argc; ++i)
    {
        const juce::String a (argv[i]);
        const auto value = a.fromFirstOccurrenceOf ("=", false, false);
        if (a.startsWith ("--scale=")) { scale = value.getFloatValue(); continue; }
        if (a.startsWith ("--size=")) { sizeW = value.getIntValue(); continue; }
        if (a.startsWith ("--levels="))
        {
            inDb = value.upToFirstOccurrenceOf (",", false, false).getFloatValue();
            const auto v = juce::StringArray::fromTokens (value, ",", "");
            outDb = v[1].getFloatValue();
            inBar = v.size() > 2 ? v[2].getFloatValue() : inDb;
            outBar = v.size() > 3 ? v[3].getFloatValue() : outDb;
            levels = true;
            continue;
        }
        if (a.startsWith ("--preset="))
        {
            for (auto& e : proc->presets.list()) if (e.name == value) proc->presets.load (e);
            continue;
        }
        if (a.startsWith ("--")) continue;
        for (auto* p : proc->getParameters())
            if (auto* r = dynamic_cast<juce::RangedAudioParameter*> (p))
                if (r->getParameterID() == a.upToFirstOccurrenceOf ("=", false, false))
                    r->setValueNotifyingHost (r->convertTo0to1 (value.getFloatValue()));
    }
    proc->uiScale = scale;      // rendered through the UI scale path, as in a host
    std::unique_ptr<WraithEditor> ed (dynamic_cast<WraithEditor*> (proc->createEditor()));
    ed->setTestLevels (inDb, outDb, inBar, outBar);
    if (sizeW > 0)
    {
        const juce::Rectangle<int> b (0, 0, sizeW, (int) (sizeW * WraithEditor::designH / WraithEditor::designW));
        ed->getConstrainer()->setBoundsForComponent (ed.get(), b, false, false, true, true);       // as the corner drags
        std::cout << "resized to " << ed->getWidth() << " x " << ed->getHeight() << ", ui scale " << proc->uiScale.load() << std::endl;
    }

    Mouse mouse { *ed };
    for (int i = 2; i < argc; ++i)
    {
        const juce::String a (argv[i]);
        const auto t = juce::StringArray::fromTokens (a.fromFirstOccurrenceOf ("=", false, false), ",", "");
        if (! (a.startsWith ("--click=") || a.startsWith ("--drag=") || a.startsWith ("--hover="))) continue;
        const juce::Point<float> p (t[0].getFloatValue(), t[1].getFloatValue());
        if (! mouse.at (p)) continue;
        const juce::String mod = a.startsWith ("--drag=") ? t[4] : t[2];
        juce::ModifierKeys mods = mod == "alt" ? juce::ModifierKeys::altModifier : mod == "shift" ? juce::ModifierKeys::shiftModifier
                                : mod == "ctrl" ? juce::ModifierKeys::ctrlModifier : juce::ModifierKeys();
        const auto pressed = mods.withFlags (juce::ModifierKeys::leftButtonModifier);
        if (a.startsWith ("--hover="))
        {
            mouse.target->mouseEnter (mouse.make (p, mods, 0, false));
            mouse.target->mouseMove (mouse.make (p, mods, 0, false));
            juce::MessageManager::getInstance()->runDispatchLoopUntil (20);
        }
        else if (a.startsWith ("--click="))
        {
            for (int c = 1; c <= (mod == "dbl" ? 2 : 1); ++c)
            {
                mouse.target->mouseDown (mouse.make (p, pressed, c, false));
                mouse.target->mouseUp (mouse.make (p, mods, c, false));
                if (c == 2) mouse.target->mouseDoubleClick (mouse.make (p, mods, c, false));
            }
            juce::MessageManager::getInstance()->runDispatchLoopUntil (50);
        }
        else
        {
            const juce::Point<float> d (t[2].getFloatValue(), t[3].getFloatValue());
            mouse.target->mouseDown (mouse.make (p, pressed, 1, false));
            const int steps = 20;
            for (int k = 1; k <= steps; ++k)
                mouse.target->mouseDrag (mouse.make (p + d * ((float) k / steps), pressed, 1, true));
            mouse.target->mouseUp (mouse.make (p + d, mods, 1, true));
            juce::MessageManager::getInstance()->runDispatchLoopUntil (50);
        }
        dump (*proc, a);
    }

    auto img = ed->createComponentSnapshot (ed->getLocalBounds(), true, 1.0f);
    juce::File f (juce::File::getCurrentWorkingDirectory().getChildFile (argv[1]));
    f.deleteFile();
    juce::FileOutputStream os (f);
    juce::PNGImageFormat().writeImageToStream (img, os);
    ed.reset();
    return 0;
}
