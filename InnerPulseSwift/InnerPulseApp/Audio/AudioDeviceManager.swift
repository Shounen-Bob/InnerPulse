import Foundation

struct AudioDevice: Identifiable {
    let id: String
    let name: String
}

struct AudioDeviceManager {
    func outputDevices() -> [AudioDevice] {
        [AudioDevice(id: "default", name: "System Default")]
    }
}
