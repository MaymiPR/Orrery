// WrRender: offline renders through Wraith's own processor (no plug-in loading), with every DSP constant
// open to change. Same job format as RefRender, so nulltest/wr_ref.py drives both:
//   WrRender jobs.txt [fs=48000] [block=512] [tuning=file]
// jobs.txt: one render per line:  in.f32 out.f32 [key=value ...]
//   param:Name=text  norm:Name=0.5  auto:Name@sample=0.7  raw=1   (as RefRender)
//   tune:key=value   a Tuning constant for this job (Source/dsp/Tuning.h), e.g. tune:smoothTauMs=5
// .f32 files are stereo interleaved float32 at the render rate.
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

int main (int argc, char** argv)
{
    ScopedJuceInitialiser_GUI init;
    StringArray args;
    for (int i = 1; i < argc; ++i) args.add (String (argv[i]).unquoted());
    if (args.size() < 1) { std::printf ("usage: WrRender jobs.txt [fs=48000] [block=512] [tuning=file]\n"); return 2; }
    double fs = 48000.0;
    int block = 512;
    const wr::dsp::Tuning defaults = wr::dsp::tuning();
    wr::dsp::Tuning base = defaults;
    for (int i = 1; i < args.size(); ++i)
    {
        if (args[i].startsWith ("fs=")) fs = args[i].substring (3).getDoubleValue();
        if (args[i].startsWith ("block=")) block = args[i].substring (6).getIntValue();
        if (args[i].startsWith ("tuning=") && base.load (args[i].substring (7).toRawUTF8()) != 0) return 1;
    }

    StringArray lines;
    File (File::getCurrentWorkingDirectory().getChildFile (args[0])).readLines (lines);
    for (auto& line : lines)
    {
        auto tok = StringArray::fromTokens (line, " ", "\"");
        tok.removeEmptyStrings();
        if (tok.size() < 2) continue;
        for (auto& t : tok) t = t.unquoted();

        wr::dsp::tuning() = base;
        bool raw = false;
        for (int i = 2; i < tok.size(); ++i)
        {
            const auto& a = tok[i];
            if (a == "raw=1") raw = true;
            else if (a.startsWith ("tune:"))
            {
                const auto kv = a.substring (5);
                if (! wr::dsp::tuning().set (kv.upToFirstOccurrenceOf ("=", false, false).toStdString(), kv.fromFirstOccurrenceOf ("=", false, false).getDoubleValue()))
                    { std::printf ("unknown tuning key in '%s'\n", a.toRawUTF8()); return 1; }
            }
        }

        WraithProcessor proc;
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
            if (isAuto) { at = name.fromFirstOccurrenceOf ("@", false, false).getIntValue(); name = name.upToFirstOccurrenceOf ("@", false, false); }
            auto* p = findParam (proc, name);
            if (p == nullptr) { std::printf ("  no parameter '%s'\n", name.toRawUTF8()); continue; }
            const float v = isParam ? p->getValueForText (val) : val.getFloatValue();
            if (isAuto) autom.insert ({ at, { p, v } });
            else p->setValueNotifyingHost (v);
        }
        proc.setRateAndBufferSizeDetails (fs, block);
        proc.prepareToPlay (fs, block);

        const auto in = readF32 (tok[0]);
        const int latency = raw ? 0 : proc.getLatencySamples();
        const int n = (int) (in.size() / 2);
        std::vector<float> out ((size_t) n * 2, 0.0f);
        AudioBuffer<float> buf (2, block);
        MidiBuffer midi;
        auto next = autom.begin();
        for (int pos = 0; pos < n + latency; pos += block)
        {
            while (next != autom.end() && next->first < pos + block) { next->second.first->setValueNotifyingHost (next->second.second); ++next; }
            buf.clear();
            for (int i = 0; i < block; ++i)
            {
                const int k = pos + i;
                if (k < n) { buf.setSample (0, i, in[(size_t) k * 2]); buf.setSample (1, i, in[(size_t) k * 2 + 1]); }
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
        os.write (out.data(), out.size() * sizeof (float));
        std::printf ("job %s: %d frames, latency %d\n", tok[1].toRawUTF8(), n, latency);
        std::fflush (stdout);
    }
    wr::dsp::tuning() = defaults;
    return 0;
}
