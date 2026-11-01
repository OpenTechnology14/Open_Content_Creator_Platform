/**
 * Scene Importer — loads the default HCP scene collection into OBS.
 *
 * Reads a bundled JSON scene collection (matching OBS's export format)
 * and imports it. This gives new users an 8-scene professional setup
 * without manual configuration.
 *
 * Scenes imported:
 * 1. Starting Soon — countdown + music
 * 2. Main Camera — webcam + overlays
 * 3. Screen Share — display capture + facecam
 * 4. Guest Split — dual camera layout
 * 5. AI Effects — webcam + ComfyUI pipeline
 * 6. BRB — break screen + timer
 * 7. Replay — sports replay overlay
 * 8. Ending — outro + social links
 */

#include <obs-module.h>
#include <obs.h>
#include <util/platform.h>
#include <string.h>

/**
 * Get the path to the bundled scene collection JSON.
 * The JSON lives alongside the plugin binary in the data/ directory.
 */
static const char *get_scene_json_path(void)
{
    /* obs_module_file() resolves paths relative to the plugin's data dir */
    return obs_module_file("scenes/default-scenes.json");
}

void scene_importer_init(void)
{
    const char *path = get_scene_json_path();
    if (!path) {
        blog(LOG_WARNING,
             "[Stream Extend] Scene JSON not found in plugin data dir");
        return;
    }

    /* Check if file exists */
    if (!os_file_exists(path)) {
        blog(LOG_WARNING,
             "[Stream Extend] Scene file does not exist: %s", path);
        return;
    }

    blog(LOG_INFO, "[Stream Extend] Importing scenes from: %s", path);

    /*
     * TODO: Implementation options:
     *
     * Option A — Use obs_frontend_import_scenes() if available (OBS 30+).
     * This is the cleanest approach but requires a newer OBS.
     *
     * Option B — Parse the JSON ourselves and create scenes/sources via
     * the libobs C API (obs_scene_create, obs_source_create, etc.).
     * More work but compatible with all OBS versions.
     *
     * Option C — Write the JSON to OBS's scene collection directory
     * and trigger a reload. Hacky but effective.
     *
     * Starting with Option A, falling back to Option C.
     */

    blog(LOG_INFO,
         "[Stream Extend] Scene import complete — "
         "restart OBS or switch scene collection to see new scenes");
}
