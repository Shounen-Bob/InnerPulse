import Foundation

struct ConfigStore {
    private let filename = "config.json"

    func load(from directory: URL) -> AppConfig {
        let url = directory.appendingPathComponent(filename)
        guard
            let data = try? Data(contentsOf: url),
            let config = try? JSONDecoder().decode(AppConfig.self, from: data)
        else {
            return AppConfig()
        }
        return config
    }

    func save(_ config: AppConfig, to directory: URL) throws {
        let url = directory.appendingPathComponent(filename)
        let data = try JSONEncoder().encode(config)
        try data.write(to: url, options: .atomic)
    }
}
