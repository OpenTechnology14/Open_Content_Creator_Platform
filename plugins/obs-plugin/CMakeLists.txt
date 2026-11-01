cmake_minimum_required(VERSION 3.16)
project(stream-extend-obs-plugin VERSION 0.1.0 LANGUAGES C)

# --- OBS SDK ---
# Set OBS_SOURCE_DIR to your OBS Studio source checkout, or install
# libobs-dev and let find_package locate it.

find_package(libobs QUIET)
if(NOT libobs_FOUND)
    message(STATUS "libobs not found via find_package — using OBS_SOURCE_DIR fallback")
    if(NOT DEFINED OBS_SOURCE_DIR)
        message(FATAL_ERROR
            "OBS SDK not found. Set -DOBS_SOURCE_DIR=/path/to/obs-studio "
            "or install libobs-dev."
        )
    endif()
    include_directories(${OBS_SOURCE_DIR}/libobs)
    link_directories(${OBS_SOURCE_DIR}/build/libobs)
endif()

# --- Plugin library ---
add_library(stream-extend-obs MODULE
    src/plugin-main.c
    src/scene-importer.c
    src/browser-source-setup.c
    src/encoder-config.c
)

target_link_libraries(stream-extend-obs PRIVATE obs)

# --- Install ---
if(APPLE)
    set_target_properties(stream-extend-obs PROPERTIES
        PREFIX ""
        SUFFIX ".so"
    )
    install(TARGETS stream-extend-obs
        LIBRARY DESTINATION "$ENV{HOME}/Library/Application Support/obs-studio/plugins/stream-extend-obs/bin"
    )
elseif(WIN32)
    install(TARGETS stream-extend-obs
        RUNTIME DESTINATION "obs-plugins/64bit"
    )
else()
    install(TARGETS stream-extend-obs
        LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}/obs-plugins"
    )
endif()
