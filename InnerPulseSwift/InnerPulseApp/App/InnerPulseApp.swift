import SwiftUI

@main
struct InnerPulseApp: App {
    @StateObject private var viewModel: MainViewModel
    private let statusBarController: StatusBarController

    init() {
        let state = AppState()
        let vm = MainViewModel(appState: state)
        _viewModel = StateObject(wrappedValue: vm)
        let controller = StatusBarController()
        controller.configure(with: vm)
        self.statusBarController = controller
    }

    var body: some Scene {
        Settings {
            EmptyView()
        }
    }
}
