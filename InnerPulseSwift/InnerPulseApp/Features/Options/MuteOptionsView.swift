import SwiftUI

struct MuteOptionsView: View {
    @State var acc = false
    @State var backbeat = false
    @State var fourth = false
    @State var eighth = false
    @State var sixteenth = false
    @State var trip = false

    var body: some View {
        Form {
            Toggle("Accent", isOn: $acc)
            Toggle("Backbeat", isOn: $backbeat)
            Toggle("4th", isOn: $fourth)
            Toggle("8th", isOn: $eighth)
            Toggle("16th", isOn: $sixteenth)
            Toggle("Trip", isOn: $trip)
        }
        .navigationTitle("Mute Options")
    }
}
