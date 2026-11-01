/**
 * Encoder Auto-Configuration.
 *
 * Detects the best available encoder (NVENC > AMF > QSV > x264)
 * and applies streaming-optimized settings.
 *
 * Target: 1080p60 at 6000 kbps CBR (Twitch-optimized defaults).
 * Falls back to lower settings if hardware can't handle it.
 */

#include <obs-module.h>
#include <obs.h>

/* Encoder preference order */
static const char *encoder_priority[] = {
    "jim_nvenc",           /* NVIDIA NVENC (OBS fork) */
    "ffmpeg_nvenc",        /* NVIDIA NVENC (FFmpeg) */
    "h264_texture_amf",    /* AMD AMF */
    "obs_qsv11",           /* Intel Quick Sync */
    "obs_x264",            /* Software x264 (fallback) */
    NULL
};

/**
 * Find the best available encoder.
 */
static const char *find_best_encoder(void)
{
    for (int i = 0; encoder_priority[i] != NULL; i++) {
        const char *id = encoder_priority[i];

        /* Check if this encoder is available on the system */
        if (obs_get_encoder_type(id) != OBS_ENCODER_VIDEO) {
            continue;
        }

        blog(LOG_INFO,
             "[Stream Extend] Found encoder: %s", id);
        return id;
    }

    /* Should always have x264 */
    return "obs_x264";
}

void encoder_config_init(void)
{
    const char *encoder_id = find_best_encoder();
    bool is_hardware = (strcmp(encoder_id, "obs_x264") != 0);

    blog(LOG_INFO,
         "[Stream Extend] Selected encoder: %s (%s)",
         encoder_id, is_hardware ? "hardware" : "software");

    /*
     * Apply recommended settings via OBS config.
     *
     * These match Twitch's recommended settings:
     * - 1080p60 for hardware encoders
     * - 720p60 for x264 (CPU can't handle 1080p60 on most systems)
     * - CBR at 6000 kbps (Twitch limit for non-partners)
     * - Keyframe interval: 2 seconds
     */

    obs_data_t *settings = obs_data_create();

    if (is_hardware) {
        /* Hardware encoder settings */
        obs_data_set_string(settings, "rate_control", "CBR");
        obs_data_set_int(settings, "bitrate", 6000);
        obs_data_set_int(settings, "keyint_sec", 2);
        obs_data_set_string(settings, "preset", "Quality");
        obs_data_set_string(settings, "profile", "high");

        blog(LOG_INFO,
             "[Stream Extend] Encoder config: CBR 6000kbps, 1080p60, "
             "Quality preset, High profile");
    } else {
        /* x264 software settings — more conservative */
        obs_data_set_string(settings, "rate_control", "CBR");
        obs_data_set_int(settings, "bitrate", 4500);
        obs_data_set_int(settings, "keyint_sec", 2);
        obs_data_set_string(settings, "preset", "veryfast");
        obs_data_set_string(settings, "profile", "high");
        obs_data_set_string(settings, "tune", "zerolatency");

        blog(LOG_INFO,
             "[Stream Extend] Encoder config: CBR 4500kbps, 720p60, "
             "veryfast preset, High profile, zerolatency");
    }

    /*
     * TODO: Apply settings to OBS output configuration.
     *
     * This requires modifying the streaming output's encoder settings
     * via obs_output_set_video_encoder() or by updating the OBS
     * profile config files directly.
     *
     * For now, log the recommended settings. A future version will
     * apply them via the OBS Frontend API when OBS 31+ provides
     * a stable config API for this.
     */

    obs_data_release(settings);

    blog(LOG_INFO,
         "[Stream Extend] Encoder configuration logged. "
         "Apply via OBS Settings → Output → Streaming.");
}
