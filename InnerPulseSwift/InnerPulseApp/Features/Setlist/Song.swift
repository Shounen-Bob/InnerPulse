import Foundation

struct Song: Codable, Identifiable, Equatable {
    let id: UUID
    var name: String
    var bpm: Int
    var bpb: Int

    init(id: UUID = UUID(), name: String, bpm: Int, bpb: Int) {
        self.id = id
        self.name = name
        self.bpm = bpm
        self.bpb = bpb
    }

    static let defaultSong = Song(name: "Default", bpm: 120, bpb: 4)
    static let demoSongs: [Song] = [
        Song(name: "Warmup Groove", bpm: 92, bpb: 4),
        Song(name: "Linear Sprint", bpm: 128, bpb: 3),
        Song(name: "Odd Meter Drill", bpm: 110, bpb: 5),
        Song(name: "Fast Pocket", bpm: 148, bpb: 7),
    ]

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case bpm
        case bpb
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.id = try container.decodeIfPresent(UUID.self, forKey: .id) ?? UUID()
        self.name = try container.decode(String.self, forKey: .name)
        self.bpm = try container.decode(Int.self, forKey: .bpm)
        self.bpb = try container.decode(Int.self, forKey: .bpb)
    }
}
