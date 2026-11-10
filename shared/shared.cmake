# Code and resources every Orrery plug-in uses: the editor's theme and font, the top-bar controls, menus, dialogs, the
# measured metal knob and the host-keys hand-back. Included from the top-level CMakeLists.txt before the plug-ins.
# Built once as the static library OrreryShared, which every plug-in, test, snapshot and renderer links (it brings the
# JUCE modules, the font and the include path of the repository root: #include "shared/ui/...").
set(SUITE_SHARED_DIR ${CMAKE_CURRENT_LIST_DIR})

# The interface font (Instrument Sans, SIL OFL 1.1; its licence beside it and in packaging/THIRD-PARTY-NOTICES.txt).
juce_add_binary_data(OrreryUiData NAMESPACE OrreryUiData HEADER_NAME OrreryUiData.h
    SOURCES ${SUITE_SHARED_DIR}/resources/fonts/InstrumentSans-Regular.ttf)
set_target_properties(OrreryUiData PROPERTIES POSITION_INDEPENDENT_CODE ON)

add_library(OrreryShared STATIC
    ${SUITE_SHARED_DIR}/ui/MetalKnob.cpp
    ${SUITE_SHARED_DIR}/ui/Widgets.cpp
    ${SUITE_SHARED_DIR}/ui/HostFocus.cpp)
target_include_directories(OrreryShared PUBLIC ${CMAKE_SOURCE_DIR})
set_target_properties(OrreryShared PROPERTIES POSITION_INDEPENDENT_CODE ON)   # linked into shared plug-ins (Linux)
# The JUCE configuration of every target that links it: the plug-ins' objects and this library's must agree on it.
target_compile_definitions(OrreryShared PUBLIC ${SUITE_DEFS})
target_link_libraries(OrreryShared
    PUBLIC OrreryUiData juce::juce_audio_utils juce::juce_dsp
    PRIVATE juce::juce_recommended_config_flags juce::juce_recommended_warning_flags suite_warnings)
