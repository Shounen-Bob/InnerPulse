import AppKit
import Combine
import SwiftUI

final class AppController: NSObject {
    private weak var viewModel: MainViewModel?
    private var mainWindow: NSWindow?
    private var optionsWindow: NSWindow?
    private var setlistWindow: NSWindow?
    private var statusItem: NSStatusItem?
    private var keyMonitor: Any?
    private var cancellables = Set<AnyCancellable>()
    private var isConfigured = false

    func configure(with viewModel: MainViewModel) {
        guard !isConfigured else { return }
        isConfigured = true
        self.viewModel = viewModel

        // Menu bar resident app (no Dock icon).
        NSApplication.shared.setActivationPolicy(.accessory)
        installStatusItem()

        // Local monitor (when app is active/focused)
        keyMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            guard let self, let vm = self.viewModel else { return event }
            // Space: Toggle Playback
            if event.keyCode == 49 {
                vm.togglePlayback()
                return nil
            }
            // Left/Right arrows: Setlist navigation
            if event.keyCode == 123 {
                vm.previousSong()
                return nil
            }
            if event.keyCode == 124 {
                vm.nextSong()
                return nil
            }
            // r: Toggle Random
            if event.charactersIgnoringModifiers == "r" {
                vm.toggleRandom()
                return nil
            }
            // m: Toggle Mute
            if event.charactersIgnoringModifiers == "m" {
                vm.toggleMute()
                return nil
            }
            // s: Open Setlist
            if event.charactersIgnoringModifiers == "s" {
                self.openSetlistWindow()
                return nil
            }
            return event
        }

        // Open main window immediately
        DispatchQueue.main.async {
            self.showMainWindow()
            NSApp.activate(ignoringOtherApps: true)
        }

        viewModel.$backgroundOpacity
            .receive(on: RunLoop.main)
            .sink { [weak self, weak viewModel] _ in
                guard let self, let vm = viewModel else { return }
                self.optionsWindow?.backgroundColor = NSColor.black.withAlphaComponent(
                    vm.backgroundOpacityFraction)
            }
            .store(in: &cancellables)
    }

    // handleGlobalKey is removed as global key monitoring for a floating panel is no longer relevant
    // in a standard app window setup. Local key events will handle interactions when the app is active.

    deinit {
        if let m = keyMonitor {
            NSEvent.removeMonitor(m)
        }
    }

    private func showMainWindow() {
        guard let win = ensureMainWindow() else { return }
        viewModel?.setInterfaceActive(true)
        NSApp.activate(ignoringOtherApps: true)
        win.makeKeyAndOrderFront(nil)
    }

    private func installStatusItem() {
        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        if let button = item.button {
            button.image = NSImage(systemSymbolName: "metronome.fill", accessibilityDescription: "InnerPulse")
            button.imagePosition = .imageOnly
            button.target = self
            button.action = #selector(handleStatusItemClick(_:))
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }

        statusItem = item
    }

    @objc
    private func handleStatusItemClick(_ sender: Any?) {
        if NSApp.currentEvent?.type == .rightMouseUp {
            presentStatusMenu()
            return
        }

        if let win = mainWindow, win.isVisible {
            win.orderOut(nil)
            refreshInterfaceActivity()
        } else {
            showMainWindow()
        }
    }

    private func presentStatusMenu() {
        let menu = NSMenu()
        let visible = mainWindow?.isVisible == true
        let toggleTitle = visible ? "Hide" : "Open"
        let toggleItem = NSMenuItem(title: toggleTitle, action: #selector(toggleFromMenu), keyEquivalent: "")
        toggleItem.target = self
        menu.addItem(toggleItem)

        let quitItem = NSMenuItem(title: "Quit", action: #selector(quitApp), keyEquivalent: "q")
        quitItem.target = self
        menu.addItem(quitItem)

        statusItem?.menu = menu
        statusItem?.button?.performClick(nil)
        statusItem?.menu = nil
    }

    @objc
    private func toggleFromMenu() {
        handleStatusItemClick(nil)
    }

    @objc
    private func quitApp() {
        NSApp.terminate(nil)
    }

    private func ensureMainWindow() -> NSWindow? {
        if let win = mainWindow {
            return win
        }
        guard let vm = viewModel else { return nil }

        // Create a custom window that looks like the previous panel
        // but behaves like a normal window.
        let win = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 248, height: 318),
            styleMask: [.titled, .fullSizeContentView, .closable, .miniaturizable],
            backing: .buffered,
            defer: false
        )
        // Hide title bar
        win.titlebarAppearsTransparent = true
        win.titleVisibility = .hidden
        win.isOpaque = false
        win.backgroundColor = .clear
        win.hasShadow = true
        win.isMovableByWindowBackground = true
        // Remove .fullScreenAuxiliary for standard app behavior in Mission Control?
        // Let's stick to standard behavior.
        win.collectionBehavior = [.managed]

        let root = FloatingPendulumView(
            viewModel: vm,
            onOptions: { [weak self] in self?.openOptionsWindow() },
            onOpenSetlist: { [weak self] in self?.openSetlistWindow() }
        )
        win.contentView = NSHostingView(rootView: root)
        win.center()
        win.delegate = self

        mainWindow = win
        return win
    }

    private func openOptionsWindow() {
        viewModel?.setInterfaceActive(true)
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
        win.backgroundColor = NSColor.black.withAlphaComponent(vm.backgroundOpacityFraction)
        win.center()
        win.contentView = NSHostingView(
            rootView: MainView(
                viewModel: vm,
                showVisualizer: false,
                onOpenSetlist: { [weak self] in self?.openSetlistWindow() },
                onQuit: { [weak self] in self?.quitApp() }
            ))
        win.isReleasedWhenClosed = false
        win.delegate = self
        win.makeKeyAndOrderFront(nil)
        optionsWindow = win
    }

    private func openSetlistWindow() {
        viewModel?.setInterfaceActive(true)
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
        win.contentView = NSHostingView(
            rootView: NavigationStack {
                SetlistEditorView(viewModel: vm)
            })
        win.isReleasedWhenClosed = false
        win.delegate = self
        win.makeKeyAndOrderFront(nil)
        setlistWindow = win
    }

    private func refreshInterfaceActivity() {
        let visibleMain = mainWindow?.isVisible == true
        let visibleOptions = optionsWindow?.isVisible == true
        let visibleSetlist = setlistWindow?.isVisible == true
        viewModel?.setInterfaceActive(visibleMain || visibleOptions || visibleSetlist)
    }
}

