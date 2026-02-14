import AppKit
import Foundation
import ServiceManagement

enum LaunchAtLoginManager {
    static func setEnabled(_ enabled: Bool) {
        // Try the official API first.
        if #available(macOS 13.0, *) {
            do {
                if enabled {
                    try SMAppService.mainApp.register()
                } else {
                    try SMAppService.mainApp.unregister()
                }
                return
            } catch {
                // In dev/unsigned/non-standard launch contexts this may fail.
                // Fall through to AppleScript-based login item update.
                print("LaunchAtLogin update via SMAppService failed: \(error)")
            }
        }

        setViaAppleScript(enabled: enabled)
    }

    private static func setViaAppleScript(enabled: Bool) {
        guard let appURL = appBundleURL() else {
            print("LaunchAtLogin fallback failed: app bundle URL not found")
            return
        }

        let path = appURL.path.replacingOccurrences(of: "\"", with: "\\\"")
        let addScript = """
        tell application "System Events"
            if not (exists login item "InnerPulseSwift") then
                make login item at end with properties {name:"InnerPulseSwift", path:"\(path)", hidden:false}
            else
                set path of login item "InnerPulseSwift" to "\(path)"
            end if
        end tell
        """
        let removeScript = """
        tell application "System Events"
            if exists login item "InnerPulseSwift" then
                delete login item "InnerPulseSwift"
            end if
        end tell
        """

        let source = enabled ? addScript : removeScript
        var error: NSDictionary?
        NSAppleScript(source: source)?.executeAndReturnError(&error)
        if let error {
            print("LaunchAtLogin fallback failed: \(error)")
        }
    }

    private static func appBundleURL() -> URL? {
        let bundleURL = Bundle.main.bundleURL
        if bundleURL.pathExtension == "app" {
            return bundleURL
        }

        // When launched from swift run, executable is in .build/...; use packaged app if present.
        let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        let candidate = root.appendingPathComponent("InnerPulseSwift.app")
        if FileManager.default.fileExists(atPath: candidate.path) {
            return candidate
        }
        return nil
    }
}
