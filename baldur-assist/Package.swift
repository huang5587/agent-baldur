// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "baldur-assist",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "baldur-assist",
            path: "Sources",
            linkerSettings: [
                .linkedFramework("AVFoundation"),
                .linkedFramework("AppKit"),
                .linkedFramework("CoreGraphics"),
            ]
        ),
    ]
)
