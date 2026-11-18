// PoRender: offline renders through Positron's own processor (no plug-in loading), with every DSP constant
// open to change. Same job format as RefRender, so nulltest/po_ref.py drives both:
//   PoRender jobs.txt [fs=48000] [block=512] [tuning=file]
// jobs.txt: one render per line:  in.f32 out.f32 [key=value ...]
//   param:Name=text  norm:Name=0.5  auto:Name@sample=0.7  sc=file.f32  raw=1   (as RefRender)
//   tune:key=value   a Tuning constant for this job (Source/dsp/Tuning.h), e.g. tune:mid.mix.4=0.7
//   ext=1            side-chain EXT (the host-only setting)
#include <cstdio>
#include <map>
#include "PluginProcessor.h"

using namespace juce;

static std::vector<float> readF32 (const String& path)
{
    MemoryBlock mb;
    File (File::getCurrentWorkingDirectory().getChildFile (path)).loadFileAsData (mb);
    return std::vector<float> ((const float*) mb.getData(), (const float*) mb.getData() + mb.getSize() / sizeof (float));
}

static AudioProcessorParameter* findParam (AudioProcessor& p, const String& name)
{
    for (auto* q : p.getParameters())
        if (q->getName (128).equalsIgnoreCase (name)) return q;
    return nullptr;
}

// a message and the exit code of a run that could not do what it was asked
static int fail (const String& message)
{
    std::printf ("%s\n", message.toRawUTF8());
    std::fflush (stdout);
    return 1;
}

// whether the whole text is one finite number (a malformed number is refused, it never reads as 0)
static bool isNumber (const String& text)
{
    const auto t = text.trim();
    if (t.isEmpty()) return false;
    char* end = nullptr;
    const double v = std::strtod (t.toRawUTF8(), &end);
    return end != nullptr && *end == 0 && std::isfinite (v);
}

