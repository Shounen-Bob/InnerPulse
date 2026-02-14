import XCTest
@testable import InnerPulseApp

final class MetronomeLogicTests: XCTestCase {
    func testDefaultBpm() {
        let engine = MetronomeEngine()
        XCTAssertEqual(engine.bpm, 120)
    }
}
