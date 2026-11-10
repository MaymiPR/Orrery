# Scorpius (recreation of Cradle's Orion). Included from the top-level CMakeLists.txt, after shared/shared.cmake.
set(SC_DIR ${CMAKE_CURRENT_LIST_DIR})

set(SC_SOURCES
    ${SC_DIR}/Source/PluginProcessor.cpp
    ${SC_DIR}/Source/PluginEditor.cpp
    ${SC_DIR}/Source/Presets.cpp
    ${SC_DIR}/Source/dsp/Engine.cpp
    ${SC_DIR}/Source/ui/Controls.cpp
    ${SC_DIR}/Source/ui/Stripe.cpp)

set(SC_DEFS ${SUITE_DEFS} SUITE_REPOSITORY="${SUITE_REPOSITORY}")
# the snapshot / test executables compile the plug-in sources outside the plug-in wrapper
set(SC_APP_DEFS ${SC_DEFS} JucePlugin_Name="Scorpius" JucePlugin_IsSynth=0 JucePlugin_WantsMidiInput=0
    JucePlugin_ProducesMidiOutput=0 JucePlugin_IsMidiEffect=0 JucePlugin_VersionString="${PROJECT_VERSION}")

set(formats VST3 Standalone)
if(APPLE)
    list(APPEND formats AU)
endif()
# The manufacturer and plug-in codes make the plug-in's identity in hosts (saved projects find it by them): keep them.
# COMPANY_NAME, BUNDLE_ID and CLAP_ID keep the suite's first name, Orrery Suite (CONTRIBUTING.md "Frozen identity").
juce_add_plugin(Scorpius
    COMPANY_NAME "Orrery Suite"
    PLUGIN_MANUFACTURER_CODE Orry
    PLUGIN_CODE Scrp
    FORMATS ${formats}
    PRODUCT_NAME "Scorpius"
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE   # the host keeps its transport shortcuts
    VST3_CATEGORIES Fx Dynamics Distortion
    AU_MAIN_TYPE kAudioUnitType_Effect
    BUNDLE_ID com.orrerysuite.scorpius)
target_sources(Scorpius PRIVATE ${SC_SOURCES})
target_include_directories(Scorpius PRIVATE ${SC_DIR}/Source ${CMAKE_SOURCE_DIR})
target_compile_definitions(Scorpius PUBLIC ${SC_DEFS})
target_link_libraries(Scorpius PRIVATE OrreryShared juce::juce_audio_utils juce::juce_dsp
    juce::juce_recommended_config_flags juce::juce_recommended_lto_flags juce::juce_recommended_warning_flags suite_warnings)
# (GCC: JUCE's VST3 SDK copy has multi-character constants)
target_compile_options(Scorpius_VST3 PRIVATE $<$<CXX_COMPILER_ID:GNU>:-Wno-multichar>)
add_dependencies(ci_targets Scorpius_VST3)
if(ORRERY_DEV_COPY)
    # Every rebuild also lands at build/plugins/<Product name>.vst3, the one folder a DAW's plug-in junction points at.
    add_custom_command(TARGET Scorpius_VST3 POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory "$<TARGET_FILE_DIR:Scorpius_VST3>/../.."
            "${CMAKE_BINARY_DIR}/plugins/Scorpius.vst3"
        VERBATIM)
endif()
if(ORRERY_CLAP)
    clap_juce_extensions_plugin(TARGET Scorpius
        CLAP_ID "com.orrerysuite.scorpius" CLAP_FEATURES audio-effect distortion compressor stereo)
    # (Xcode: the CLAP bundle's identifier matches the one in its Info.plist)
    set_target_properties(Scorpius_CLAP PROPERTIES XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "com.orrerysuite.scorpius")
endif()

