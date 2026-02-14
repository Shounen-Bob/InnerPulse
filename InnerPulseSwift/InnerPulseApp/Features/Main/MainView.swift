import AppKit
import SwiftUI

struct MainView: View {
    @ObservedObject var viewModel: MainViewModel
    let showVisualizer: Bool
    let onOpenSetlist: (() -> Void)?
    let onClose: (() -> Void)?
    let onQuit: (() -> Void)?
    @State private var activeSheet: ActiveSheet?
    @State private var keyMonitor: Any?

    private enum ActiveSheet: Int, Identifiable {
        case muteOptions
        case randomOptions
        case log

        var id: Int { rawValue }
    }

    private enum Palette {
        static let bgTop = Color(red: 0.09, green: 0.10, blue: 0.14)
        static let bgBottom = Color(red: 0.04, green: 0.05, blue: 0.07)
        static let optionsTop = Color(red: 0.08, green: 0.09, blue: 0.12)
        static let optionsBottom = Color(red: 0.03, green: 0.04, blue: 0.06)
        static let panel = Color.white.opacity(0.06)
        static let panelStroke = Color.white.opacity(0.12)
        static let accent = Color.cyan
        static let warning = Color.orange
    }

    private var isOptionsMode: Bool { !showVisualizer }
    private var optionsOpacity: Double { viewModel.backgroundOpacityFraction }

