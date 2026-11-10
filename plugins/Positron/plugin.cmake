# Positron (recreation of Cradle's The God Particle). Included from the top-level CMakeLists.txt.
set(PO_DIR ${CMAKE_CURRENT_LIST_DIR})

juce_add_binary_data(PositronData SOURCES ${PO_DIR}/resources/glass/glass_off.png ${PO_DIR}/resources/glass/glass_lit.png)
set_target_properties(PositronData PROPERTIES POSITION_INDEPENDENT_CODE ON)

set(PO_SOURCES
    ${PO_DIR}/Source/dsp/Engine.cpp
    ${PO_DIR}/Source/PluginProcessor.cpp
    ${PO_DIR}/Source/PluginEditor.cpp
    ${PO_DIR}/Source/Presets.cpp
    ${PO_DIR}/Source/ui/Visualizer.cpp
    ${SUITE_UI_SOURCES})

set(PO_DEFS ${SUITE_DEFS} SUITE_REPOSITORY="${SUITE_REPOSITORY}")
# the snapshot / test executables compile the plug-in sources outside the plug-in wrapper
set(PO_APP_DEFS ${PO_DEFS} JucePlugin_Name="Positron" JucePlugin_IsSynth=0 JucePlugin_WantsMidiInput=0
    JucePlugin_ProducesMidiOutput=0 JucePlugin_IsMidiEffect=0 JucePlugin_VersionString="${PROJECT_VERSION}")

set(formats VST3 Standalone)
if(APPLE)
    list(APPEND formats AU)
endif()
# The manufacturer and plug-in codes make the plug-in's identity in hosts (saved projects find it by them): keep them.
juce_add_plugin(Positron
    COMPANY_NAME "Orrery Suite"
    PLUGIN_MANUFACTURER_CODE Orry
    PLUGIN_CODE Pstn
    FORMATS ${formats}
    PRODUCT_NAME "Positron"
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS FALSE   # the host keeps its transport shortcuts
    VST3_CATEGORIES Fx Dynamics Mastering
    AU_MAIN_TYPE kAudioUnitType_Effect
    BUNDLE_ID com.orrerysuite.positron)
# MSBuild cannot handle the apostrophe of the product name in the shared-code library's file name
# (both names: Xcode builds the library under XCODE_ATTRIBUTE_PRODUCT_NAME, the link lines use OUTPUT_NAME)
set_target_properties(Positron PROPERTIES OUTPUT_NAME "Positron_SharedCode" XCODE_ATTRIBUTE_PRODUCT_NAME "Positron_SharedCode")
target_sources(Positron PRIVATE ${PO_SOURCES})
target_include_directories(Positron PRIVATE ${PO_DIR}/Source ${CMAKE_SOURCE_DIR})
target_compile_definitions(Positron PUBLIC ${PO_DEFS})
target_link_libraries(Positron PRIVATE PositronData OrreryUiData juce::juce_audio_utils juce::juce_dsp
    juce::juce_recommended_config_flags juce::juce_recommended_lto_flags juce::juce_recommended_warning_flags suite_warnings)
# (GCC: JUCE's VST3 SDK copy has multi-character constants)
target_compile_options(Positron_VST3 PRIVATE $<$<CXX_COMPILER_ID:GNU>:-Wno-multichar>)
add_dependencies(ci_targets Positron_VST3)
if(ORRERY_CLAP)
    clap_juce_extensions_plugin(TARGET Positron
        CLAP_ID "com.orrerysuite.positron" CLAP_FEATURES audio-effect mastering stereo)
    # (Xcode: the CLAP bundle's identifier matches the one in its Info.plist)
    set_target_properties(Positron_CLAP PROPERTIES XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "com.orrerysuite.positron")
endif()

# Unit tests (DSP + processor):  cmake --build build --target PositronTests, then ctest --test-dir build -C Release
juce_add_console_app(PositronTests PRODUCT_NAME "PositronTests")
target_sources(PositronTests PRIVATE ${PO_DIR}/tests/PositronTests.cpp ${PO_SOURCES})
target_include_directories(PositronTests PRIVATE ${PO_DIR}/Source ${CMAKE_SOURCE_DIR})
target_compile_definitions(PositronTests PRIVATE ${PO_APP_DEFS})
target_link_libraries(PositronTests PRIVATE PositronData OrreryUiData juce::juce_audio_utils juce::juce_dsp
    juce::juce_recommended_config_flags)
add_test(NAME PositronTests COMMAND PositronTests)
add_dependencies(ci_targets PositronTests)

if(ORRERY_TOOLS)
    # Editor snapshot (PNG) for the visual comparison with the reference
    juce_add_console_app(PositronSnapshot PRODUCT_NAME "PositronSnapshot")
    target_sources(PositronSnapshot PRIVATE ${PO_DIR}/tools/Snapshot.cpp ${PO_SOURCES})
    target_include_directories(PositronSnapshot PRIVATE ${PO_DIR}/Source ${CMAKE_SOURCE_DIR})
    target_compile_definitions(PositronSnapshot PRIVATE ${PO_APP_DEFS})
    target_link_libraries(PositronSnapshot PRIVATE PositronData OrreryUiData juce::juce_audio_utils juce::juce_dsp
        juce::juce_recommended_config_flags)

    # Offline renders through our own processor with every DSP constant open to change (fitting, null tests), and a
    # second copy for trying DSP changes while a fit is running with the first (nulltest/tgp.py: PO_RENDER=dev)
    foreach(t PoRender PoRenderDev)
        juce_add_console_app(${t} PRODUCT_NAME "${t}")
        target_sources(${t} PRIVATE ${PO_DIR}/tools/PoRender.cpp ${PO_SOURCES})
        target_include_directories(${t} PRIVATE ${PO_DIR}/Source ${CMAKE_SOURCE_DIR})
        target_compile_definitions(${t} PRIVATE ${PO_APP_DEFS})
        target_link_libraries(${t} PRIVATE PositronData OrreryUiData juce::juce_audio_utils juce::juce_dsp
            juce::juce_recommended_config_flags)
    endforeach()

    # the band gain computer as a plain C library for the fitting scripts (nulltest/charsim.py)
    add_library(charsim SHARED ${PO_DIR}/tools/charsim.cpp)
    target_include_directories(charsim PRIVATE ${PO_DIR}/Source)
    set_target_properties(charsim PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/charsim)
    if(WIN32)
        add_dependencies(ci_targets PositronSnapshot)      # ci.yml's screenshot artefact is made on Windows
    endif()
    add_dependencies(ci_targets PoRender)          # the render regression
endif()
