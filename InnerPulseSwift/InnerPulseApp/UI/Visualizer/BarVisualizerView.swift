import SwiftUI

struct BarVisualizerView: View {
    let phase: Double
    let isPlaying: Bool
    let beat: Int
    let isMute: Bool
    let showBeatLabel: Bool

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = geo.size.height
            let cx = w * 0.5
            let cy = h * 0.82
            let len = min(h * 0.62, 140) * 0.9
            let spread = 42.0
            let deg = isPlaying ? (spread * cos(phase * .pi)) : 0.0
            let rad = CGFloat(deg - 90.0) * .pi / 180.0
            let x = cx + len * cos(rad)
            let y = cy + len * sin(rad)
            let color = isMute ? Color.orange : Color.cyan

            ZStack {
                Path { p in
                    p.addArc(center: CGPoint(x: cx, y: cy), radius: len, startAngle: .degrees(228), endAngle: .degrees(312), clockwise: false)
                }
                .stroke(Color.white.opacity(0.15), style: StrokeStyle(lineWidth: 3, lineCap: .round))

                Path { p in
                    p.move(to: CGPoint(x: cx, y: cy))
                    p.addLine(to: CGPoint(x: x, y: y))
                }
                .stroke(color, style: StrokeStyle(lineWidth: 4, lineCap: .round))

                Circle()
                    .fill(Color.white.opacity(0.5))
                    .frame(width: 8, height: 8)
                    .position(x: cx, y: cy)

                Circle()
                    .fill(color.opacity(0.3))
                    .frame(width: 34, height: 34)
                    .position(x: x, y: y)
                    .blur(radius: 5)

                Circle()
                    .fill(color)
                    .frame(width: 18, height: 18)
                    .position(x: x, y: y)

                if showBeatLabel {
                    Text(isMute ? "MUTE" : "Beat \(beat)")
                        .font(.system(size: 14, weight: .bold, design: .rounded))
                        .foregroundStyle(color)
                        .position(x: cx, y: h - 10)
                }
            }
        }
        .frame(height: 190)
    }
}
