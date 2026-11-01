/**
 * Browser Source Setup — auto-creates Browser Sources for overlays.
 *
 * Creates Browser Source entries in the current scene collection
 * pointing to the platform's overlay endpoints:
 *
 * - NodeCG alerts (http://localhost:9091/bundles/hcp-alerts/graphics/alerts.html)
 * - Stream info overlay (http://localhost:8000/overlays/stream-info)
 * - Sponsor rotation (http://localhost:8000/overlays/sponsors)
 * - Chat overlay (http://localhost:8000/overlays/chat)
 */

#include <obs-module.h>
#include <obs.h>

struct browser_source_def {
    const char *name;
    const char *url;
    int width;
    int height;
};

static const struct browser_source_def default_sources[] = {
    {
        "SE: Alerts",
        "http://localhost:9091/bundles/hcp-alerts/graphics/alerts.html",
        1920, 1080
    },
    {
        "SE: Stream Info",
        "http://localhost:8000/overlays/stream-info",
        400, 120
    },
    {
        "SE: Sponsors",
        "http://localhost:8000/overlays/sponsors",
        300, 80
    },
    {
        "SE: Chat",
        "http://localhost:8000/overlays/chat",
        400, 600
    },
};

static const int num_sources =
    sizeof(default_sources) / sizeof(default_sources[0]);

void browser_source_setup_init(void)
{
    obs_source_t *current_scene_source = obs_frontend_get_current_scene();
    if (!current_scene_source) {
        blog(LOG_WARNING,
             "[Stream Extend] No active scene — cannot add Browser Sources");
        return;
    }

    obs_scene_t *scene = obs_scene_from_source(current_scene_source);
    if (!scene) {
        obs_source_release(current_scene_source);
        blog(LOG_WARNING,
             "[Stream Extend] Current source is not a scene");
        return;
    }

    for (int i = 0; i < num_sources; i++) {
        const struct browser_source_def *def = &default_sources[i];

        /* Check if source already exists */
        obs_source_t *existing = obs_get_source_by_name(def->name);
        if (existing) {
            blog(LOG_INFO,
                 "[Stream Extend] Browser source '%s' already exists, skipping",
                 def->name);
            obs_source_release(existing);
            continue;
        }

        /* Create Browser Source settings */
        obs_data_t *settings = obs_data_create();
        obs_data_set_string(settings, "url", def->url);
        obs_data_set_int(settings, "width", def->width);
        obs_data_set_int(settings, "height", def->height);
        obs_data_set_bool(settings, "shutdown", true);
        obs_data_set_bool(settings, "restart_when_active", false);

        /* Create the source */
        obs_source_t *source = obs_source_create(
            "browser_source", def->name, settings, NULL);

        if (source) {
            /* Add to current scene */
            obs_scene_add(scene, source);
            blog(LOG_INFO,
                 "[Stream Extend] Created Browser Source: %s -> %s",
                 def->name, def->url);
            obs_source_release(source);
        } else {
            blog(LOG_WARNING,
                 "[Stream Extend] Failed to create Browser Source: %s",
                 def->name);
        }

        obs_data_release(settings);
    }

    obs_source_release(current_scene_source);

    blog(LOG_INFO,
         "[Stream Extend] Browser Source setup complete — %d sources configured",
         num_sources);
}
