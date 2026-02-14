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
        try? configStore.save(config, to: workingDirectory)
    }

    func saveSetlist() {
        try? setlistStore.save(setlist, to: workingDirectory)
    }

    private static func resolveWorkingDirectory() -> URL {
        let fm = FileManager.default
        let cwd = URL(fileURLWithPath: fm.currentDirectoryPath)
        let parent = cwd.deletingLastPathComponent()
        let candidates = [cwd, parent]

        for dir in candidates {
            let hasConfig = fm.fileExists(atPath: dir.appendingPathComponent("config.json").path)
            let hasSetlist = fm.fileExists(atPath: dir.appendingPathComponent("setlist.json").path)
            if hasConfig || hasSetlist {
                return dir
            }
        }
        return cwd
    }
}
