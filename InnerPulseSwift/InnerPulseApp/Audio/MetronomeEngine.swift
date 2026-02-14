import AVFoundation
import Foundation
import QuartzCore

struct MetronomeState {
    let beat: Int
    let bar: Int
    let isMute: Bool
    let timestamp: TimeInterval
}

struct MetronomeControlState {
    enum ToneMode: String {
        case electronic
        case woody
    }

    var bpm: Int = 120
    var beatsPerBar: Int = 4
    var playBars: Int = 3
    var muteBars: Int = 1
    var randomTraining: Bool = false
    var forcePlay: Bool = false
    var rndPlayMin: Int = 1
    var rndPlayMax: Int = 2
    var rndMuteMin: Int = 1
    var rndMuteMax: Int = 2

    var vMaster: Double = 0.8
    var vAcc: Double = 0.8
    var vBackbeat: Double = 0.0
    var v4th: Double = 0.5
    var v8th: Double = 0.0
    var v16th: Double = 0.0
    var vTrip: Double = 0.0
    var vMuteDim: Double = 0.0

    var muteOptAcc = false
    var muteOptBackbeat = false
    var muteOpt4th = false
    var muteOpt8th = false
    var muteOpt16th = false
    var muteOptTrip = false
    var toneMode: ToneMode = .electronic
}

final class MetronomeEngine {
    private let lock = NSLock()
    private var timer: DispatchSourceTimer?

    private let engine = AVAudioEngine()
    private let accPlayer = AVAudioPlayerNode()
    private let backbeatPlayer = AVAudioPlayerNode()
    private let fourthPlayer = AVAudioPlayerNode()
    private let eighthPlayer = AVAudioPlayerNode()
    private let sixteenthPlayer = AVAudioPlayerNode()
    private let tripletPlayer = AVAudioPlayerNode()
    private var audioGraphConfigured = false

    private var accentBuffer: AVAudioPCMBuffer?
    private var backbeatBuffer: AVAudioPCMBuffer?
    private var quarterBuffer: AVAudioPCMBuffer?
    private var eighthBuffer: AVAudioPCMBuffer?
    private var sixteenthBuffer: AVAudioPCMBuffer?
    private var tripletBuffer: AVAudioPCMBuffer?

    private var tickCount = 0
    private var rndPhase = "play"
    private var rndLeft = 0
    private var control = MetronomeControlState()
    private var loadedToneMode: MetronomeControlState.ToneMode = .electronic

    private(set) var isPlaying = false
    var onBeat: ((MetronomeState) -> Void)?

    func updateControlState(_ newState: MetronomeControlState) {
        lock.lock()
        control = newState
        if audioGraphConfigured, loadedToneMode != newState.toneMode {
            regenerateToneBuffersNoLock(mode: newState.toneMode)
        }
        lock.unlock()
    }

    func start() {
        lock.lock()
        defer { lock.unlock() }
        guard !isPlaying else { return }

        setupAudioIfNeeded()
        do {
            if !engine.isRunning {
                try engine.start()
            }
            for p in allPlayers() where !p.isPlaying {
                p.play()
            }
        } catch {
            print("Audio start error: \(error)")
        }

        tickCount = 0
        rndPhase = "play"
        rndLeft = max(1, control.playBars)
        isPlaying = true

        let timer = DispatchSource.makeTimerSource(queue: DispatchQueue.global(qos: .userInitiated))
        timer.schedule(deadline: .now(), repeating: tickIntervalNoLock())
        timer.setEventHandler { [weak self] in
            self?.advanceTick()
        }
        self.timer = timer
        timer.resume()
    }

    func stop() {
        lock.lock()
        defer { lock.unlock() }
        guard isPlaying else { return }
        timer?.cancel()
        timer = nil
        for p in allPlayers() { p.stop() }
        engine.pause()
        isPlaying = false
    }

    func updateTiming() {
        lock.lock()
        defer { lock.unlock() }
        guard isPlaying else { return }

        timer?.cancel()
        let timer = DispatchSource.makeTimerSource(queue: DispatchQueue.global(qos: .userInitiated))
        timer.schedule(deadline: .now(), repeating: tickIntervalNoLock())
        timer.setEventHandler { [weak self] in
            self?.advanceTick()
        }
        self.timer = timer
        timer.resume()
    }

