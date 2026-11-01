/**
 * StreamManager — HaishinKit RTMP/SRT streaming from Android.
 *
 * Android counterpart to the iOS StreamManager.
 * Uses HaishinKit.kt (Kotlin port) for RTMP/SRT streaming.
 *
 * Dependencies:
 * - HaishinKit.kt: implementation("com.github.shogo4405:HaishinKit.kt:x.x.x")
 *   https://github.com/shogo4405/HaishinKit.kt
 */

package com.streamextend.haishinkit

import android.content.Context
import android.hardware.camera2.CameraManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Stream configuration.
 */
data class StreamConfig(
    var rtmpUrl: String = "",
    var streamKey: String = "",
    var protocol: StreamProtocol = StreamProtocol.RTMP,
    var resolution: StreamResolution = StreamResolution.HD1080,
    var bitrate: Int = 6000,  // kbps
    var fps: Int = 30,
    var useBackCamera: Boolean = true,
    var audioEnabled: Boolean = true,
) {
    enum class StreamProtocol { RTMP, SRT }

    enum class StreamResolution(val width: Int, val height: Int) {
        HD720(1280, 720),
        HD1080(1920, 1080),
        UHD4K(3840, 2160),
    }
}

/**
 * Stream state.
 */
sealed class StreamState {
    data object Idle : StreamState()
    data object Connecting : StreamState()
    data object Streaming : StreamState()
    data object Reconnecting : StreamState()
    data class Error(val message: String) : StreamState()
}

/**
 * Stream statistics.
 */
data class StreamStats(
    val bytesOut: Long = 0,
    val currentBitrate: Double = 0.0,
    val droppedFrames: Int = 0,
    val fps: Double = 0.0,
    val uptime: Long = 0,  // seconds
)

/**
 * Manages the RTMP/SRT stream lifecycle on Android.
 */
class StreamManager(private val context: Context) {
    private val _state = MutableStateFlow<StreamState>(StreamState.Idle)
    val state: StateFlow<StreamState> = _state.asStateFlow()

    private val _stats = MutableStateFlow(StreamStats())
    val stats: StateFlow<StreamStats> = _stats.asStateFlow()

    private var config = StreamConfig()

    // HaishinKit objects (initialized on first stream)
    // private var rtmpConnection: RtmpConnection? = null
    // private var rtmpStream: RtmpStream? = null

    /**
     * Configure stream settings.
     */
    fun configure(config: StreamConfig) {
        this.config = config
    }

    /**
     * Start streaming.
     */
    fun startStream() {
        if (_state.value !is StreamState.Idle) return
        _state.value = StreamState.Connecting

        when (config.protocol) {
            StreamConfig.StreamProtocol.RTMP -> startRTMP()
            StreamConfig.StreamProtocol.SRT -> startSRT()
        }
    }

    /**
     * Stop streaming.
     */
    fun stopStream() {
        // TODO: Close HaishinKit connection
        // rtmpConnection?.close()
        // rtmpStream = null
        // rtmpConnection = null
        _state.value = StreamState.Idle
    }

    /**
     * Switch between front and back camera.
     */
    fun switchCamera() {
        config = config.copy(useBackCamera = !config.useBackCamera)
        // TODO: Reattach camera via HaishinKit
    }

    /**
     * Toggle audio mute.
     */
    fun toggleMute() {
        config = config.copy(audioEnabled = !config.audioEnabled)
        // TODO: Attach/detach audio source
    }

    /**
     * Update bitrate mid-stream.
     */
    fun setBitrate(kbps: Int) {
        config = config.copy(bitrate = kbps)
        // TODO: Update HaishinKit video settings
    }

    // ---- Private ----

    private fun startRTMP() {
        /*
         * TODO: Implement with HaishinKit.kt
         *
         * val connection = RtmpConnection()
         * val stream = RtmpStream(connection)
         *
         * stream.videoSetting.apply {
         *     width = config.resolution.width
         *     height = config.resolution.height
         *     bitRate = config.bitrate * 1000
         * }
         *
         * stream.audioSetting.apply {
         *     bitRate = 128_000
         * }
         *
         * // Attach camera
         * val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
         * val cameraId = if (config.useBackCamera) "0" else "1"
         * stream.attachCamera(cameraManager, cameraId)
         *
         * // Attach audio
         * if (config.audioEnabled) {
         *     stream.attachAudio(AudioRecordSource(context))
         * }
         *
         * // Connect
         * connection.connect(config.rtmpUrl)
         * stream.publish(config.streamKey)
         *
         * _state.value = StreamState.Streaming
         */

        _state.value = StreamState.Error("RTMP implementation pending — add HaishinKit.kt dependency")
    }

    private fun startSRT() {
        _state.value = StreamState.Error("SRT not yet implemented — use RTMP")
    }
}
