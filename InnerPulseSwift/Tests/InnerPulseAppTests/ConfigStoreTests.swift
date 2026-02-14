import XCTest
@testable import InnerPulseApp

final class ConfigStoreTests: XCTestCase {
    func testDefaultConfigTone() {
        let config = AppConfig()
        XCTAssertEqual(config.tone, "electronic")
    }
}
