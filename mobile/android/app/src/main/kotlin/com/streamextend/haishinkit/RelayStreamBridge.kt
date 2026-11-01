/**
 * RelayStreamBridge — Connects mobile streaming to the relay on Android.
 *
 * Android counterpart to the iOS RelayStreamBridge.
 * Receives remote commands and reports stats via the relay WebSocket.
 */

package com.streamextend.haishinkit

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import okhttp3.*
import org.json.JSONObject

/**
 * Bridge between the relay WebSocket and the stream manager.
 */
class RelayStreamBridge(
    private val streamManager: StreamManager,
    private val scope: CoroutineScope = CoroutineScope(Dispatchers.IO),
) {
    private val _relayConnected = MutableStateFlow(false)
    val relayConnected: StateFlow<Boolean> = _relayConnected.asStateFlow()

    private val _subscriptionTier = MutableStateFlow("free")
    val subscriptionTier: StateFlow<String> = _subscriptionTier.asStateFlow()

    private var webSocket: WebSocket? = null
    private val client = OkHttpClient()

    companion object {
        private const val HOSTED_RELAY_URL = "wss://relay.streamextend.com/ws"
    }

    /**
     * Connect to hosted relay with JWT.
     */
    fun connectHosted(jwt: String) {
        connect(HOSTED_RELAY_URL, jwt)
    }

    /**
     * Connect to self-hosted relay.
     */
    fun connectSelfHosted(url: String, apiKey: String?) {
        val wsUrl = url
            .replace("https://", "wss://")
            .replace("http://", "ws://")
            .let { if (it.endsWith("/ws")) it else "$it/ws" }
        connect(wsUrl, apiKey)
    }

    /**
     * Disconnect from relay.
     */
    fun disconnect() {
        webSocket?.close(1000, "Client disconnect")
        webSocket = null
        _relayConnected.value = false
    }

    /**
     * Send stream stats to relay.
     */
    fun reportStats() {
        if (!_relayConnected.value) return

        val stats = streamManager.stats.value
        val timestamp = System.currentTimeMillis() / 1000

        val msg = JSONObject().apply {
            put("MetricsBatch", JSONObject().apply {
                put("metrics", org.json.JSONArray().apply {
                    put(JSONObject().apply {
                        put("name", "stream_bitrate_kbps")
                        put("value", stats.currentBitrate)
                        put("timestamp", timestamp)
                    })
                    put(JSONObject().apply {
                        put("name", "stream_fps")
                        put("value", stats.fps)
                        put("timestamp", timestamp)
                    })
                    put(JSONObject().apply {
                        put("name", "stream_dropped_frames")
                        put("value", stats.droppedFrames)
                        put("timestamp", timestamp)
                    })
                })
            })
        }

        webSocket?.send(msg.toString())
    }

    // ---- Private ----

    private fun connect(url: String, token: String?) {
        val request = Request.Builder().url(url).build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                // Send auth
                val auth = JSONObject().apply {
                    put("Auth", JSONObject().apply {
                        put("jwt", token ?: "")
                    })
                }
                webSocket.send(auth.toString())
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                handleMessage(text)
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                _relayConnected.value = false
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                _relayConnected.value = false
            }
        })
    }

    private fun handleMessage(text: String) {
        try {
            val json = JSONObject(text)

            when {
                json.has("AuthOk") -> {
                    _relayConnected.value = true
                    val sub = json.getJSONObject("AuthOk")
                        .optJSONObject("subscription")
                    _subscriptionTier.value = sub?.optString("tier", "free") ?: "free"
                }

                json.has("Command") -> {
                    val cmd = json.getJSONObject("Command")
                    handleCommand(cmd)
                }

                json.has("Pong") -> {
                    // Heartbeat — ignore
                }
            }
        } catch (e: Exception) {
            // Ignore malformed messages
        }
    }

    private fun handleCommand(command: JSONObject) {
        val action = command.optString("action", "")

        scope.launch(Dispatchers.Main) {
            when (action) {
                "start_stream" -> streamManager.startStream()
                "stop_stream" -> streamManager.stopStream()
                "switch_camera" -> streamManager.switchCamera()
                "toggle_mute" -> streamManager.toggleMute()
                "set_bitrate" -> {
                    val payload = command.optJSONObject("payload")
                    val kbps = payload?.optInt("bitrate", 6000) ?: 6000
                    streamManager.setBitrate(kbps)
                }
            }
        }
    }
}
