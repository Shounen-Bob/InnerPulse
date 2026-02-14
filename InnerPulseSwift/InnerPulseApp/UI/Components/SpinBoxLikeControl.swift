import SwiftUI

struct SpinBoxLikeControl: View {
    let title: String
    @Binding var value: Int
    let range: ClosedRange<Int>
    @State private var textValue = ""

    var body: some View {
        VStack(spacing: 6) {
            Text(title)
                .font(.system(.caption2, design: .rounded, weight: .semibold))
                .foregroundStyle(Color.white.opacity(0.82))
                .textCase(.uppercase)
                .tracking(0.6)

            HStack(spacing: 5) {
                Button("-") {
                    value = max(range.lowerBound, value - 1)
                    textValue = "\(value)"
                }
                .buttonStyle(.plain)
                .frame(width: 18, height: 18)
                .background(Color.white.opacity(0.14), in: RoundedRectangle(cornerRadius: 5, style: .continuous))

                TextField("", text: $textValue)
                    .textFieldStyle(.plain)
                    .multilineTextAlignment(.center)
                    .font(.system(size: 14, weight: .bold, design: .monospaced))
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
                    .onChange(of: textValue) { newValue in
                        let digitsOnly = newValue.filter(\.isNumber)
                        if digitsOnly != newValue {
                            textValue = digitsOnly
                        }
                    }
                    .onSubmit { commitText() }

                Button("+") {
                    value = min(range.upperBound, value + 1)
                    textValue = "\(value)"
                }
                .buttonStyle(.plain)
                .frame(width: 18, height: 18)
                .background(Color.white.opacity(0.14), in: RoundedRectangle(cornerRadius: 5, style: .continuous))
            }
            .padding(.horizontal, 6)
            .padding(.vertical, 4)
            .background(Color.black.opacity(0.28), in: RoundedRectangle(cornerRadius: 8, style: .continuous))
        }
        .frame(maxWidth: .infinity, minHeight: 74)
        .padding(.vertical, 6)
        .padding(.horizontal, 6)
        .background(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [Color.white.opacity(0.1), Color.white.opacity(0.04)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
        )
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(Color.white.opacity(0.12), lineWidth: 1)
        )
        .onAppear {
            textValue = "\(value)"
        }
        .onChange(of: value) { newValue in
            textValue = "\(newValue)"
        }
    }

    private func commitText() {
        if let v = Int(textValue) {
            value = min(range.upperBound, max(range.lowerBound, v))
        }
        textValue = "\(value)"
    }
}
