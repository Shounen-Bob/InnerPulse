import AppKit
import SwiftUI
import UniformTypeIdentifiers

struct SetlistEditorView: View {
    @ObservedObject var viewModel: MainViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var searchText = ""
    @State private var importError: String?

    private var visibleSongIDs: [UUID] {
        let key = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !key.isEmpty else {
            return viewModel.setlist.map { $0.id }
        }
        return
            viewModel.setlist
            .filter { $0.name.localizedCaseInsensitiveContains(key) }
            .map { $0.id }
    }

    var body: some View {
        VStack(spacing: 12) {
            TextField("Search songs", text: $searchText)
                .textFieldStyle(.roundedBorder)
                .padding(.horizontal, 2)

            ScrollView {
                LazyVStack(spacing: 12) {
                    ForEach(visibleSongIDs, id: \.self) { id in
                        if let songBinding = binding(for: id) {
                            let song = songBinding.wrappedValue
                            VStack(alignment: .leading, spacing: 8) {
                                TextField("Song Name", text: songBinding.name, axis: .vertical)
                                    .textFieldStyle(.roundedBorder)
                                    .lineLimit(1...2)

                                HStack(spacing: 10) {
                                    HStack(spacing: 4) {
                                        Text("BPM")
                                        TextField("BPM", value: songBinding.bpm, format: .number)
                                            .textFieldStyle(.roundedBorder)
                                            .frame(width: 50)
                                            .multilineTextAlignment(.trailing)
                                        Stepper("", value: songBinding.bpm, in: 40...300)
                                            .labelsHidden()
                                    }
                                    Stepper("Beat \(song.bpb)", value: songBinding.bpb, in: 1...8)
                                    Spacer(minLength: 4)
                                    Button(role: .destructive) {
                                        removeSong(withId: id)
                                    } label: {
                                        Image(systemName: "trash")
                                            .font(.system(size: 12, weight: .bold))
                                            .frame(width: 26, height: 26)
                                    }
                                    .buttonStyle(.borderless)
                                }
                            }
                            .padding(.vertical, 6)
                            .padding(.horizontal, 6)
                            .background(
                                RoundedRectangle(cornerRadius: 10, style: .continuous)
                                    .fill(Color.black.opacity(0.04))
                            )
                        }
                    }
                }
                .padding(.horizontal, 2)
                .padding(.bottom, 4)
            }
        }
        .padding(.vertical, 6)
        .alert(
            "JSON Load Failed",
            isPresented: Binding(
                get: { importError != nil },
                set: { if !$0 { importError = nil } }
            )
        ) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(importError ?? "")
        }
        .toolbar {
            ToolbarItemGroup(placement: .automatic) {
                Button("Load JSON") { loadFromJSON() }
                Button("Add") {
                    viewModel.setlist.append(Song(name: "New Song", bpm: 120, bpb: 4))
                }
            }
            ToolbarItem(placement: .cancellationAction) {
                Button("Done") { dismiss() }
            }
        }
        .navigationTitle("Setlist")
    }

    private func binding(for id: UUID) -> Binding<Song>? {
        guard let idx = viewModel.setlist.firstIndex(where: { $0.id == id }) else { return nil }
        return $viewModel.setlist[idx]
    }

    private func removeSong(withId id: UUID) {
        guard let idx = viewModel.setlist.firstIndex(where: { $0.id == id }) else { return }
        viewModel.setlist.remove(at: idx)
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
            viewModel.setlist = loaded
            searchText = ""  // Clear search to show new songs
        } catch {
            importError = error.localizedDescription
        }
    }
}