# Unit tests (processor, presets, compare):  ctest --test-dir build -C Release
juce_add_console_app(ScorpiusTests PRODUCT_NAME "ScorpiusTests")
target_sources(ScorpiusTests PRIVATE ${SC_DIR}/tests/ScorpiusTests.cpp ${SC_SOURCES})
target_include_directories(ScorpiusTests PRIVATE ${SC_DIR}/Source ${CMAKE_SOURCE_DIR})
target_compile_definitions(ScorpiusTests PRIVATE ${SC_APP_DEFS})
target_link_libraries(ScorpiusTests PRIVATE OrreryShared juce::juce_audio_utils juce::juce_dsp juce::juce_recommended_config_flags)
add_test(NAME ScorpiusTests COMMAND ScorpiusTests)
add_dependencies(ci_targets ScorpiusTests)

# The built VST3 hosted as a DAW hosts it (tools/HostTest.cpp): save and reload, rate changes, offline rendering and
# every saved state of an earlier release in tests/data (state-<x.y.z>.bin with its .txt, written at each release
# that changes a parameter or its reading: ScorpiusHostTest <vst3> --save-state plugins/Scorpius/tests/data/state-<x.y.z>.bin).
juce_add_console_app(ScorpiusHostTest PRODUCT_NAME "ScorpiusHostTest")
target_sources(ScorpiusHostTest PRIVATE ${CMAKE_SOURCE_DIR}/tools/HostTest.cpp)
target_compile_definitions(ScorpiusHostTest PRIVATE JUCE_PLUGINHOST_VST3=1 JUCE_MODAL_LOOPS_PERMITTED=1 ${SUITE_DEFS})
target_link_libraries(ScorpiusHostTest PRIVATE juce::juce_audio_processors juce::juce_gui_basics
    juce::juce_recommended_config_flags juce::juce_recommended_warning_flags suite_warnings)
add_dependencies(ScorpiusHostTest Scorpius_VST3)          # the test loads the VST3 bundle
file(GLOB SC_STATES CONFIGURE_DEPENDS ${SC_DIR}/tests/data/state-*.bin)
add_test(NAME ScorpiusHostTest
    COMMAND ScorpiusHostTest $<GENEX_EVAL:$<TARGET_PROPERTY:Scorpius_VST3,JUCE_PLUGIN_ARTEFACT_FILE>> ${SC_STATES})
add_dependencies(ci_targets ScorpiusHostTest)

if(ORRERY_TOOLS)
    # Editor snapshot (PNG) for the visual comparison with the reference (tools/compare_ui.py)
    juce_add_console_app(ScorpiusSnapshot PRODUCT_NAME "ScorpiusSnapshot")
    target_sources(ScorpiusSnapshot PRIVATE ${SC_DIR}/tools/Snapshot.cpp ${SC_SOURCES})
    target_include_directories(ScorpiusSnapshot PRIVATE ${SC_DIR}/Source ${CMAKE_SOURCE_DIR})
    target_compile_definitions(ScorpiusSnapshot PRIVATE ${SC_APP_DEFS})
    target_link_libraries(ScorpiusSnapshot PRIVATE OrreryShared juce::juce_audio_utils juce::juce_dsp juce::juce_recommended_config_flags)
    # Offline renders through our processor with every DSP constant open to change (the fits: nulltest/ori.py, 'model')
    juce_add_console_app(ScRender PRODUCT_NAME "ScRender")
    target_sources(ScRender PRIVATE ${SC_DIR}/tools/ScRender.cpp ${SC_SOURCES})
    target_include_directories(ScRender PRIVATE ${SC_DIR}/Source ${CMAKE_SOURCE_DIR})
    target_compile_definitions(ScRender PRIVATE ${SC_APP_DEFS})
    target_link_libraries(ScRender PRIVATE OrreryShared juce::juce_audio_utils juce::juce_dsp juce::juce_recommended_config_flags)
    if(WIN32)
        add_dependencies(ci_targets ScorpiusSnapshot)      # ci.yml's screenshot artefact is made on Windows
    endif()
    add_dependencies(ci_targets ScRender)          # the render regression
endif()
