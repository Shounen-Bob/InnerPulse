import Foundation

struct SetlistStore {
    private let filename = "setlist.json"

    func load(from directory: URL) -> [Song] {
        let url = directory.appendingPathComponent(filename)
        guard
            let data = try? Data(contentsOf: url),
            let setlist = try? JSONDecoder().decode([Song].self, from: data),
            !setlist.isEmpty
        else {
            return Song.demoSongs
        }
        return setlist
    }

    func save(_ setlist: [Song], to directory: URL) throws {
        let url = directory.appendingPathComponent(filename)
        let data = try JSONEncoder().encode(setlist)
        try data.write(to: url, options: .atomic)
    }
}
