import AVFoundation
import Foundation

class AudioRecorder {
    private var audioEngine: AVAudioEngine?
    private var audioFile: AVAudioFile?
    private var outputURL: URL

    init() {
        let tempDir = ProjectPaths.tempDirectory
        try? FileManager.default.createDirectory(at: tempDir, withIntermediateDirectories: true)
        outputURL = tempDir.appendingPathComponent("baldur_question.wav")
    }

    func startRecording() throws {
        let engine = AVAudioEngine()
        let inputNode = engine.inputNode
        let inputFormat = inputNode.outputFormat(forBus: 0)

        // Remove previous recording if it exists
        try? FileManager.default.removeItem(at: outputURL)

        // Target format: 16kHz mono, 16-bit PCM (optimal for speech recognition)
        let outputSettings: [String: Any] = [
            AVFormatIDKey: kAudioFormatLinearPCM,
            AVSampleRateKey: 16000.0,
            AVNumberOfChannelsKey: 1,
            AVLinearPCMBitDepthKey: 16,
            AVLinearPCMIsFloatKey: false,
            AVLinearPCMIsBigEndianKey: false,
        ]

        audioFile = try AVAudioFile(forWriting: outputURL, settings: outputSettings, commonFormat: .pcmFormatInt16, interleaved: true)

        // Create converter to resample/downmix to target format
        guard let outputFormat = AVAudioFormat(commonFormat: .pcmFormatInt16, sampleRate: 16000, channels: 1, interleaved: true) else {
            throw NSError(domain: "AudioRecorder", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to create output format"])
        }
        guard let converter = AVAudioConverter(from: inputFormat, to: outputFormat) else {
            throw NSError(domain: "AudioRecorder", code: 2, userInfo: [NSLocalizedDescriptionKey: "Failed to create audio converter"])
        }

        inputNode.installTap(onBus: 0, bufferSize: 4096, format: inputFormat) { [weak self] buffer, _ in
            guard let self = self, let file = self.audioFile else { return }

            let frameCount = AVAudioFrameCount(Double(buffer.frameLength) * 16000.0 / inputFormat.sampleRate)
            guard let convertedBuffer = AVAudioPCMBuffer(pcmFormat: outputFormat, frameCapacity: frameCount) else { return }

            var error: NSError?
            converter.convert(to: convertedBuffer, error: &error) { inNumPackets, outStatus in
                outStatus.pointee = .haveData
                return buffer
            }

            try? file.write(from: convertedBuffer)
        }

        engine.prepare()
        try engine.start()
        self.audioEngine = engine

        print("[baldur-assist] Recording started...")
    }

    func stopRecording() throws -> URL {
        guard audioEngine != nil else {
            throw RecorderError.notRecording
        }

        audioEngine?.inputNode.removeTap(onBus: 0)
        audioEngine?.stop()
        audioEngine = nil
        audioFile = nil

        guard FileManager.default.fileExists(atPath: outputURL.path) else {
            throw RecorderError.noAudioFile
        }

        print("[baldur-assist] Recording stopped. Saved to \(outputURL.path)")
        return outputURL
    }

    enum RecorderError: Error {
        case notRecording
        case noAudioFile
    }
}
