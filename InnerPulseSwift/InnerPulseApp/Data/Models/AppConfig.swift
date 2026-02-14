import Foundation

struct AppConfig: Codable, Equatable {
    var audioDevice: String = ""
    var bufferSize: String = "128"
    var tone: String = "electronic"
    var bpm: Int = 120
    var bpb: Int = 4
    var playBars: Int = 3
    var muteBars: Int = 1
    var rndPlayMin: Int = 1
    var rndPlayMax: Int = 2
    var rndMuteMin: Int = 1
    var rndMuteMax: Int = 2
    var backgroundOpacity: Int = 18
    var launchAtLogin: Bool = false

    enum CodingKeys: String, CodingKey {
        case audioDevice = "audio_device"
        case bufferSize = "buffer_size"
        case tone
        case bpm
        case bpb
        case playBars = "play"
        case muteBars = "mute"
        case rndPlayMin = "rnd_play_min"
        case rndPlayMax = "rnd_play_max"
        case rndMuteMin = "rnd_mute_min"
        case rndMuteMax = "rnd_mute_max"
        case backgroundOpacity = "background_opacity"
        case launchAtLogin = "launch_at_login"
    }

    init() {}

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        audioDevice = try c.decodeIfPresent(String.self, forKey: .audioDevice) ?? ""
        bufferSize = try c.decodeIfPresent(String.self, forKey: .bufferSize) ?? "128"
        tone = try c.decodeIfPresent(String.self, forKey: .tone) ?? "electronic"
        bpm = try c.decodeIfPresent(Int.self, forKey: .bpm) ?? 120
        bpb = try c.decodeIfPresent(Int.self, forKey: .bpb) ?? 4
        playBars = try c.decodeIfPresent(Int.self, forKey: .playBars) ?? 3
        muteBars = try c.decodeIfPresent(Int.self, forKey: .muteBars) ?? 1
        rndPlayMin = try c.decodeIfPresent(Int.self, forKey: .rndPlayMin) ?? 1
        rndPlayMax = try c.decodeIfPresent(Int.self, forKey: .rndPlayMax) ?? 2
        rndMuteMin = try c.decodeIfPresent(Int.self, forKey: .rndMuteMin) ?? 1
        rndMuteMax = try c.decodeIfPresent(Int.self, forKey: .rndMuteMax) ?? 2
        backgroundOpacity = min(
            100, max(0, try c.decodeIfPresent(Int.self, forKey: .backgroundOpacity) ?? 18))
        launchAtLogin = try c.decodeIfPresent(Bool.self, forKey: .launchAtLogin) ?? false
    }
}
