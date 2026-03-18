import Foundation

enum Constants {
    // Keycodes
    static let hotkeyBacktick: UInt16 = 50
    static let hotkeyEscape: UInt16 = 53

    // Server
    static let serverURL = "http://localhost:8787/ask"
    static let requestTimeoutSeconds: TimeInterval = 120

    // Headers
    static let headerTextResponse = "X-Text-Response"
    static let headerPartyUpdate = "X-Party-Update"

    // Audio
    static let sampleRate: Double = 16000.0
    static let audioBufferSize: UInt32 = 4096
    static let playbackCheckIntervalNs: UInt64 = 100_000_000

    // Files
    static let recordingFilename = "baldur_question.wav"
    static let responseFilename = "baldur_response.aiff"

    // Sounds
    static let soundStart = "Bottle"
    static let soundError = "Basso"

    // Window Detection
    static let bg3OwnerName = "bg3"
    static let baldurWindowSubstring = "baldur"
}
