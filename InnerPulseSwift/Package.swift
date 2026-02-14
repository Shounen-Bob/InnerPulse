// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "InnerPulseApp",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "InnerPulseApp", targets: ["InnerPulseApp"])
    ],
    targets: [
        .executableTarget(
            name: "InnerPulseApp",
            path: "InnerPulseApp",
            resources: [
                .process("Resources")
            ]
        ),
        .testTarget(
            name: "InnerPulseAppTests",
            dependencies: ["InnerPulseApp"],
            path: "Tests/InnerPulseAppTests"
        )
    ]
)
