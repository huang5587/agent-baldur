import Foundation

enum ProjectPaths {
    /// Returns the temp directory relative to the executable location.
    static var tempDirectory: URL {
        let executableURL = URL(fileURLWithPath: CommandLine.arguments[0])
        let projectDir = executableURL.deletingLastPathComponent()
        return projectDir.appendingPathComponent("temp")
    }
}
