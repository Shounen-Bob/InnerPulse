import SwiftUI

struct LedVisualizerView: View {
    let beat: Int
    let beatsPerBar: Int
    let isMute: Bool

    var body: some View {
        HStack(spacing: 18) {
            ForEach(1...4, id: \.self) { idx in
                let active = idx == beat
                let enabled = idx <= beatsPerBar
                let baseColor = isMute ? Color.orange : Color.cyan

                ZStack {
                    Circle()
                        .fill(Color.white.opacity(enabled ? 0.07 : 0.03))
                        .frame(width: 34, height: 34)
                    Circle()
                        .fill(active ? baseColor : Color.white.opacity(enabled ? 0.20 : 0.08))
                        .frame(width: enabled ? 24 : 14, height: enabled ? 24 : 14)
                        .overlay(
                            Circle()
                                .stroke(Color.white.opacity(active ? 0.65 : 0.25), lineWidth: 1)
                        )
                }
                .animation(.linear(duration: 0.06), value: active)
            }
        }
        .padding(.vertical, 18)
    }
}
