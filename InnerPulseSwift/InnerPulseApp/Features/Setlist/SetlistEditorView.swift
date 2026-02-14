import AppKit
import SwiftUI
import UniformTypeIdentifiers

struct SetlistEditorView: View {
    @Binding var setlist: [Song]
    @Environment(\.dismiss) private var dismiss
    @State private var searchText = ""
    @State private var importError: String?

    private var visibleIndices: [Int] {
        if searchText.isEmpty {
            return Array(setlist.indices)
        }
        let key = searchText.lowercased()
        return setlist.indices.filter { idx in
            setlist[idx].name.lowercased().contains(key)
        }
    }

    var body: some View {
        List {
            ForEach(visibleIndices, id: \.self) { idx in
                VStack(alignment: .leading, spacing: 8) {
                    TextField("Song Name", text: $setlist[idx].name, axis: .vertical)
                        .textFieldStyle(.roundedBorder)
                        .lineLimit(1...2)

                    HStack(spacing: 10) {
                        Stepper("BPM \(setlist[idx].bpm)", value: $setlist[idx].bpm, in: 40...300)
                        Stepper("Beat \(setlist[idx].bpb)", value: $setlist[idx].bpb, in: 1...8)
                        Spacer(minLength: 4)
                        Button(role: .destructive) {
                            setlist.remove(at: idx)
                        } label: {
                            Image(systemName: "trash")
                                .font(.system(size: 12, weight: .bold))
                                .frame(width: 26, height: 26)
                        }
                        .buttonStyle(.borderless)
                    }
                }
                .padding(.vertical, 4)
            }
        }
        .listStyle(.inset)
        .searchable(text: $searchText, prompt: "Search songs")
        .alert("JSON Load Failed", isPresented: Binding(
            get: { importError != nil },
            set: { if !$0 { importError = nil } }
        )) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(importError ?? "")
        }
        .toolbar {
            ToolbarItemGroup(placement: .automatic) {
                Button("Load JSON") { loadFromJSON() }
                Button("Add") {
                    setlist.append(Song(name: "New Song", bpm: 120, bpb: 4))
                }
            }
            ToolbarItem(placement: .cancellationAction) {
                Button("Done") { dismiss() }
            }
        }
        .navigationTitle("Setlist")
    }

    private func loadFromJSON() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowsMultipleSelection = false
        panel.allowedContentTypes = [.json]

        guard panel.runModal() == .OK, let url = panel.url else { return }
        do {
            let data = try Data(contentsOf: url)
            let loaded = try JSONDecoder().decode([Song].self, from: data)
            guard !loaded.isEmpty else {
                importError = "The selected JSON has no songs."
                return
            }
            setlist = loaded
        } catch {
            importError = error.localizedDescription
        }
    }
}