    var body: some View {
        ZStack {
            if isOptionsMode {
                LinearGradient(
                    colors: [Palette.optionsTop, Palette.optionsBottom], startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .opacity(0.08 + optionsOpacity * 0.92)
                .ignoresSafeArea()
                Circle()
                    .fill(Palette.accent.opacity(0.02 + optionsOpacity * 0.09))
                    .frame(width: 320, height: 320)
                    .blur(radius: 24)
                    .offset(x: 120, y: -220)
            } else {
                LinearGradient(
                    colors: [Palette.bgTop, Palette.bgBottom], startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
            }

            VStack(spacing: isOptionsMode ? 4 : 8) {
                if !isOptionsMode {
                    topHeader
                }
                if showVisualizer {
                    visualizerCard
                }
                controlsCard
                mixerCard
                bottomRow
            }
            .padding(.horizontal, isOptionsMode ? 6 : 10)
            .padding(.vertical, isOptionsMode ? 2 : 10)
            .background(
                RoundedRectangle(cornerRadius: isOptionsMode ? 18 : 0, style: .continuous)
                    .fill(isOptionsMode ? Color.black.opacity(optionsOpacity * 0.14) : Color.clear)
            )
            .overlay(
                RoundedRectangle(cornerRadius: isOptionsMode ? 18 : 0, style: .continuous)
                    .stroke(
                        isOptionsMode ? Color.white.opacity(0.04 + optionsOpacity * 0.16) : Color.clear,
                        lineWidth: 1)
            )
            .padding(isOptionsMode ? 0 : 0)
        }
        .sheet(item: $activeSheet) { sheet in
            switch sheet {
            case .muteOptions:
                NavigationStack {
                    Form {
                        Section("Sounds Allowed During Mute Bars") {
                            Toggle("Accent", isOn: $viewModel.muteOptAcc)
                            Toggle("Backbeat", isOn: $viewModel.muteOptBackbeat)
                            Toggle("Quarter (4th)", isOn: $viewModel.muteOpt4th)
                            Toggle("Eighth (8th)", isOn: $viewModel.muteOpt8th)
                            Toggle("Sixteenth (16th)", isOn: $viewModel.muteOpt16th)
                            Toggle("Triplet", isOn: $viewModel.muteOptTrip)
                        }
                    }
                    .navigationTitle("Mute Rules")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Close") { activeSheet = nil }
                        }
                    }
                }
                .frame(minWidth: 340, minHeight: 320)
            case .randomOptions:
                NavigationStack {
                    Form {
                        Section("Normal (Play) Bars") {
                            Text("Min/Max bars to keep metronome audible in Random mode.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Stepper(
                                "Min: \(viewModel.rndPlayMin)", value: $viewModel.rndPlayMin,
                                in: 1...16)
                            Stepper(
                                "Max: \(viewModel.rndPlayMax)", value: $viewModel.rndPlayMax,
                                in: 1...16)
                        }
                        Section("Mute Bars") {
                            Text("Min/Max bars to mute in Random mode.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Stepper(
                                "Min: \(viewModel.rndMuteMin)", value: $viewModel.rndMuteMin,
                                in: 1...16)
                            Stepper(
                                "Max: \(viewModel.rndMuteMax)", value: $viewModel.rndMuteMax,
                                in: 1...16)
                        }
                    }
                    .navigationTitle("Random Settings")
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Close") { activeSheet = nil }
                        }
                    }
                }
                .frame(minWidth: 340, minHeight: 300)
            case .log:
                NavigationStack {
                    LogView(logs: viewModel.logs)
                        .toolbar {
                            ToolbarItem(placement: .cancellationAction) {
                                Button("Close") { activeSheet = nil }
                            }
                        }
                }
                .frame(minWidth: 520, maxWidth: .infinity, minHeight: 360, maxHeight: .infinity)
            }
        }
        .onAppear {
            installHotkeys()
        }
        .onDisappear {
            removeHotkeys()
        }
    }

    private var topHeader: some View {
        card {
            VStack(spacing: isOptionsMode ? 9 : 6) {
                HStack(spacing: 8) {
                    if isOptionsMode {
                        Image(systemName: "slider.horizontal.3")
                            .font(.system(size: 13, weight: .heavy))
                            .frame(width: 24, height: 24)
                            .background(
                                Palette.accent.opacity(0.2),
                                in: RoundedRectangle(cornerRadius: 7, style: .continuous))
                        VStack(alignment: .leading, spacing: 2) {
                            Text("InnerPulse Options")
                                .font(.system(size: 14, weight: .bold, design: .rounded))
                                .foregroundStyle(.white)
                            Text("Session controls and mixer setup")
                                .font(.system(size: 10, weight: .semibold, design: .rounded))
                                .foregroundStyle(.white.opacity(0.58))
                        }
                        Spacer()
                    } else {
                        compactButton("chevron.left") { viewModel.previousSong() }
                        Text(viewModel.currentSongTitle)
                            .font(.system(size: 13, weight: .semibold, design: .rounded))
                            .lineLimit(1)
                            .frame(maxWidth: .infinity)
                        compactButton("chevron.right") { viewModel.nextSong() }
                    }
                }

                HStack {
                    Text("Bar: \(viewModel.currentBar)")
                        .font(.system(size: 12, weight: .bold, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.75))
                    Spacer()
                    if viewModel.forcePlay {
                        Text("MUTE OFF")
                            .font(.system(size: 11, weight: .bold, design: .rounded))
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Palette.warning.opacity(0.24), in: Capsule())
                            .foregroundStyle(Palette.warning)
                    }
                    Text(viewModel.isMute ? "MUTE" : "PLAY")
                        .font(.system(size: 11, weight: .bold, design: .rounded))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(
                            (viewModel.isMute ? Palette.warning : Palette.accent).opacity(0.2),
                            in: Capsule()
                        )
                        .foregroundStyle(viewModel.isMute ? Palette.warning : Palette.accent)
                }
            }
        }
    }

    private var visualizerCard: some View {
        card {
            BarVisualizerView(
                phase: viewModel.visualPhase,
                isPlaying: viewModel.isPlaying,
                beat: viewModel.currentBeat,
                isMute: viewModel.isMute,
                showBeatLabel: true
            )
        }
    }

    private var controlsCard: some View {
        card {
            VStack(spacing: 7) {
                if isOptionsMode {
                    sectionTitle("Tempo")
                }
                HStack(spacing: 7) {
                    SpinBoxLikeControl(title: "BPM", value: $viewModel.bpm, range: 40...300)
                    SpinBoxLikeControl(title: "BEATS", value: $viewModel.beatsPerBar, range: 1...8)
                }

                if isOptionsMode {
                    sectionTitle("Training")
                }
                HStack(spacing: 7) {
                    SpinBoxLikeControl(title: "PLAY", value: $viewModel.playBars, range: 1...16)
                    SpinBoxLikeControl(title: "MUTE", value: $viewModel.muteBars, range: 0...16)
                }

                HStack(spacing: 8) {
                    Toggle("Random", isOn: $viewModel.randomTraining)
                        .toggleStyle(.switch)
                    Toggle("Mute Off", isOn: $viewModel.forcePlay)
                        .toggleStyle(.switch)
                }
                .font(.system(size: 12, weight: .semibold, design: .rounded))
                .tint(Palette.accent)
                .foregroundStyle(.white.opacity(0.92))

                if isOptionsMode {
                    sectionTitle("Tone")
                    HStack(spacing: 6) {
                        toneButton("Electronic", isActive: viewModel.toneMode == .electronic) {
                            viewModel.toneMode = .electronic
                        }
                        toneButton("Woody", isActive: viewModel.toneMode == .woody) {
                            viewModel.toneMode = .woody
                        }
                    }

                    sectionTitle("System")
                    VStack(spacing: 7) {
                        HStack(spacing: 8) {
                            Text("Background")
                                .font(.system(size: 11, weight: .bold, design: .rounded))
                                .foregroundStyle(.white.opacity(0.82))
                            Slider(
                                value: Binding(
                                    get: { Double(viewModel.backgroundOpacity) },
                                    set: { viewModel.backgroundOpacity = Int($0.rounded()) }
                                ),
                                in: 0...100,
                                step: 1
                            )
                            .tint(Palette.accent)
                            Text("\(viewModel.backgroundOpacity)%")
                                .font(.system(size: 11, weight: .bold, design: .monospaced))
                                .foregroundStyle(.white.opacity(0.86))
                                .frame(width: 44, alignment: .trailing)
                        }
                        Text("100% = 不透過")
                            .font(.system(size: 10, weight: .semibold, design: .rounded))
                            .foregroundStyle(.white.opacity(0.55))
                            .frame(maxWidth: .infinity, alignment: .leading)

                        Toggle("Mac起動時にInnerPulseを起動", isOn: $viewModel.launchAtLogin)
                            .toggleStyle(.switch)
                            .font(.system(size: 12, weight: .semibold, design: .rounded))
                            .tint(Palette.accent)
                            .foregroundStyle(.white.opacity(0.92))
                    }
                }

                if !isOptionsMode {
                    miniAction("RANDOM OPT") { activeSheet = .randomOptions }
                }
            }
        }
    }

    private var mixerCard: some View {
        card {
            VStack(spacing: 5) {
                if isOptionsMode {
                    sectionTitle("Mixer")
                }
                HStack(spacing: 5) {
                    VerticalSlider(
                        title: "MST", value: $viewModel.vMaster, range: 0...1, labelColor: .white)
                    VerticalSlider(
                        title: "ACC", value: $viewModel.vAcc, range: 0...1, labelColor: .yellow)
                    VerticalSlider(
                        title: "BACK", value: $viewModel.vBackbeat, range: 0...1, labelColor: .pink)
                    VerticalSlider(
                        title: "4TH", value: $viewModel.v4th, range: 0...1, labelColor: .cyan)
                    VerticalSlider(
                        title: "8TH", value: $viewModel.v8th, range: 0...1, labelColor: .mint)
                    VerticalSlider(
                        title: "16T", value: $viewModel.v16th, range: 0...1, labelColor: .blue)
                    VerticalSlider(
                        title: "TRP", value: $viewModel.vTrip, range: 0...1, labelColor: .purple)
                    VerticalSlider(
                        title: "MUTE", value: $viewModel.vMuteDim, range: 0...1, labelColor: .gray)
                }
            }
        }
    }

    private var bottomRow: some View {
        VStack(spacing: 6) {
            if !isOptionsMode {
                Button(viewModel.isPlaying ? "STOP" : "START") {
                    viewModel.togglePlayback()
                }
                .keyboardShortcut(.space, modifiers: [])
                .font(.system(size: 17, weight: .heavy, design: .rounded))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
                .background(
                    viewModel.isPlaying ? Palette.warning : Palette.accent,
                    in: RoundedRectangle(cornerRadius: 11, style: .continuous)
                )
                .foregroundStyle(.black)
            }

            if isOptionsMode {
                let cols = Array(repeating: GridItem(.flexible(), spacing: 6), count: 3)
                LazyVGrid(columns: cols, spacing: 6) {
                    optionAction("MUTE RULES", icon: "speaker.slash") { activeSheet = .muteOptions }
                    optionAction("RANDOM", icon: "shuffle") { activeSheet = .randomOptions }
                    optionAction("SETLIST", icon: "music.note.list") { onOpenSetlist?() }
                    optionAction("LOG", icon: "doc.text.magnifyingglass") { activeSheet = .log }
                    optionAction("CLOSE", icon: "xmark.circle") { onClose?() }
                    optionAction("QUIT", icon: "power") { onQuit?() }
                }
            } else {
                HStack(spacing: 6) {
                    miniAction("MUTE RULES") { activeSheet = .muteOptions }
                    miniAction("SETLIST") { onOpenSetlist?() }
                    miniAction("LOG") { activeSheet = .log }
                        .keyboardShortcut("l", modifiers: [])
                }
            }
        }
    }

    private func compactButton(_ systemName: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: systemName)
                .font(.system(size: 11, weight: .bold))
                .frame(width: 24, height: 22)
                .background(
                    Color.white.opacity(0.10),
                    in: RoundedRectangle(cornerRadius: 8, style: .continuous))
        }
        .buttonStyle(.plain)
        .foregroundStyle(.white)
    }

    private func miniAction(_ title: String, action: @escaping () -> Void) -> some View {
        Button(title, action: action)
            .font(.system(size: 11, weight: .bold, design: .rounded))
            .tracking(0.4)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 9)
            .background(
                LinearGradient(
                    colors: [
                        Color.white.opacity(isOptionsMode ? 0.20 : 0.18),
                        Color.white.opacity(isOptionsMode ? 0.08 : 0.06),
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                ),
                in: RoundedRectangle(cornerRadius: 9, style: .continuous)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 9, style: .continuous)
                    .stroke(
                        LinearGradient(
                            colors: [Color.white.opacity(0.34), Color.white.opacity(0.10)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1
                    )
            )
            .foregroundStyle(.white)
            .shadow(color: .black.opacity(0.30), radius: 4, y: 2)
    }

    private func optionAction(_ title: String, icon: String, action: @escaping () -> Void)
        -> some View
    {
        Button(action: action) {
            Label(title, systemImage: icon)
                .font(.system(size: 10, weight: .bold, design: .rounded))
                .lineLimit(1)
                .minimumScaleFactor(0.85)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 8)
        }
        .buttonStyle(.plain)
        .background(
            LinearGradient(
                colors: [Color.white.opacity(0.20), Color.white.opacity(0.08)],
                startPoint: .top,
                endPoint: .bottom
            ),
            in: RoundedRectangle(cornerRadius: 9, style: .continuous)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 9, style: .continuous)
                .stroke(Color.white.opacity(0.22), lineWidth: 1)
        )
        .foregroundStyle(.white)
        .shadow(color: .black.opacity(0.28), radius: 4, y: 2)
    }

    private func toneButton(_ title: String, isActive: Bool, action: @escaping () -> Void)
        -> some View
    {
        Button(action: action) {
            Text(title)
                .font(.system(size: 11, weight: .bold, design: .rounded))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 7)
        }
        .buttonStyle(.plain)
        .background(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .fill(isActive ? Palette.accent.opacity(0.28) : Color.white.opacity(0.08))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .stroke(
                    isActive ? Palette.accent.opacity(0.9) : Color.white.opacity(0.18), lineWidth: 1
                )
        )
        .foregroundStyle(isActive ? Color.cyan.opacity(0.95) : Color.white.opacity(0.90))
    }

    private func card<Content: View>(@ViewBuilder content: () -> Content) -> some View {
        content()
            .padding(isOptionsMode ? 4 : 8)
            .frame(maxWidth: .infinity)
            .background(
                RoundedRectangle(cornerRadius: 13, style: .continuous)
                    .fill(
                        isOptionsMode
                            ? LinearGradient(
                                colors: [
                                    Color.white.opacity(0.01 + optionsOpacity * 0.06),
                                    Color.white.opacity(optionsOpacity * 0.02),
                                ],
                                startPoint: .topLeading, endPoint: .bottomTrailing)
                            : LinearGradient(
                                colors: [Palette.panel, Palette.panel], startPoint: .top,
                                endPoint: .bottom)
                    )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 13, style: .continuous)
                    .stroke(
                        isOptionsMode ? Color.white.opacity(0.03 + optionsOpacity * 0.14) : Palette.panelStroke,
                        lineWidth: 1)
            )
            .shadow(color: isOptionsMode ? .black.opacity(0.28) : .clear, radius: 5, y: 2)
    }

    private func sectionTitle(_ title: String) -> some View {
        Text(title.uppercased())
            .font(.system(size: 10, weight: .black, design: .rounded))
            .kerning(0.8)
            .foregroundStyle(.white.opacity(0.55))
            .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func installHotkeys() {
        guard keyMonitor == nil else { return }
        keyMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { event in
            guard let chars = event.charactersIgnoringModifiers?.lowercased() else {
                return event
            }
            if chars == "l" {
                activeSheet = .log
                return nil
            }
            return event
        }
    }

    private func removeHotkeys() {
        if let m = keyMonitor {
            NSEvent.removeMonitor(m)
            keyMonitor = nil
        }
    }
}
