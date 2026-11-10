# Wraith (recreation of Cradle The Spirit). Included from the top-level CMakeLists.txt after shared/shared.cmake.
set(WR_DIR ${CMAKE_CURRENT_LIST_DIR})

set(WR_SOURCES
    ${WR_DIR}/Source/dsp/Engine.cpp
    ${WR_DIR}/Source/dsp/Reverb.cpp
    ${WR_DIR}/Source/PluginProcessor.cpp
    ${WR_DIR}/Source/PluginEditor.cpp
    ${WR_DIR}/Source/Presets.cpp
    ${WR_DIR}/Source/ui/Faceplate.cpp
    ${WR_DIR}/Source/ui/Controls.cpp
    ${WR_DIR}/Source/ui/Displays.cpp
    ${SUITE_UI_SOURCES})

# the reverb's measured responses per rate (nulltest/pack_reverb.py)
juce_add_binary_data(WraithIR HEADER_NAME WraithIR.h NAMESPACE WraithIR SOURCES
    ${WR_DIR}/resources/ir/reverb_44100.bin ${WR_DIR}/resources/ir/reverb_48000.bin ${WR_DIR}/resources/ir/reverb_88200.bin ${WR_DIR}/resources/ir/reverb_96000.bin)
set_target_properties(WraithIR PROPERTIES POSITION_INDEPENDENT_CODE ON)

set(WR_DEFS ${SUITE_DEFS} SUITE_REPOSITORY="${SUITE_REPOSITORY}")
# the snapshot / test / render executables compile the plug-in sources outside the plug-in wrapper
set(WR_APP_DEFS ${WR_DEFS} JucePlugin_Name="Wraith" JucePlugin_IsSynth=0 JucePlugin_WantsMidiInput=0
    JucePlugin_ProducesMidiOutput=0 JucePlugin_IsMidiEffect=0 JucePlugin_VersionString="${PROJECT_VERSION}")

set(formats VST3 Standalone)
if(APPLE)
    list(APPEND formats AU)
endif()
# The manufacturer and plug-in codes make the plug-in's identity in hosts (saved projects find it by them): keep them.
juce_add_plugin(Wraith
    COMPANY_NAME "Orrery Suite"
    PLUGIN_MANUFACTURER_CODE Orry
    PLUGIN_CODE Wrth
    FORMATS ${formats}
    PRODUCT_NAME "Wraith"
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE   # the host keeps its transport shortcuts
    VST3_CATEGORIES Fx Dynamics Reverb
    AU_MAIN_TYPE kAudioUnitType_Effect
    BUNDLE_ID com.orrerysuite.wraith)
# MSBuild cannot handle an apostrophe or other odd characters in the shared-code library's file name (both names:
# Xcode builds the library under XCODE_ATTRIBUTE_PRODUCT_NAME, the link lines use OUTPUT_NAME)
set_target_properties(Wraith PROPERTIES OUTPUT_NAME "Wraith_SharedCode" XCODE_ATTRIBUTE_PRODUCT_NAME "Wraith_SharedCode")
target_sources(Wraith PRIVATE ${WR_SOURCES})
target_include_directories(Wraith PRIVATE ${WR_DIR}/Source ${CMAKE_SOURCE_DIR})
target_compile_definitions(Wraith PUBLIC ${WR_DEFS})
target_link_libraries(Wraith PRIVATE OrreryUiData WraithIR juce::juce_audio_utils juce::juce_dsp
    juce::juce_recommended_config_flags juce::juce_recommended_lto_flags juce::juce_recommended_warning_flags suite_warnings)
# The VST3 wrapper compiles the SDK's vst2persistence.cpp, whose four-character constants GCC reports as -Wmultichar
# (48 lines per build); the option has to sit on the wrapper target, not the shared code.
target_compile_options(Wraith_VST3 PRIVATE $<$<CXX_COMPILER_ID:GNU>:-Wno-multichar>)
add_dependencies(ci_targets Wraith_VST3)
if(ORRERY_CLAP)
    clap_juce_extensions_plugin(TARGET Wraith
        CLAP_ID "com.orrerysuite.wraith" CLAP_FEATURES audio-effect compressor reverb stereo)
    # Xcode wants the bundle identifier as a build setting too, or it warns that the Info.plist's differs from ''.
    set_target_properties(Wraith_CLAP PROPERTIES XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "com.orrerysuite.wraith")
endif()

# Unit tests (DSP + processor):  cmake --build build --target WraithTests, then ctest --test-dir build -C Release
juce_add_console_app(WraithTests PRODUCT_NAME "WraithTests")
target_sources(WraithTests PRIVATE ${WR_DIR}/tests/WraithTests.cpp ${WR_SOURCES})
target_include_directories(WraithTests PRIVATE ${WR_DIR}/Source ${CMAKE_SOURCE_DIR})
target_compile_definitions(WraithTests PRIVATE ${WR_APP_DEFS})
target_link_libraries(WraithTests PRIVATE OrreryUiData WraithIR juce::juce_audio_utils juce::juce_dsp juce::juce_recommended_config_flags
    juce::juce_recommended_warning_flags suite_warnings)
add_test(NAME WraithTests COMMAND WraithTests)
add_dependencies(ci_targets WraithTests)

if(ORRERY_TOOLS)
    # Editor snapshot (PNG) for the visual comparison with the reference (nulltest/compare_ui.py)
    juce_add_console_app(WraithSnapshot PRODUCT_NAME "WraithSnapshot")
    target_sources(WraithSnapshot PRIVATE ${WR_DIR}/tools/Snapshot.cpp ${WR_SOURCES})
    target_include_directories(WraithSnapshot PRIVATE ${WR_DIR}/Source ${CMAKE_SOURCE_DIR})
    target_compile_definitions(WraithSnapshot PRIVATE JUCE_MODAL_LOOPS_PERMITTED=1 ${WR_APP_DEFS})
    target_link_libraries(WraithSnapshot PRIVATE OrreryUiData WraithIR juce::juce_audio_utils juce::juce_dsp juce::juce_recommended_config_flags)

    # Offline renders through our own processor with every DSP constant open to change (fitting, null tests), and a
    # second copy for trying DSP changes while a fit is running with the first (nulltest/ts.py: WR_RENDER=dev)
    foreach(t WrRender WrRenderDev)
        juce_add_console_app(${t} PRODUCT_NAME "${t}")
        target_sources(${t} PRIVATE ${WR_DIR}/tools/WrRender.cpp ${WR_SOURCES})
        target_include_directories(${t} PRIVATE ${WR_DIR}/Source ${CMAKE_SOURCE_DIR})
        target_compile_definitions(${t} PRIVATE ${WR_APP_DEFS})
        target_link_libraries(${t} PRIVATE OrreryUiData WraithIR juce::juce_audio_utils juce::juce_dsp juce::juce_recommended_config_flags)
    endforeach()
    if(WIN32)
        add_dependencies(ci_targets WraithSnapshot)      # ci.yml's screenshot artefact is made on Windows
    endif()
    add_dependencies(ci_targets WrRender)          # the render regression
endif()
