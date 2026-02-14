import SwiftUI

struct VerticalSlider: View {
    let title: String
    @Binding var value: Double
    var range: ClosedRange<Double>
    var labelColor: Color = .white

    var body: some View {
        VStack(spacing: 4) {
            VerticalMacSlider(value: $value, range: range, accent: labelColor)
            Text(title)
                .font(.system(size: 9, weight: .bold, design: .rounded))
                .foregroundStyle(labelColor)
                .lineLimit(1)
            Text(String(format: "%.0f", value * 100))
                .font(.system(size: 10, weight: .bold, design: .monospaced))
                .foregroundStyle(.white.opacity(0.9))
        }
        .frame(width: 42, height: 138)
    }
}

private struct VerticalMacSlider: View {
    @Binding var value: Double
    let range: ClosedRange<Double>
    let accent: Color

    private let trackWidth: CGFloat = 12
    private let trackHeight: CGFloat = 92
    private let knobSize: CGFloat = 16

    var body: some View {
        GeometryReader { _ in
            ZStack {
                Capsule(style: .continuous)
                    .fill(Color.white.opacity(0.10))
                    .frame(width: trackWidth, height: trackHeight)
                    .overlay(
                        VStack(spacing: 0) {
                            tick(width: 7, alpha: 0.38)
                            Spacer()
                            tick(width: 5, alpha: 0.28)
                            Spacer()
                            tick(width: 7, alpha: 0.38)
                        }
                        .padding(.vertical, 6)
                    )

                Capsule(style: .continuous)
                    .fill(accent.opacity(0.75))
                    .frame(width: 4, height: fillHeight())
                    .offset(y: (trackHeight - fillHeight()) * 0.5)

                Circle()
                    .fill(
                        RadialGradient(
                            colors: [Color.white, Color.white.opacity(0.78)],
                            center: .topLeading,
                            startRadius: 1,
                            endRadius: knobSize
                        )
                    )
                    .overlay(Circle().stroke(Color.black.opacity(0.22), lineWidth: 1))
                    .frame(width: knobSize, height: knobSize)
                    .offset(y: knobOffsetY())
                    .shadow(color: .black.opacity(0.3), radius: 1.5, y: 1)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 0)
                    .onChanged { g in
                        updateValue(fromY: g.location.y)
                    }
            )
        }
        .frame(width: 26, height: 98)
    }

    private func tick(width: CGFloat, alpha: CGFloat) -> some View {
        Rectangle()
            .fill(Color.white.opacity(alpha))
            .frame(width: width, height: 1)
    }

    private func normalized() -> Double {
        let clamped = min(range.upperBound, max(range.lowerBound, value))
        let span = max(0.000001, range.upperBound - range.lowerBound)
        return (clamped - range.lowerBound) / span
    }

    private func knobOffsetY() -> CGFloat {
        let n = normalized()
        return CGFloat((1.0 - n) * Double(trackHeight) - Double(trackHeight) * 0.5)
    }

    private func fillHeight() -> CGFloat {
        let n = normalized()
        return max(1, CGFloat(n) * trackHeight)
    }

    private func updateValue(fromY y: CGFloat) {
        let local = min(trackHeight, max(0, y))
        let n = 1.0 - (Double(local) / Double(trackHeight))
        value = range.lowerBound + n * (range.upperBound - range.lowerBound)
    }
}