    private func tickIntervalNoLock() -> DispatchTimeInterval {
        let safeBpm = max(1, control.bpm)
        let seconds = 60.0 / Double(safeBpm) / 12.0
        return .nanoseconds(max(1, Int(seconds * 1_000_000_000.0)))
    }

    private func advanceTick() {
        lock.lock()
        guard isPlaying else {
            lock.unlock()
            return
        }

        let c = control
        let tpb = max(1, 12 * c.beatsPerBar)
        let tick = tickCount % 12
        let bar = (tickCount / tpb) + 1
        let beat = ((tickCount % tpb) / 12) + 1
        let isMute = computeMuteNoLock(bar: bar, tpb: tpb, control: c)
        tickCount += 1
        lock.unlock()

        triggerTickSounds(tick: tick, beat: beat, muted: isMute, control: c)

        if tick == 0 {
            let ts = CACurrentMediaTime()
            DispatchQueue.main.async { [weak self] in
                self?.onBeat?(MetronomeState(beat: beat, bar: bar, isMute: isMute, timestamp: ts))
            }
        }
    }

    private func computeMuteNoLock(bar: Int, tpb: Int, control: MetronomeControlState) -> Bool {
        let atBarHead = (tickCount % tpb) == 0

        if control.randomTraining, atBarHead {
            rndLeft -= 1
            if rndLeft <= 0 {
                rndPhase = (rndPhase == "play") ? "mute" : "play"
                if rndPhase == "play" {
                    rndLeft = Int.random(in: max(1, control.rndPlayMin)...max(max(1, control.rndPlayMin), control.rndPlayMax))
                } else {
                    rndLeft = Int.random(in: max(1, control.rndMuteMin)...max(max(1, control.rndMuteMin), control.rndMuteMax))
                }
            }
        }

        if control.forcePlay { return false }
        if control.randomTraining { return rndPhase == "mute" }

        let cycle = max(1, control.playBars + control.muteBars)
        let offset = (bar - 1) % cycle
        return offset >= control.playBars
    }

    private func triggerTickSounds(tick: Int, beat: Int, muted: Bool, control: MetronomeControlState) {
        let muteScale = muted ? control.vMuteDim : 1.0
        if muteScale <= 0 { return }

        struct Trigger {
            let player: AVAudioPlayerNode
            let buffer: AVAudioPCMBuffer?
            let volume: Double
            let allowedDuringMute: Bool
        }

        var triggers: [Trigger] = []

        if tick == 0 {
            if (beat == 2 || beat == 4) && control.vBackbeat > 0 {
                triggers.append(Trigger(player: backbeatPlayer, buffer: backbeatBuffer, volume: control.vBackbeat, allowedDuringMute: control.muteOptBackbeat))
            }

            if beat == 1 {
                if control.vAcc > 0 {
                    triggers.append(Trigger(player: accPlayer, buffer: accentBuffer, volume: control.vAcc, allowedDuringMute: control.muteOptAcc))
                }
            } else if control.v4th > 0 {
                triggers.append(Trigger(player: fourthPlayer, buffer: quarterBuffer, volume: control.v4th, allowedDuringMute: control.muteOpt4th))
            }
        }

        if tick == 6, control.v8th > 0 {
            triggers.append(Trigger(player: eighthPlayer, buffer: eighthBuffer, volume: control.v8th, allowedDuringMute: control.muteOpt8th))
        }

        if (tick == 3 || tick == 9), control.v16th > 0 {
            triggers.append(Trigger(player: sixteenthPlayer, buffer: sixteenthBuffer, volume: control.v16th, allowedDuringMute: control.muteOpt16th))
        }

        if (tick == 4 || tick == 8), control.vTrip > 0 {
            triggers.append(Trigger(player: tripletPlayer, buffer: tripletBuffer, volume: control.vTrip, allowedDuringMute: control.muteOptTrip))
        }

        for trigger in triggers {
            if muted && !control.forcePlay && !trigger.allowedDuringMute {
                continue
            }
            let gain = Float(max(0, trigger.volume * muteScale * control.vMaster))
            guard gain > 0, let buffer = trigger.buffer else { continue }
            trigger.player.volume = gain
            trigger.player.scheduleBuffer(buffer, at: nil, options: [], completionHandler: nil)
        }
    }

