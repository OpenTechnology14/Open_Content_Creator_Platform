/**
 * StreamManager — HaishinKit RTMP/SRT streaming from iOS.
 *
 * Turns the iPhone into a mobile streaming camera that connects
 * to the relay or directly to RTMP/SRT ingest endpoints.
 *
 * Features:
 * - RTMP streaming to Twitch/YouTube/custom endpoints
 * - SRT streaming for low-latency applications
 * - Camera switching (front/back)
 * - Audio from device mic or external
 * - Bitrate/resolution control
 * - Background streaming support
 * - Relay integration for remote start/stop
 *
 * Dependencies:
 * - HaishinKit (Swift Package Manager)
 *   https://github.com/shogo4405/HaishinKit.swift
 */

import Foundation
import AVFoundation
import HaishinKit

/// Stream configuration.
struct StreamConfig {
    var rtmpUrl: String = ""
    var streamKey: String = ""
    var protocol: StreamProtocol = .rtmp
    var resolution: StreamResolution = .hd1080
    var bitrate: Int = 6000  // kbps
    var fps: Int = 30
    var useBackCamera: Bool = true
    var audioEnabled: Bool = true

    enum StreamProtocol {
        case rtmp
        case srt
    }

    enum StreamResolution {
        case hd720   // 1280x720
        case hd1080  // 1920x1080
        case uhd4k   // 3840x2160 (only on capable devices)

        var width: Int {
            switch self {
            case .hd720: return 1280
            case .hd1080: return 1920
            case .uhd4k: return 3840
            }
        }

        var height: Int {
            switch self {
            case .hd720: return 720
            case .hd1080: return 1080
            case .uhd4k: return 2160
            }
        }
    }
}

/// Stream state.
enum StreamState {
    case idle
    case connecting
    case streaming
    case reconnecting
    case error(String)
}

/// Manages the RTMP/SRT stream lifecycle.
class StreamManager: ObservableObject {
    @Published var state: StreamState = .idle
    @Published var stats: StreamStats = StreamStats()

    private var rtmpConnection: RTMPConnection?
    private var rtmpStream: RTMPStream?
    private var config: StreamConfig

    struct StreamStats {
        var bytesOut: Int64 = 0
        var currentBitrate: Double = 0
        var droppedFrames: Int = 0
        var fps: Double = 0
        var uptime: TimeInterval = 0
    }

    init(config: StreamConfig = StreamConfig()) {
        self.config = config
    }

    // MARK: - Public API

    /// Configure stream settings.
    func configure(_ config: StreamConfig) {
        self.config = config
    }

    /// Start streaming.
    func startStream() {
        guard case .idle = state else { return }
        state = .connecting

        switch config.protocol {
        case .rtmp:
            startRTMP()
        case .srt:
            startSRT()
        }
    }

    /// Stop streaming.
    func stopStream() {
        rtmpConnection?.close()
        rtmpStream = nil
        rtmpConnection = nil
        state = .idle
    }

    /// Switch between front and back camera.
    func switchCamera() {
        config.useBackCamera.toggle()
        guard let stream = rtmpStream else { return }

        let position: AVCaptureDevice.Position = config.useBackCamera ? .back : .front
        stream.attachCamera(AVCaptureDevice.default(
            .builtInWideAngleCamera,
            for: .video,
            position: position
        ))
    }

    /// Toggle audio mute.
    func toggleMute() {
        config.audioEnabled.toggle()
        rtmpStream?.attachAudio(config.audioEnabled ? AVCaptureDevice.default(for: .audio) : nil)
    }

    /// Update bitrate mid-stream.
    func setBitrate(_ kbps: Int) {
        config.bitrate = kbps
        rtmpStream?.videoSettings.bitRate = kbps * 1000
    }

    // MARK: - Private

    private func startRTMP() {
        let connection = RTMPConnection()
        let stream = RTMPStream(connection: connection)

        // Video settings
        stream.videoSettings = VideoCodecSettings(
            videoSize: .init(
                width: Int32(config.resolution.width),
                height: Int32(config.resolution.height)
            ),
            bitRate: config.bitrate * 1000,
            maxKeyFrameIntervalDuration: 2
        )

        // Audio settings
        stream.audioSettings = AudioCodecSettings(
            bitRate: 128 * 1000
        )

        // Attach camera
        let position: AVCaptureDevice.Position = config.useBackCamera ? .back : .front
        stream.attachCamera(AVCaptureDevice.default(
            .builtInWideAngleCamera,
            for: .video,
            position: position
        ))

        // Attach audio
        if config.audioEnabled {
            stream.attachAudio(AVCaptureDevice.default(for: .audio))
        }

        // Connect
        let fullUrl = config.rtmpUrl.hasSuffix("/")
            ? config.rtmpUrl + config.streamKey
            : config.rtmpUrl + "/" + config.streamKey

        connection.connect(fullUrl)
        stream.publish("")

        self.rtmpConnection = connection
        self.rtmpStream = stream
        self.state = .streaming
    }

    private func startSRT() {
        // TODO: Implement SRT via HaishinKit's SRTStream
        // SRT provides lower latency than RTMP and is preferred
        // for professional applications.
        state = .error("SRT not yet implemented — use RTMP")
    }
}
