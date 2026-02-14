import SwiftUI

struct RandomTrainingOptionsView: View {
    @State var playMin = 1
    @State var playMax = 2
    @State var muteMin = 1
    @State var muteMax = 2

    var body: some View {
        Form {
            Stepper("Play Min: \(playMin)", value: $playMin, in: 1...16)
            Stepper("Play Max: \(playMax)", value: $playMax, in: 1...16)
            Stepper("Mute Min: \(muteMin)", value: $muteMin, in: 1...16)
            Stepper("Mute Max: \(muteMax)", value: $muteMax, in: 1...16)
        }
        .navigationTitle("Random Training")
    }
}
