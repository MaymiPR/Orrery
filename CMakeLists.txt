cmake_minimum_required(VERSION 3.22)

# Orrery Suite: one CMake project for every plug-in (plugins/<Name>/plugin.cmake) and the measurement tools.
# The suite's version, shared by every plug-in: a new plug-in raises the middle number (1.1.0, 1.2.0 ...), fixes and
# small updates the last (1.1.1, 1.1.2 ...). CHANGELOG.md has a section per version.
project(OrrerySuite VERSION 1.2.1)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Windows: static C++ runtime, so the plugins load on any PC without a redistributable.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

include(FetchContent)
FetchContent_Declare(JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 9.0.5
    GIT_SHALLOW ON)
FetchContent_MakeAvailable(JUCE)
# A tag can be moved: build only from the commit it pointed to when chosen
# (unless FETCHCONTENT_SOURCE_DIR_JUCE points at a JUCE of your own).
set(ORRERY_JUCE_COMMIT d60b7a78030661574a615b586d9325ba7a7fa7dd)
if(NOT FETCHCONTENT_SOURCE_DIR_JUCE)
    find_package(Git REQUIRED)
    execute_process(COMMAND ${GIT_EXECUTABLE} rev-parse HEAD WORKING_DIRECTORY ${juce_SOURCE_DIR}
        OUTPUT_VARIABLE juce_commit OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(NOT juce_commit STREQUAL ORRERY_JUCE_COMMIT)
        message(FATAL_ERROR "JUCE 9.0.5 is at ${juce_commit}, expected ${ORRERY_JUCE_COMMIT}")
    endif()
endif()

# GCC 13 and later report juce_LookAndFeel_V2.cpp:413 (JUCE 9.0.5) as -Wdangling-reference: front() of a span
# returned by value, whose storage the alert options own, so nothing dangles. Off for that one JUCE file only
# (the plug-ins are included below, not added as subdirectories, so this directory's source property reaches them);
# GCC 12 and earlier don't know the option.
set_source_files_properties("${juce_SOURCE_DIR}/modules/juce_gui_basics/juce_gui_basics_2.cpp" PROPERTIES
    COMPILE_OPTIONS "$<$<AND:$<CXX_COMPILER_ID:GNU>,$<VERSION_GREATER_EQUAL:$<CXX_COMPILER_VERSION>,13>>:-Wno-dangling-reference>")

# CLAP through clap-juce-extensions (MIT; brings the CLAP SDK).
option(ORRERY_CLAP "Build the CLAP plugins" ON)
if(ORRERY_CLAP)
    FetchContent_Declare(clap_juce_extensions
        GIT_REPOSITORY https://github.com/free-audio/clap-juce-extensions.git
        GIT_TAG 7adee3a1bd4684d4caa5601100e364abccff4b4d
        GIT_SUBMODULES_RECURSE ON)
    FetchContent_MakeAvailable(clap_juce_extensions)
endif()

# Measurement tools (hosts for the reference plug-ins, fitting helpers); not shipped.
option(ORRERY_TOOLS "Build the measurement tools" ON)

set(SUITE_DEFS JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0 JUCE_VST3_CAN_REPLACE_VST2=0)
set(SUITE_REPOSITORY "https://github.com/MaymiPR/Orrery")
enable_testing()

# The plug-ins. Each is included (not added as a subdirectory), so its build output stays at
# build/<Target>_artefacts. packaging/plugins.txt lists them for the installers and the release workflow.
# Every plugin.cmake adds its VST3, its tests, its renderer (and on Windows its snapshot tool) to ci_targets, so
# ci.yml builds one target on every system and a new plug-in needs no workflow edit.
add_custom_target(ci_targets)
include(shared/shared.cmake)
include(plugins/Positron/plugin.cmake)
include(plugins/Scorpius/plugin.cmake)
include(plugins/Wraith/plugin.cmake)

if(ORRERY_TOOLS)
    juce_add_console_app(ParamDump PRODUCT_NAME "ParamDump")
    target_sources(ParamDump PRIVATE tools/ParamDump.cpp)
    target_compile_definitions(ParamDump PRIVATE
        JUCE_PLUGINHOST_VST3=1 JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0)
    target_link_libraries(ParamDump PRIVATE
        juce::juce_audio_processors juce::juce_gui_basics
        juce::juce_recommended_config_flags)
    # offline renders through any VST3 (the measurements and null tests; tools/RefRender.cpp)
    juce_add_console_app(RefRender PRODUCT_NAME "RefRender")
    target_sources(RefRender PRIVATE tools/RefRender.cpp)
    target_compile_definitions(RefRender PRIVATE JUCE_PLUGINHOST_VST3=1 JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0)
    target_link_libraries(RefRender PRIVATE juce::juce_audio_processors juce::juce_recommended_config_flags)
    if(WIN32)
        # films / screenshots a plug-in's editor while audio plays (tools/RefCapture.cpp)
        juce_add_gui_app(RefCapture PRODUCT_NAME "RefCapture")
        target_sources(RefCapture PRIVATE tools/RefCapture.cpp)
        target_compile_definitions(RefCapture PRIVATE JUCE_PLUGINHOST_VST3=1 JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0)
        target_link_libraries(RefCapture PRIVATE juce::juce_audio_processors juce::juce_gui_basics
            juce::juce_recommended_config_flags)
    endif()
endif()
