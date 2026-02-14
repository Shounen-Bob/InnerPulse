import Foundation

struct WaveGenerator {
    func makeClick(sampleRate: Double, duration: Double = 0.1, frequency: Double = 800) -> [Float] {
        let length = Int(sampleRate * duration)
        guard length > 0 else { return [] }

        return (0..<length).map { i in
            let t = Double(i) / sampleRate
            let envelope = exp(-t * 20.0)
            let value = sin(2.0 * .pi * frequency * t) * envelope
            return Float(value)
        }
    }
}
