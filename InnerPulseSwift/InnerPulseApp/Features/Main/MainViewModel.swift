import Foundation
import QuartzCore

final class MainViewModel: ObservableObject {
    enum ToneMode: String, CaseIterable {
        case electronic
        case woody
    }

    @Published var bpm: Int { didSet { guard !isBootstrapping else { return }; syncTempo() } }
    @Published var beatsPerBar: Int { didSet { guard !isBootstrapping else { return }; syncTempo() } }
    @Published var playBars: Int { didSet { guard !isBootstrapping else { return }; syncTrainingOptions() } }
    @Published var muteBars: Int { didSet { guard !isBootstrapping else { return }; syncTrainingOptions() } }
    @Published var randomTraining: Bool { didSet { guard !isBootstrapping else { return }; syncTrainingOptions() } }
    @Published var forcePlay: Bool { didSet { guard !isBootstrapping else { return }; syncTrainingOptions() } }
    @Published var rndPlayMin: Int { didSet { guard !isBootstrapping else { return }; syncTrainingOptions() } }
    @Published var rndPlayMax: Int { didSet { guard !isBootstrapping else { return }; syncTrainingOptions() } }
    @Published var rndMuteMin: Int { didSet { guard !isBootstrapping else { return }; syncTrainingOptions() } }
    @Published var rndMuteMax: Int { didSet { guard !isBootstrapping else { return }; syncTrainingOptions() } }
    @Published var vMaster: Double { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var vAcc: Double { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var vBackbeat: Double { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var v4th: Double { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var v8th: Double { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var v16th: Double { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var vTrip: Double { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var vMuteDim: Double { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var muteOptAcc: Bool { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var muteOptBackbeat: Bool { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var muteOpt4th: Bool { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var muteOpt8th: Bool { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var muteOpt16th: Bool { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var muteOptTrip: Bool { didSet { guard !isBootstrapping else { return }; syncMixOptions() } }
    @Published var toneMode: ToneMode { didSet { guard !isBootstrapping else { return }; syncToneOptions() } }
    @Published var isPlaying = false
    @Published var currentBeat = 1
    @Published var currentBar = 1
    @Published var isMute = false
    @Published var visualPhase: Double = -1.0
    @Published var isLogPresented = false
    @Published var logs: [String] = []
    @Published var isSetlistPresented = false
    @Published var setlist: [Song] { didSet { guard !isBootstrapping else { return }; persistSetlistChanges() } }
    @Published var setlistIndex: Int

    private let appState: AppState
    private let engine = MetronomeEngine()
    private var isBootstrapping = true
    private var visualTimer: DispatchSourceTimer?
    private var phaseAnchorBeat: Double = 0.0
    private var phaseAnchorTime: TimeInterval?
    private var lastBeatTimestamp: TimeInterval?

    init(appState: AppState) {
        self.appState = appState
        self.bpm = appState.config.bpm
        self.beatsPerBar = appState.config.bpb
        self.playBars = appState.config.playBars
        self.muteBars = appState.config.muteBars
        self.randomTraining = false
        self.forcePlay = false
        self.rndPlayMin = appState.config.rndPlayMin
        self.rndPlayMax = appState.config.rndPlayMax
        self.rndMuteMin = appState.config.rndMuteMin
        self.rndMuteMax = appState.config.rndMuteMax
        self.vMaster = 0.8
        self.vAcc = 0.8
        self.vBackbeat = 0.0
        self.v4th = 0.5
        self.v8th = 0.0
        self.v16th = 0.0
        self.vTrip = 0.0
        self.vMuteDim = 0.0
        self.muteOptAcc = false
        self.muteOptBackbeat = false
        self.muteOpt4th = false
        self.muteOpt8th = false
        self.muteOpt16th = false
        self.muteOptTrip = false
        self.toneMode = ToneMode(rawValue: appState.config.tone) ?? .electronic
        self.setlist = appState.setlist
        self.setlistIndex = appState.setlistIndex

        engine.onBeat = { [weak self] state in
            guard let self else { return }
            self.currentBeat = state.beat
            self.currentBar = state.bar
            self.isMute = state.isMute
            self.appendTimingLog(state: state)
        }
        isBootstrapping = false
    }

    func togglePlayback() {
        if isPlaying {
            engine.stop()
            stopVisualClock()
            isPlaying = false
            currentBeat = 1
            currentBar = 1
            isMute = false
            visualPhase = -1.0
            log("[STOP]")
        } else {
            applyToEngine()
            engine.start()
            startVisualClock(reset: true)
            isPlaying = true
            lastBeatTimestamp = nil
            logs.removeAll(keepingCapacity: true)
            log("[START] BPM:\(bpm)")
        }
    }

    private func syncTempo() {
        reanchorVisualPhaseForTempoChange()
        applyToEngine()
        engine.updateTiming()
        saveConfig()
    }

    private func syncTrainingOptions() {
        if rndPlayMax < rndPlayMin { rndPlayMax = rndPlayMin }
        if rndMuteMax < rndMuteMin { rndMuteMax = rndMuteMin }
        applyToEngine()
        saveConfig()
    }

    private func syncMixOptions() {
        applyToEngine()
    }

    private func syncToneOptions() {
        applyToEngine()
        saveConfig()
    }

    func toggleLogWindow() {
        isLogPresented.toggle()
    }

    func previousSong() {
        guard !setlist.isEmpty else { return }
        setlistIndex = (setlistIndex - 1 + setlist.count) % setlist.count
        applySong()
    }

    func nextSong() {
        guard !setlist.isEmpty else { return }
        setlistIndex = (setlistIndex + 1) % setlist.count
        applySong()
    }

    private func persistSetlistChanges() {
        appState.setlist = setlist
        appState.saveSetlist()
    }

    var currentSongTitle: String {
        guard !setlist.isEmpty else { return "No Song" }
        return "\(setlistIndex + 1). \(setlist[setlistIndex].name)"
    }

    private func applySong() {
        guard setlist.indices.contains(setlistIndex) else { return }
        let song = setlist[setlistIndex]
        bpm = song.bpm
        beatsPerBar = song.bpb
        syncTempo()
        appState.setlistIndex = setlistIndex
    }

    private func applyToEngine() {
        var state = MetronomeControlState()
        state.bpm = bpm
        state.beatsPerBar = beatsPerBar
        state.playBars = playBars
        state.muteBars = muteBars
        state.randomTraining = randomTraining
        state.forcePlay = forcePlay
        state.rndPlayMin = rndPlayMin
        state.rndPlayMax = rndPlayMax
        state.rndMuteMin = rndMuteMin
        state.rndMuteMax = rndMuteMax
        state.vMaster = vMaster
        state.vAcc = vAcc
        state.vBackbeat = vBackbeat
        state.v4th = v4th
        state.v8th = v8th
        state.v16th = v16th
        state.vTrip = vTrip
        state.vMuteDim = vMuteDim
        state.muteOptAcc = muteOptAcc
        state.muteOptBackbeat = muteOptBackbeat
        state.muteOpt4th = muteOpt4th
        state.muteOpt8th = muteOpt8th
        state.muteOpt16th = muteOpt16th
        state.muteOptTrip = muteOptTrip
        state.toneMode = (toneMode == .woody) ? .woody : .electronic
        engine.updateControlState(state)
    }

    private func saveConfig() {
        appState.config.bpm = bpm
        appState.config.bpb = beatsPerBar
        appState.config.playBars = playBars
        appState.config.muteBars = muteBars
        appState.config.rndPlayMin = rndPlayMin
        appState.config.rndPlayMax = rndPlayMax
        appState.config.rndMuteMin = rndMuteMin
        appState.config.rndMuteMax = rndMuteMax
        appState.config.tone = toneMode.rawValue
        appState.saveConfig()
    }

    private func startVisualClock(reset: Bool) {
        if reset || phaseAnchorTime == nil {
            phaseAnchorBeat = 0.0
            phaseAnchorTime = CACurrentMediaTime()
            visualPhase = 0.0
        }
        visualTimer?.cancel()
        let timer = DispatchSource.makeTimerSource(queue: .main)
        timer.schedule(deadline: .now(), repeating: .milliseconds(16))
        timer.setEventHandler { [weak self] in
            guard let self else { return }
            self.visualPhase = self.currentVisualPhase()
        }
        visualTimer = timer
        timer.resume()
    }

    private func stopVisualClock() {
        visualTimer?.cancel()
        visualTimer = nil
        phaseAnchorTime = nil
        phaseAnchorBeat = 0.0
    }

    private func reanchorVisualPhaseForTempoChange() {
        guard isPlaying else { return }
        let nowPhase = currentVisualPhase()
        phaseAnchorBeat = nowPhase
        phaseAnchorTime = CACurrentMediaTime()
        visualPhase = nowPhase
    }

    private func currentVisualPhase() -> Double {
        guard let anchorTime = phaseAnchorTime else { return -1.0 }
        let elapsed = CACurrentMediaTime() - anchorTime
        return phaseAnchorBeat + elapsed * Double(max(1, bpm)) / 60.0
    }

    private func visualPhase(at timestamp: TimeInterval) -> Double {
        guard let anchorTime = phaseAnchorTime else { return -1.0 }
        let elapsed = timestamp - anchorTime
        return phaseAnchorBeat + elapsed * Double(max(1, bpm)) / 60.0
    }

    private func appendTimingLog(state: MetronomeState) {
        let dfText: String
        if let last = lastBeatTimestamp {
            let expected = 60.0 / Double(max(1, bpm))
            let dfMs = (state.timestamp - last - expected) * 1000.0
            dfText = String(format: "%+.1fms", dfMs)
        } else {
            dfText = "N/A"
        }
        lastBeatTimestamp = state.timestamp

        let phase = visualPhase(at: state.timestamp)
        let angle = 30.0 * cos(phase * .pi)
        let visErr = 30.0 - abs(angle)
        let mode = state.isMute ? "MUTE" : "PLAY"
        log(String(format: "[%@] Bar:%d Beat:%d (Df:%@) | Vis:%.4f°", mode, state.bar, state.beat, dfText, visErr))
    }

    private func log(_ message: String) {
        logs.append(message)
        if logs.count > 400 {
            logs.removeFirst(logs.count - 400)
        }
    }
}