    private func setupAudioIfNeeded() {
        guard !audioGraphConfigured else { return }

        let players = allPlayers()
        for p in players {
            engine.attach(p)
            engine.connect(p, to: engine.mainMixerNode, format: nil)
        }
        audioGraphConfigured = true

        regenerateToneBuffersNoLock(mode: control.toneMode)
    }

    private func allPlayers() -> [AVAudioPlayerNode] {
        [accPlayer, backbeatPlayer, fourthPlayer, eighthPlayer, sixteenthPlayer, tripletPlayer]
    }

    private func regenerateToneBuffersNoLock(mode: MetronomeControlState.ToneMode) {
        let format = engine.mainMixerNode.outputFormat(forBus: 0)
        loadedToneMode = mode

        switch mode {
        case .electronic:
            accentBuffer = makeClickBuffer(format: format, frequency: 1600, duration: 0.045, decay: 42, gain: 1.0)
            backbeatBuffer = makeSnareBuffer(format: format, duration: 0.055, gain: 1.0)
            quarterBuffer = makeClickBuffer(format: format, frequency: 950, duration: 0.035, decay: 36, gain: 1.0)
            eighthBuffer = makeClickBuffer(format: format, frequency: 1250, duration: 0.025, decay: 42, gain: 1.0)
            sixteenthBuffer = makeClickBuffer(format: format, frequency: 760, duration: 0.02, decay: 50, gain: 1.0)
            tripletBuffer = makeClickBuffer(format: format, frequency: 1080, duration: 0.025, decay: 42, gain: 1.0)
        case .woody:
            accentBuffer = makeClickBuffer(format: format, frequency: 620, duration: 0.03, decay: 95, gain: 1.0, harmonic: 2.1)
            backbeatBuffer = makeSnareBuffer(format: format, duration: 0.05, gain: 0.85)
            quarterBuffer = makeClickBuffer(format: format, frequency: 520, duration: 0.025, decay: 110, gain: 0.9, harmonic: 1.95)
            eighthBuffer = makeClickBuffer(format: format, frequency: 880, duration: 0.02, decay: 120, gain: 0.75, harmonic: 2.25)
            sixteenthBuffer = makeClickBuffer(format: format, frequency: 760, duration: 0.018, decay: 130, gain: 0.65, harmonic: 2.4)
            tripletBuffer = makeClickBuffer(format: format, frequency: 700, duration: 0.02, decay: 120, gain: 0.7, harmonic: 2.2)
        }
    }

    private func makeClickBuffer(
        format: AVAudioFormat,
        frequency: Double,
        duration: Double,
        decay: Double,
        gain: Double,
        harmonic: Double = 1.8
    ) -> AVAudioPCMBuffer? {
        let sampleRate = format.sampleRate
        let frameCount = AVAudioFrameCount(max(1, Int(sampleRate * duration)))
        guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frameCount) else {
            return nil
        }

        buffer.frameLength = frameCount
        guard let channels = buffer.floatChannelData else { return nil }
        let channelCount = Int(format.channelCount)

        for i in 0..<Int(frameCount) {
            let t = Double(i) / sampleRate
            let env = exp(-t * decay)
            let fundamental = sin(2.0 * .pi * frequency * t)
            let overtone = 0.35 * sin(2.0 * .pi * frequency * harmonic * t)
            let sample = Float((fundamental + overtone) * env * gain)
            for c in 0..<channelCount {
                channels[c][i] = sample
            }
        }
        return buffer
    }

    private func makeSnareBuffer(format: AVAudioFormat, duration: Double, gain: Double) -> AVAudioPCMBuffer? {
        let sampleRate = format.sampleRate
        let frameCount = AVAudioFrameCount(max(1, Int(sampleRate * duration)))
        guard let buffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: frameCount) else {
            return nil
        }

        buffer.frameLength = frameCount
        guard let channels = buffer.floatChannelData else { return nil }
        let channelCount = Int(format.channelCount)

        for i in 0..<Int(frameCount) {
            let t = Double(i) / sampleRate
            let noise = Double.random(in: -1.0...1.0)
            let body = sin(2.0 * .pi * 220.0 * t) * 0.25
            let env = exp(-t * 34.0)
            let sample = Float((noise * 0.75 + body) * env * gain)
            for c in 0..<channelCount {
                channels[c][i] = sample
            }
        }
        return buffer
    }
}
