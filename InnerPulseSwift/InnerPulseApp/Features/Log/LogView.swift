import AppKit
import SwiftUI

struct LogView: View {
    let logs: [String]
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(spacing: 0) {
            header
            content
        }
        .background(Color.black.opacity(0.92))
        .foregroundStyle(Color.white)
    }

    private var header: some View {
        HStack(spacing: 8) {
            Button("Copy", action: copyAll)
                .keyboardShortcut("c", modifiers: [.command])
            Spacer()
            Button("Close") { dismiss() }
                .keyboardShortcut(.escape, modifiers: [])
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(Color.black.opacity(0.96))
        .foregroundStyle(Color.white)
    }

    private var content: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 8) {
                ForEach(logs.indices, id: \.self) { index in
                    Text(logs[index])
                        .foregroundStyle(Color.green.opacity(0.95))
                        .font(.system(size: 12, weight: .regular, design: .monospaced))
                        .textSelection(.enabled)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 3)
                        .background(Color.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 6, style: .continuous))
                }
            }
            .padding()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func copyAll() {
        let text = logs.joined(separator: "\n")
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(text, forType: .string)
    }
}
