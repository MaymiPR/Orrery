// Unit tests for Wraith: the DSP blocks (Source/dsp) and the processor. Run: WraithTests (exit code 0 =
// all passed; ctest runs it). The match with the reference itself is the null-test suite (nulltest/nulltest.py,
// NULLTESTS.md). Add a test per block as Phase 4 adds the blocks: a filter's gain at a frequency, a detector's time
// constant, a table's end points, the latency, the state of a saved project from the last release.
#include <cmath>
#include <cstdio>
#include <random>
#include <vector>
#include "PluginProcessor.h"
#include "dsp/Engine.h"

static int failures = 0, checks = 0;
#define CHECK(cond) do { ++checks; if (! (cond)) { ++failures; std::printf ("FAIL %s:%d  %s\n", __FILE__, __LINE__, #cond); } } while (0)
#define CHECK_NEAR(a, b, tol) do { ++checks; const double va = (a), vb = (b); if (! (std::fabs (va - vb) <= (tol))) { ++failures; std::printf ("FAIL %s:%d  %s = %g, expected %g +- %g\n", __FILE__, __LINE__, #a, va, vb, (double) (tol)); } } while (0)

using namespace juce;

static double db (double v) { return 20.0 * std::log10 (std::max (v, 1.0e-30)); }

// the real-unit value of a parameter, and setting one
static float real (WraithProcessor& p, const char* pid)
{
    auto* r = dynamic_cast<RangedAudioParameter*> (p.apvts.getParameter (pid));
    return r->convertFrom0to1 (r->getValue());
}
static void setReal (WraithProcessor& p, const char* pid, float v)
{
    auto* r = dynamic_cast<RangedAudioParameter*> (p.apvts.getParameter (pid));
    r->setValueNotifyingHost (r->convertTo0to1 (v));
}

// renders n samples of x through a prepared processor in blocks
static std::vector<float> run (WraithProcessor& p, const std::vector<float>& x, int block = 512)
{
    std::vector<float> y (x.size());
    AudioBuffer<float> buf (2, block);
    MidiBuffer midi;
    for (size_t pos = 0; pos < x.size(); pos += (size_t) block)
    {
        const int n = (int) std::min ((size_t) block, x.size() - pos);
        buf.setSize (2, n, false, false, true);
        for (int i = 0; i < n; ++i) { buf.setSample (0, i, x[pos + (size_t) i]); buf.setSample (1, i, x[pos + (size_t) i]); }
        p.processBlock (buf, midi);
        for (int i = 0; i < n; ++i) y[pos + (size_t) i] = buf.getSample (0, i);
    }
    return y;
}

static std::vector<float> sine (double f, double fs, int n, float amp = 0.5f)
{
    std::vector<float> x ((size_t) n);
    for (int i = 0; i < n; ++i) x[(size_t) i] = amp * (float) std::sin (2.0 * MathConstants<double>::pi * f * i / fs);
    return x;
}

static void testLayout()
{
    WraithProcessor p;
    CHECK (p.getParameters().size() == wr::numParams);
    CHECK (p.getBypassParameter() != nullptr);
    for (auto* pid : wr::allIds) CHECK (p.apvts.getParameter (pid) != nullptr);
}

static void allStagesOff (WraithProcessor& p)
{
    for (auto* pid : { wr::id::riderOn, wr::id::characterOn, wr::id::eqOn, wr::id::doublerOn, wr::id::reverbOn })
        setReal (p, pid, 0.0f);
}

static void testUnityAllOff()
{
    WraithProcessor p;
    p.prepareToPlay (48000.0, 512);
    allStagesOff (p);
    const auto x = sine (1000.0, 48000.0, 48000);
    const auto y = run (p, x);
    // every stage off passes the signal unchanged, as the reference does (MEASUREMENTS.md 1)
    double err = 0;
    for (size_t i = 24000; i < x.size(); ++i) err = std::max (err, (double) std::fabs (y[i] - x[i]));
    CHECK (db (err) < -100.0);
    CHECK (p.getLatencySamples() == 0);    // the reference reports 0 at every rate
}

static void testGains()
{
    WraithProcessor p;
    p.prepareToPlay (48000.0, 512);
    allStagesOff (p);
    setReal (p, wr::id::inputGain, -6.0f);
    setReal (p, wr::id::outputGain, 2.0f);
    const auto x = sine (1000.0, 48000.0, 48000);
    const auto y = run (p, x);
    double peak = 0;
    for (size_t i = 24000; i < y.size(); ++i) peak = std::max (peak, (double) std::fabs (y[i]));
    CHECK_NEAR (db (peak / 0.5), -4.0, 0.01);
}

static void testBypassIsDelayedInput()
{
    WraithProcessor p;
    p.prepareToPlay (48000.0, 256);
    setReal (p, wr::id::inputGain, 6.0f);
    p.getBypassParameter()->setValueNotifyingHost (1.0f);
    std::mt19937 rng (3);
    std::normal_distribution<float> nd (0.0f, 0.1f);
    std::vector<float> x (24000);
    for (auto& v : x) v = nd (rng);
    const auto y = run (p, x, 256);
    const int lat = p.getLatencySamples();
    double err = 0;
    for (size_t i = (size_t) lat; i < x.size(); ++i) err = std::max (err, (double) std::fabs (y[i] - x[i - (size_t) lat]));
    CHECK (exactlyEqual (err, 0.0));
}

