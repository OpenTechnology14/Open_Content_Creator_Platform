/**
 * Stream Extend OBS Plugin — Main entry point.
 *
 * Free (MIT licensed) OBS Studio plugin that serves as the funnel
 * into the Stream Extend paid app. Features:
 *
 * 1. One-click scene import (loads default scene collection)
 * 2. Auto-create Browser Sources (overlays, alerts, graphics)
 * 3. Encoder auto-configuration (NVENC/AMF/x264 best settings)
 * 4. Menu item to open Stream Extend app
 *
 * This plugin does NOT require Stream Extend to function.
 * It makes OBS setup faster; the app adds remote control + dashboards.
 */

#include <obs-module.h>
#include <obs-frontend-api.h>

/* Forward declarations */
extern void scene_importer_init(void);
extern void browser_source_setup_init(void);
extern void encoder_config_init(void);

OBS_DECLARE_MODULE()
OBS_MODULE_USE_DEFAULT_LOCALE("stream-extend-obs", "en-US")

/* ---------- Menu callbacks ---------- */

static void on_import_scenes(void *data)
{
    (void)data;
    blog(LOG_INFO, "[Stream Extend] Importing default scene collection...");
    /* TODO: Load scenes from bundled JSON */
    scene_importer_init();
}

static void on_setup_browser_sources(void *data)
{
    (void)data;
    blog(LOG_INFO, "[Stream Extend] Setting up Browser Sources...");
    browser_source_setup_init();
}

static void on_configure_encoder(void *data)
{
    (void)data;
    blog(LOG_INFO, "[Stream Extend] Auto-configuring encoder...");
    encoder_config_init();
}

static void on_open_stream_extend(void *data)
{
    (void)data;
    blog(LOG_INFO, "[Stream Extend] Opening Stream Extend app...");

    /* Try to open the Stream Extend app via platform-specific URL scheme */
#ifdef __APPLE__
    system("open 'streamextend://' 2>/dev/null || "
           "open 'https://streamextend.com/download' 2>/dev/null");
#elif _WIN32
    system("start streamextend:// 2>NUL || "
           "start https://streamextend.com/download 2>NUL");
#else
    system("xdg-open 'streamextend://' 2>/dev/null || "
           "xdg-open 'https://streamextend.com/download' 2>/dev/null");
#endif
}

/* ---------- Module lifecycle ---------- */

bool obs_module_load(void)
{
    blog(LOG_INFO, "[Stream Extend] Plugin loaded (v%s)",
         obs_module_get_version());

    /* Register menu items under Tools → Stream Extend */
    obs_frontend_add_tools_menu_item(
        "Stream Extend: Import Scenes",
        on_import_scenes, NULL);

    obs_frontend_add_tools_menu_item(
        "Stream Extend: Setup Browser Sources",
        on_setup_browser_sources, NULL);

    obs_frontend_add_tools_menu_item(
        "Stream Extend: Auto-Configure Encoder",
        on_configure_encoder, NULL);

    obs_frontend_add_tools_menu_item(
        "Stream Extend: Open App",
        on_open_stream_extend, NULL);

    return true;
}

void obs_module_unload(void)
{
    blog(LOG_INFO, "[Stream Extend] Plugin unloaded");
}

const char *obs_module_description(void)
{
    return "Stream Extend — one-click OBS setup, scene import, "
           "Browser Source creation, and encoder configuration. "
           "Free and open source (MIT). "
           "Get the full app at https://streamextend.com";
}
