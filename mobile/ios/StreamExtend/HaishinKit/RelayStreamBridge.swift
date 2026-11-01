/**
 * RelayStreamBridge — Connects mobile streaming to the relay.
 *
 * When the user has a subscription (Connect tier+), this bridge:
 * 1. Receives start/stop commands from the relay (remote control)
 * 2. Reports stream stats to the relay
 * 3. Forwards push notifications for stream alerts
 * 4. Allows the desktop app to control the mobile camera
 *
 * This is what makes the mobile app useful as a "remote camera"
 * that the desktop Stream Extend app can control.
 */

import Foundation

/// Bridge between the relay WebSocket connection and the stream manager.
class RelayStreamBridge: ObservableObject {
    private let streamManager: StreamManager
    private var webSocketTask: URLSessionWebSocketTask?
    private var isConnected = false

    @Published var relayConnected = false
    @Published var subscriptionTier: String = "free"

    // Relay URLs
    private let hostedRelayURL = "wss://relay.streamextend.com/ws"
    private var selfHostedURL: String?
    private var jwt: String?

    init(streamManager: StreamManager) {
        self.streamManager = streamManager
    }

    // MARK: - Connection

    /// Connect to hosted relay with JWT.
    func connectHosted(jwt: String) {
        self.jwt = jwt
        self.selfHostedURL = nil
        connect(url: hostedRelayURL, token: jwt)
    }

    /// Connect to self-hosted relay.
    func connectSelfHosted(url: String, apiKey: String?) {
        self.selfHostedURL = url
        let wsURL = url.replacingOccurrences(of: "https://", with: "wss://")
            .replacingOccurrences(of: "http://", with: "ws://")
        let finalURL = wsURL.hasSuffix("/ws") ? wsURL : wsURL + "/ws"
        connect(url: finalURL, token: apiKey)
    }

    /// Disconnect from relay.
    func disconnect() {
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        isConnected = false
        relayConnected = false
    }

    // MARK: - Private

    private func connect(url: String, token: String?) {
        guard let wsURL = URL(string: url) else { return }

        let session = URLSession(configuration: .default)
        webSocketTask = session.webSocketTask(with: wsURL)
        webSocketTask?.resume()

        // Send auth
        let authMsg: [String: Any] = [
            "Auth": ["jwt": token ?? ""]
        ]
        if let data = try? JSONSerialization.data(withJSONObject: authMsg),
           let str = String(data: data, encoding: .utf8) {
            webSocketTask?.send(.string(str)) { _ in }
        }

        // Start receiving
        receiveMessages()
    }

    private func receiveMessages() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self else { return }

            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self.handleMessage(text)
                default:
                    break
                }
                // Continue receiving
                self.receiveMessages()

            case .failure(let error):
                print("[RelayBridge] WebSocket error: \(error)")
                DispatchQueue.main.async {
                    self.relayConnected = false
                }
            }
        }
    }

    private func handleMessage(_ text: String) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else { return }

        if let authOk = json["AuthOk"] as? [String: Any] {
            DispatchQueue.main.async {
                self.relayConnected = true
                if let sub = authOk["subscription"] as? [String: Any] {
                    self.subscriptionTier = sub["tier"] as? String ?? "free"
                }
            }
        } else if let command = json["Command"] as? [String: Any] {
            handleCommand(command)
        } else if json["Pong"] != nil {
            // Heartbeat response — ignore
        }
    }

    private func handleCommand(_ command: [String: Any]) {
        guard let action = command["action"] as? String else { return }

        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }

            switch action {
            case "start_stream":
                self.streamManager.startStream()
            case "stop_stream":
                self.streamManager.stopStream()
            case "switch_camera":
                self.streamManager.switchCamera()
            case "toggle_mute":
                self.streamManager.toggleMute()
            case "set_bitrate":
                if let payload = command["payload"] as? [String: Any],
                   let kbps = payload["bitrate"] as? Int {
                    self.streamManager.setBitrate(kbps)
                }
            default:
                print("[RelayBridge] Unknown command: \(action)")
            }
        }
    }

    /// Send stream stats to relay (called periodically).
    func reportStats() {
        guard isConnected else { return }

        let stats = streamManager.stats
        let msg: [String: Any] = [
            "MetricsBatch": [
                "metrics": [
                    ["name": "stream_bitrate_kbps", "value": stats.currentBitrate, "timestamp": Int(Date().timeIntervalSince1970)],
                    ["name": "stream_fps", "value": stats.fps, "timestamp": Int(Date().timeIntervalSince1970)],
                    ["name": "stream_dropped_frames", "value": stats.droppedFrames, "timestamp": Int(Date().timeIntervalSince1970)],
                ]
            ]
        ]

        if let data = try? JSONSerialization.data(withJSONObject: msg),
           let str = String(data: data, encoding: .utf8) {
            webSocketTask?.send(.string(str)) { _ in }
        }
    }
}