int main (int argc, char** argv)
{
    ScopedJuceInitialiser_GUI init;
    StringArray args;
    for (int i = 1; i < argc; ++i) args.add (String (argv[i]).unquoted());
    if (args.size() < 1) { std::printf ("usage: PoRender jobs.txt [fs=48000] [block=512] [tuning=file]\n"); return 2; }
    double fs = 48000.0;
    int block = 512;
    const po::dsp::Tuning defaults = po::dsp::tuning();
    po::dsp::Tuning base = defaults;
    for (int i = 1; i < args.size(); ++i)
    {
        if (args[i].startsWith ("fs="))
        {
            if (! isNumber (args[i].substring (3)) || args[i].substring (3).getDoubleValue() <= 0.0) return fail ("malformed number in '" + args[i] + "'");
            fs = args[i].substring (3).getDoubleValue();
        }
        if (args[i].startsWith ("block="))
        {
            if (! isNumber (args[i].substring (6)) || args[i].substring (6).getIntValue() < 1) return fail ("malformed number in '" + args[i] + "'");
            block = args[i].substring (6).getIntValue();
        }
        if (args[i].startsWith ("tuning=") && base.load (args[i].substring (7).toRawUTF8()) != 0) return 1;
    }

    const File jobsFile (File::getCurrentWorkingDirectory().getChildFile (args[0]));
    if (! jobsFile.existsAsFile()) return fail ("cannot read the jobs file " + args[0]);
    StringArray lines;
    jobsFile.readLines (lines);
    for (auto& line : lines)
    {
        auto tok = StringArray::fromTokens (line, " ", "\"");
        tok.removeEmptyStrings();
        if (tok.size() < 2) continue;
        for (auto& t : tok) t = t.unquoted();

        po::dsp::tuning() = base;
        String scPath;
        bool raw = false, ext = false;
        for (int i = 2; i < tok.size(); ++i)
        {
            const auto& a = tok[i];
            if (a.startsWith ("sc=")) scPath = a.substring (3);
            else if (a == "raw=1") raw = true;
            else if (a == "ext=1") ext = true;
            else if (a.startsWith ("tune:"))
            {
                const auto kv = a.substring (5);
                if (! isNumber (kv.fromFirstOccurrenceOf ("=", false, false))) return fail ("malformed number in '" + a + "'");
                if (! po::dsp::tuning().set (kv.upToFirstOccurrenceOf ("=", false, false).toStdString(), kv.fromFirstOccurrenceOf ("=", false, false).getDoubleValue()))
                    { std::printf ("unknown tuning key in '%s'\n", a.toRawUTF8()); return 1; }
            }
        }

        PositronProcessor proc;
        auto layout = proc.getBusesLayout();
        if (layout.inputBuses.size() > 1) layout.inputBuses.getReference (1) = AudioChannelSet::stereo();
        proc.setBusesLayout (layout);
        proc.sidechainExternal = ext;
        std::multimap<int, std::pair<AudioProcessorParameter*, float>> autom;
        for (int i = 2; i < tok.size(); ++i)
        {
            const auto& a = tok[i];
            const bool isParam = a.startsWith ("param:"), isNorm = a.startsWith ("norm:"), isAuto = a.startsWith ("auto:");
            if (! (isParam || isNorm || isAuto)) continue;
            const auto body = a.fromFirstOccurrenceOf (":", false, false);
            auto name = body.upToFirstOccurrenceOf ("=", false, false);
            const auto val = body.fromFirstOccurrenceOf ("=", false, false);
            int at = -1;
            if (isAuto)
            {
                if (! isNumber (name.fromFirstOccurrenceOf ("@", false, false))) return fail ("malformed number in '" + a + "'");
                at = name.fromFirstOccurrenceOf ("@", false, false).getIntValue();
                name = name.upToFirstOccurrenceOf ("@", false, false);
            }
            auto* p = findParam (proc, name);
            if (p == nullptr) return fail ("  no parameter '" + name + "'");
            if (! isParam && ! isNumber (val)) return fail ("malformed number in '" + a + "'");
            const float v = isParam ? p->getValueForText (val) : val.getFloatValue();
            if (isAuto) autom.insert ({ at, { p, v } });
            else p->setValueNotifyingHost (v);
        }
        const int nIn = proc.getTotalNumInputChannels();
        proc.setRateAndBufferSizeDetails (fs, block);    // (setPlayConfigDetails would reset the side-chain bus)
        proc.prepareToPlay (fs, block);

        if (! File::getCurrentWorkingDirectory().getChildFile (tok[0]).existsAsFile()) return fail ("cannot read the input " + tok[0]);
        const auto in = readF32 (tok[0]);
        if (scPath.isNotEmpty() && ! File::getCurrentWorkingDirectory().getChildFile (scPath).existsAsFile())
            return fail ("cannot read the side-chain input " + scPath);
        const auto sc = scPath.isNotEmpty() ? readF32 (scPath) : std::vector<float>();
        const int latency = raw ? 0 : proc.getLatencySamples();
        const int n = (int) (in.size() / 2);
        std::vector<float> out ((size_t) n * 2, 0.0f);
        AudioBuffer<float> buf (jmax (nIn, 2), block);
        MidiBuffer midi;
        auto next = autom.begin();
        for (int pos = 0; pos < n + latency; pos += block)
        {
            while (next != autom.end() && next->first < pos + block) { next->second.first->setValueNotifyingHost (next->second.second); ++next; }
            buf.clear();
            for (int i = 0; i < block; ++i)
            {
                const int k = pos + i;
                if (k < n)
                {
                    buf.setSample (0, i, in[(size_t) k * 2]);
                    buf.setSample (1, i, in[(size_t) k * 2 + 1]);
                    if (nIn > 3 && (size_t) k * 2 + 1 < sc.size()) { buf.setSample (2, i, sc[(size_t) k * 2]); buf.setSample (3, i, sc[(size_t) k * 2 + 1]); }
                }
            }
            proc.processBlock (buf, midi);
            for (int i = 0; i < block; ++i)
            {
                const int k = pos + i - latency;
                if (k >= 0 && k < n) { out[(size_t) k * 2] = buf.getSample (0, i); out[(size_t) k * 2 + 1] = buf.getSample (1, i); }
            }
        }
        File f (File::getCurrentWorkingDirectory().getChildFile (tok[1]));
        f.deleteFile();
        FileOutputStream os (f);
        if (! os.openedOk() || ! os.write (out.data(), out.size() * sizeof (float))) return fail ("cannot write the output " + tok[1]);
        os.flush();
        std::printf ("job %s: %d frames, latency %d\n", tok[1].toRawUTF8(), n, latency);
        std::fflush (stdout);
    }
    po::dsp::tuning() = defaults;
    return 0;
}