extension AppController: NSWindowDelegate {
    func windowWillClose(_ notification: Notification) {
        if let win = notification.object as? NSWindow {
            if win == mainWindow {
                // Keep app resident when the main window is closed.
                mainWindow = nil
            }
            if win == optionsWindow {
                optionsWindow = nil
            }
            if win == setlistWindow {
                setlistWindow = nil
            }
            refreshInterfaceActivity()
        }
    }
}

private struct FloatingPendulumView: View {
    @ObservedObject var viewModel: MainViewModel
    let onOptions: () -> Void
    let onOpenSetlist: () -> Void
    @State private var bpmText = ""

    var body: some View {
        ZStack(alignment: .topTrailing) {
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(Color.black.opacity(viewModel.backgroundOpacityFraction))
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(
                            Color.white.opacity(0.12 + viewModel.backgroundOpacityFraction * 0.4),
                            lineWidth: 1)
                )

            VStack(spacing: 10) {
                HStack(spacing: 4) {
                    Button(action: { viewModel.previousSong() }) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 10, weight: .bold))
                            .frame(width: 20, height: 20)
                            .background(
                                Color.white.opacity(0.14),
                                in: RoundedRectangle(cornerRadius: 6, style: .continuous))
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(.white)

                    Button(action: {
                        onOpenSetlist()
                    }) {
                        Text(viewModel.currentSongTitle)
                            .font(.system(size: 11, weight: .semibold, design: .rounded))
                            .lineLimit(1)
                            .truncationMode(.tail)
                            .frame(maxWidth: .infinity)
                            .foregroundStyle(.white.opacity(0.9))
                            .contentShape(Rectangle())  // Make entire text area clickable
                    }
                    .buttonStyle(.plain)

                    Button(action: { viewModel.nextSong() }) {

                        Image(systemName: "chevron.right")
                            .font(.system(size: 10, weight: .bold))
                            .frame(width: 20, height: 20)
                            .background(
                                Color.white.opacity(0.14),
                                in: RoundedRectangle(cornerRadius: 6, style: .continuous))
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
                    if viewModel.randomTraining {
                        subtleStateText("RND ON")
                    }
                    if viewModel.forcePlay {
                        subtleStateText("MUTE OFF")
                    }
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
                        .background(
                            Color.white.opacity(0.14),
                            in: RoundedRectangle(cornerRadius: 6, style: .continuous))

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
                        .background(
                            Color.white.opacity(0.14),
                            in: RoundedRectangle(cornerRadius: 6, style: .continuous))
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

    private func subtleStateText(_ title: String) -> some View {
        Text(title)
            .font(.system(size: 9, weight: .semibold, design: .rounded))
            .foregroundStyle(Color.white.opacity(0.62))
    }
}
