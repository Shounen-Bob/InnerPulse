import AppKit
import SwiftUI

final class StatusBarController: NSObject {
    private var statusItem: NSStatusItem?
    private weak var viewModel: MainViewModel?
    private var floatingPanel: NSPanel?
    private var optionsWindow: NSWindow?
    private var setlistWindow: NSWindow?
    private var keyMonitor: Any?
    private var isConfigured = false

    func configure(with viewModel: MainViewModel) {
        guard !isConfigured else { return }
        isConfigured = true
        self.viewModel = viewModel
        NSApplication.shared.setActivationPolicy(.accessory)

        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = item.button {
            button.image = NSImage(systemSymbolName: "metronome", accessibilityDescription: "InnerPulse")
            button.imagePosition = .imageOnly
            button.target = self
            button.action = #selector(handleStatusItemClick(_:))
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }
        statusItem = item

        keyMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            guard let self, let vm = self.viewModel else { return event }
            if event.keyCode == 49 { // space
                vm.togglePlayback()
                return nil
            }
            return event
        }
    }

    @objc
    private func handleStatusItemClick(_ sender: NSStatusBarButton) {
        guard let event = NSApp.currentEvent else {
            togglePendulumWindow()
            return
        }

        if event.type == .rightMouseUp || event.modifierFlags.contains(.option) {
            presentMenu()
        } else {
            togglePendulumWindow()
        }
    }

    private func presentMenu() {
        let menu = NSMenu()

        let toggleItem = NSMenuItem(
            title: (floatingPanel?.isVisible == true) ? "Hide Pendulum" : "Show Pendulum",
            action: #selector(menuTogglePendulum),
            keyEquivalent: ""
        )
        toggleItem.target = self
        menu.addItem(toggleItem)

        let playTitle = (viewModel?.isPlaying == true) ? "Stop (Space)" : "Start (Space)"
        let playItem = NSMenuItem(title: playTitle, action: #selector(menuTogglePlayback), keyEquivalent: " ")
        playItem.target = self
        menu.addItem(playItem)

        menu.addItem(.separator())

        let optItem = NSMenuItem(title: "Options", action: #selector(menuOpenOptions), keyEquivalent: ",")
        optItem.target = self
        menu.addItem(optItem)

        let setlistItem = NSMenuItem(title: "Setlist", action: #selector(menuOpenSetlist), keyEquivalent: "s")
        setlistItem.target = self
        menu.addItem(setlistItem)

        menu.addItem(.separator())

        let quitItem = NSMenuItem(title: "Quit InnerPulse", action: #selector(menuQuit), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)

        statusItem?.menu = menu
        statusItem?.button?.performClick(nil)
        statusItem?.menu = nil
    }

    @objc private func menuTogglePendulum() { togglePendulumWindow() }

    @objc private func menuTogglePlayback() { viewModel?.togglePlayback() }

    @objc private func menuOpenOptions() { openOptionsWindow() }
    @objc private func menuOpenSetlist() { openSetlistWindow() }

    @objc private func menuQuit() {
        NSApp.terminate(nil)
    }

    private func togglePendulumWindow() {
        guard let panel = ensureFloatingPanel() else { return }

        if panel.isVisible {
            panel.orderOut(nil)
        } else {
            placePanelNearTopRightIfNeeded(panel)
            panel.orderFrontRegardless()
        }
    }

    private func ensureFloatingPanel() -> NSPanel? {
        if let panel = floatingPanel {
            return panel
        }
        guard let vm = viewModel else { return nil }

        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 248, height: 318),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.isOpaque = false
        panel.backgroundColor = .clear
        panel.level = .floating
        panel.hasShadow = true
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.isMovableByWindowBackground = true
        panel.hidesOnDeactivate = false

        let root = FloatingPendulumView(
            viewModel: vm,
            onOptions: { [weak self] in self?.openOptionsWindow() }
        )
        panel.contentView = NSHostingView(rootView: root)

        floatingPanel = panel
        return panel
    }

    private func placePanelNearTopRightIfNeeded(_ panel: NSPanel) {
        guard panel.frame.origin == .zero else { return }
        guard let screen = NSScreen.main else { return }
        let vf = screen.visibleFrame
        let x = vf.maxX - panel.frame.width - 18
        let y = vf.maxY - panel.frame.height - 28
        panel.setFrameOrigin(NSPoint(x: x, y: y))
    }

    private func openOptionsWindow() {
        NSApp.activate(ignoringOtherApps: true)

        if let win = optionsWindow {
            win.makeKeyAndOrderFront(nil)
            return
        }
        guard let vm = viewModel else { return }
        let win = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 390, height: 660),
            styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        win.title = "InnerPulse Options"
        win.titlebarAppearsTransparent = true
        win.titleVisibility = .hidden
        win.isOpaque = false
        win.backgroundColor = NSColor.black.withAlphaComponent(0.18)
        win.center()
        win.contentView = NSHostingView(rootView: MainView(
            viewModel: vm,
            showVisualizer: false,
            onOpenSetlist: { [weak self] in self?.openSetlistWindow() }
        ))
        win.isReleasedWhenClosed = false
        win.delegate = self
        win.makeKeyAndOrderFront(nil)
        optionsWindow = win
    }

    private func openSetlistWindow() {
        NSApp.activate(ignoringOtherApps: true)

        if let win = setlistWindow {
            win.makeKeyAndOrderFront(nil)
            return
        }
        guard let vm = viewModel else { return }
        let win = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 520, height: 520),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        win.title = "Setlist"
        win.center()
        win.contentView = NSHostingView(rootView: NavigationStack {
            SetlistEditorView(setlist: Binding(
                get: { vm.setlist },
                set: { vm.setlist = $0 }
            ))
        })
        win.isReleasedWhenClosed = false
        win.delegate = self
        win.makeKeyAndOrderFront(nil)
        setlistWindow = win
    }
}

