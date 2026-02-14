import Foundation

final class AppState: ObservableObject {
    @Published var config: AppConfig
    @Published var setlist: [Song]
    @Published var setlistIndex: Int

    let workingDirectory: URL
    private let configStore = ConfigStore()
    private let setlistStore = SetlistStore()

    init() {
        let dir = Self.resolveWorkingDirectory()
        self.workingDirectory = dir
        self.config = configStore.load(from: dir)
        self.setlist = setlistStore.load(from: dir)
        self.setlistIndex = 0
    }

    func saveConfig() {
        let configToSave = self.config
        let directory = self.workingDirectory
        DispatchQueue.global(qos: .background).async { [weak self] in
            guard let self else { return }
            try? self.configStore.save(configToSave, to: directory)
        }
    }

    func saveSetlist() {
        let setlistToSave = self.setlist
        let directory = self.workingDirectory
        DispatchQueue.global(qos: .background).async { [weak self] in
            guard let self else { return }
            try? self.setlistStore.save(setlistToSave, to: directory)
        }
    }

    func resetData() {
        let directory = self.workingDirectory
        DispatchQueue.global(qos: .background).async {
            let fm = FileManager.default
            try? fm.removeItem(at: directory.appendingPathComponent("config.json"))
            try? fm.removeItem(at: directory.appendingPathComponent("setlist.json"))
            // We might want to reload defaults here, or let the next launch handle it.
            // For now, next launch is sufficient as the user will likely restart.
        }
    }

    private static func resolveWorkingDirectory() -> URL {
        let fm = FileManager.default
        // Use ~/Library/Application Support/InnerPulseSwift
        if let appSupport = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask).first {
            let innerPulseDir = appSupport.appendingPathComponent("InnerPulseSwift")

            // Create directory if it doesn't exist
            if !fm.fileExists(atPath: innerPulseDir.path) {
                try? fm.createDirectory(at: innerPulseDir, withIntermediateDirectories: true)
            }

            return innerPulseDir
        }

        // Fallback (should rarely happen on macOS)
        return URL(fileURLWithPath: fm.currentDirectoryPath)
    }
}