static void testStateRoundTrip()
{
    WraithProcessor p;
    setReal (p, wr::id::inputGain, -3.5f);
    p.uiScale = 1.5f;
    p.presets.setCurrentName ("mine");
    MemoryBlock mb;
    p.getStateInformation (mb);
    WraithProcessor q;
    q.setStateInformation (mb.getData(), (int) mb.getSize());
    CHECK_NEAR (real (q, wr::id::inputGain), -3.5, 1e-4);
    CHECK_NEAR (q.uiScale.load(), 1.5, 1e-6);
    CHECK (q.presets.currentName() == "mine");
}

static void testStartupPreset()
{
    WraithProcessor p;
    // the plug-in opens with "lead", exact values included (RESEARCH.md "Presets")
    CHECK (p.presets.currentName() == "lead");
    CHECK_NEAR (real (p, wr::id::eqLow), 4.0975, 1e-4);
    CHECK_NEAR (real (p, wr::id::focus), 8.0, 1e-6);
    setReal (p, wr::id::inputGain, 4.0f);
    const auto all = p.presets.list();
    CHECK (all.size() >= 11 && all[0].factory && all[0].name == "backing stack");     // the reference's menu order
    for (auto& e : all)
        if (e.name == "lead") p.presets.load (e);
    CHECK_NEAR (real (p, wr::id::inputGain), 0.0, 1e-6);
    CHECK_NEAR (real (p, wr::id::reverbFilter), 9845.186, 0.01);
}

static void testTapers()
{
    WraithProcessor p;
    auto norm = [&] (const char* pid, float v) { return dynamic_cast<RangedAudioParameter*> (p.apvts.getParameter (pid))->convertTo0to1 (v); };
    CHECK_NEAR (norm (wr::id::doublerMix, 0.1f), 0.307692, 1e-5);     // ParamDump's default position
    CHECK_NEAR (norm (wr::id::reverbMix, 0.2f), 0.5, 1e-6);
    CHECK_NEAR (norm (wr::id::reverbFilter, 8041.65f), 0.5, 1e-5);
    CHECK_NEAR (norm (wr::id::riderSpeed, 0.003f), 0.222222, 1e-5);
}

static void testExtremeInput()
{
    WraithProcessor p;
    p.prepareToPlay (96000.0, 64);
    std::vector<float> x (9600, 100.0f);        // far over full scale: no NaN, no inf
    const auto y = run (p, x, 64);
    bool finite = true;
    for (auto v : y) finite = finite && std::isfinite (v);
    CHECK (finite);
}

static void testCompare()
{
    WraithProcessor p;
    setReal (p, wr::id::inputGain, -3.0f);
    p.selectCompareSlot (1);                                   // B starts as a copy of A
    CHECK_NEAR (real (p, wr::id::inputGain), -3.0, 1e-4);
    setReal (p, wr::id::inputGain, 5.0f);
    p.selectCompareSlot (0);
    CHECK_NEAR (real (p, wr::id::inputGain), -3.0, 1e-4);
    p.selectCompareSlot (1);
    CHECK_NEAR (real (p, wr::id::inputGain), 5.0, 1e-4);
    MemoryBlock mb;                                            // both settings and the active one survive the state
    p.getStateInformation (mb);
    WraithProcessor q;
    q.setStateInformation (mb.getData(), (int) mb.getSize());
    CHECK (q.compareSlot() == 1);
    CHECK_NEAR (real (q, wr::id::inputGain), 5.0, 1e-4);
    q.selectCompareSlot (0);
    CHECK_NEAR (real (q, wr::id::inputGain), -3.0, 1e-4);
    q.copyCompareSlot();                                       // A -> B
    q.selectCompareSlot (1);
    CHECK_NEAR (real (q, wr::id::inputGain), -3.0, 1e-4);
}

static void testIoLink()
{
    WraithProcessor p;
    p.prepareToPlay (48000.0, 512);
    allStagesOff (p);
    setReal (p, wr::id::inputGain, 6.0f);
    setReal (p, wr::id::outputGain, 3.0f);
    p.ioLink = true;                                           // the output follows -input: unity overall
    const auto x = sine (1000.0, 48000.0, 48000);
    const auto y = run (p, x);
    double err = 0;
    for (size_t i = 24000; i < x.size(); ++i) err = std::max (err, (double) std::fabs (y[i] - x[i]));
    CHECK (db (err) < -100.0);
    MemoryBlock mb;
    p.getStateInformation (mb);
    WraithProcessor q;
    q.setStateInformation (mb.getData(), (int) mb.getSize());
    CHECK (q.ioLink.load());
}

static void testSidechainWithoutBus()
{
    // EXT with the side-chain bus not connected keeps listening to the input: the same output as INT
    std::vector<float> x (48000);
    std::mt19937 rng (5);
    std::normal_distribution<float> nd (0.0f, 0.1f);
    for (auto& v : x) v = nd (rng);
    WraithProcessor a, b;
    a.prepareToPlay (48000.0, 512);
    b.prepareToPlay (48000.0, 512);
    b.sidechainExternal = true;
    const auto ya = run (a, x), yb = run (b, x);
    double err = 0;
    for (size_t i = 0; i < x.size(); ++i) err = std::max (err, (double) std::fabs (ya[i] - yb[i]));
    CHECK (exactlyEqual (err, 0.0));
    CHECK (a.getBusCount (true) == 2);                         // the side-chain input exists, off by default
}

int main()
{
    ScopedJuceInitialiser_GUI init;
    testLayout();
    testUnityAllOff();
    testGains();
    testBypassIsDelayedInput();
    testStateRoundTrip();
    testStartupPreset();
    testTapers();
    testExtremeInput();
    testCompare();
    testIoLink();
    testSidechainWithoutBus();
    std::printf ("%d checks, %d failures\n", checks, failures);
    return failures == 0 ? 0 : 1;
}