extension StatusBarController: NSWindowDelegate {
    func windowWillClose(_ notification: Notification) {
        if let win = notification.object as? NSWindow, win == optionsWindow {
            optionsWindow = nil
        }
        if let win = notification.object as? NSWindow, win == setlistWindow {
            setlistWindow = nil
        }
    }
}

private struct FloatingPendulumView: View {
    @ObservedObject var viewModel: MainViewModel
    let onOptions: () -> Void
    @State private var bpmText = ""
    private let panelOpacityScale = 1.2

    var body: some View {
        ZStack(alignment: .topTrailing) {
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(Color.black.opacity(0.18 * panelOpacityScale))
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(Color.white.opacity(0.28 * panelOpacityScale), lineWidth: 1)
                )

            VStack(spacing: 10) {
                HStack(spacing: 4) {
                    Button(action: { viewModel.previousSong() }) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 10, weight: .bold))
                            .frame(width: 20, height: 20)
                            .background(Color.white.opacity(0.14), in: RoundedRectangle(cornerRadius: 6, style: .continuous))
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(.white)

                    Text(viewModel.currentSongTitle)
                        .font(.system(size: 11, weight: .semibold, design: .rounded))
                        .lineLimit(1)
                        .truncationMode(.tail)
                        .frame(maxWidth: .infinity)
                        .foregroundStyle(.white.opacity(0.9))

                    Button(action: { viewModel.nextSong() }) {
                        Image(systemName: "chevron.right")
                            .font(.system(size: 10, weight: .bold))
                            .frame(width: 20, height: 20)
                            .background(Color.white.opacity(0.14), in: RoundedRectangle(cornerRadius: 6, style: .continuous))
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(.white)

                    Button(action: onOptions) {
                        Image(systemName: "slider.horizontal.3")
                            .font(.system(size: 12, weight: .bold))
                            .frame(width: 22, height: 22)
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(.white)
                }
                .padding(.horizontal, 10)
                .padding(.top, 10)

                HStack(spacing: 6) {
                    Text("Beat \(viewModel.currentBeat)")
                        .font(.system(size: 12, weight: .bold, design: .rounded))
                        .foregroundStyle(.white.opacity(0.85))
                    Text("•")
                        .foregroundStyle(.white.opacity(0.28))
                    Text("\(viewModel.bpm) BPM / \(viewModel.beatsPerBar)/4")
                        .font(.system(size: 11, weight: .semibold, design: .monospaced))
                        .foregroundStyle(.white.opacity(0.72))
                    Spacer()
                }
                .padding(.horizontal, 10)

                BarVisualizerView(
                    phase: viewModel.visualPhase,
                    isPlaying: viewModel.isPlaying,
                    beat: viewModel.currentBeat,
                    isMute: viewModel.isMute,
                    showBeatLabel: false
                )
                .frame(height: 182)
                .padding(.horizontal, 8)
                .contentShape(Rectangle())
                .onTapGesture {
                    viewModel.togglePlayback()
                }

                HStack(spacing: 8) {
                    HStack(spacing: 6) {
                        Text("BPM")
                            .font(.system(size: 11, weight: .bold, design: .rounded))
                            .foregroundStyle(.white.opacity(0.74))
                        Button("-") {
                            viewModel.bpm = max(40, viewModel.bpm - 1)
                            bpmText = "\(viewModel.bpm)"
                        }
                        .buttonStyle(.plain)
                        .frame(width: 20, height: 20)
                        .background(Color.white.opacity(0.14), in: RoundedRectangle(cornerRadius: 6, style: .continuous))

                        TextField("", text: $bpmText)
                            .textFieldStyle(.plain)
                            .multilineTextAlignment(.center)
                            .font(.system(size: 16, weight: .black, design: .monospaced))
                            .foregroundStyle(.white)
                            .frame(width: 42)
                            .onChange(of: bpmText) { newValue in
                                let digitsOnly = newValue.filter(\.isNumber)
                                if digitsOnly != newValue {
                                    bpmText = digitsOnly
                                }
                            }
                            .onSubmit {
                                if let v = Int(bpmText) {
                                    viewModel.bpm = min(300, max(40, v))
                                }
                                bpmText = "\(viewModel.bpm)"
                            }

                        Button("+") {
                            viewModel.bpm = min(300, viewModel.bpm + 1)
                            bpmText = "\(viewModel.bpm)"
                        }
                        .buttonStyle(.plain)
                        .frame(width: 20, height: 20)
                        .background(Color.white.opacity(0.14), in: RoundedRectangle(cornerRadius: 6, style: .continuous))
                    }
                    .frame(maxWidth: .infinity)
                }
                .padding(.horizontal, 10)
                .padding(.bottom, 10)
            }
        }
        .frame(width: 248, height: 318)
        .background(Color.clear)
        .onAppear {
            bpmText = "\(viewModel.bpm)"
        }
        .onChange(of: viewModel.bpm) { value in
            bpmText = "\(value)"
        }
        .help("Click: Start/Stop | Space: Start/Stop | Gear: Open Options")
    }
}
