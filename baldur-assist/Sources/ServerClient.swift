import AVFoundation
import Foundation

class ServerClient {
    private let serverURL = URL(string: "http://localhost:8787/ask")!
    private var audioPlayer: AVAudioPlayer?
    private let partyManager = PartyManager()

    func sendRequest(audioURL: URL, imageData: Data) async throws {
        let boundary = UUID().uuidString
        var request = URLRequest(url: serverURL)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 120

        var body = Data()

        // Add image
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"screenshot.png\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/png\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n".data(using: .utf8)!)

        // Add audio
        let audioData = try Data(contentsOf: audioURL)
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"audio\"; filename=\"question.wav\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(audioData)
        body.append("\r\n".data(using: .utf8)!)

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        print("[baldur-assist] Sending request to server...")
        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            let statusCode = (response as? HTTPURLResponse)?.statusCode ?? -1
            let bodyStr = String(data: data, encoding: .utf8) ?? "no body"
            print("[baldur-assist] Server error (\(statusCode)): \(bodyStr)")
            return
        }

        if let textResponse = httpResponse.value(forHTTPHeaderField: "X-Text-Response"),
           let decoded = textResponse.removingPercentEncoding {
            print("[baldur-assist] LLM response: \(decoded)")
        }

        // Check for party update data
        if let partyUpdate = httpResponse.value(forHTTPHeaderField: "X-Party-Update"),
           let decoded = partyUpdate.removingPercentEncoding,
           let jsonData = decoded.data(using: .utf8) {
            do {
                try partyManager.updateCharacter(jsonData: jsonData)
            } catch {
                print("[baldur-assist] Failed to update party: \(error)")
                // Continue anyway - the voice response will still play
            }
        }

        // Save and play the response audio
        let tempURL = ProjectPaths.tempDirectory.appendingPathComponent("baldur_response.aiff")

        do {
            try data.write(to: tempURL)
        } catch {
            print("[baldur-assist] Failed to save audio file: \(error)")
            return
        }

        print("[baldur-assist] Playing response audio...")
        do {
            audioPlayer = try AVAudioPlayer(contentsOf: tempURL)
            audioPlayer?.play()

            // Wait for playback to finish
            while audioPlayer?.isPlaying == true {
                try await Task.sleep(nanoseconds: 100_000_000) // 100ms
            }
            print("[baldur-assist] Playback complete.")
        } catch {
            print("[baldur-assist] Failed to play audio: \(error)")
        }
    }
}
