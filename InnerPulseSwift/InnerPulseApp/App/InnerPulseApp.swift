import SwiftUI

@main
struct InnerPulseApp: App {
    @StateObject private var viewModel: MainViewModel
    private let appController: AppController

    init() {
        let state = AppState()
        let vm = MainViewModel(appState: state)
        _viewModel = StateObject(wrappedValue: vm)
        let controller = AppController()
        controller.configure(with: vm)
        self.appController = controller
    }

    var body: some Scene {
        Settings {
            EmptyView()
        }
    }
}
