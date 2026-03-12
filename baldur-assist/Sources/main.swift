import AppKit
import CoreGraphics
import Foundation

let recorder = AudioRecorder()
let screenCapture = ScreenCapture()
let serverClient = ServerClient()

var isRecording = false
var processingRequest = false
var eventTap: CFMachPort?

func playSound(_ name: String) {
    let projectDir = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()
        .deletingLastPathComponent()
    let soundPath = projectDir.appendingPathComponent("\(name).aiff").path

    if let sound = NSSound(contentsOfFile: soundPath, byReference: true) {
        sound.play()
    } else {
        print("[baldur-assist] Sound not found: \(soundPath)")
    }
}

func handleHotkey() {
    if processingRequest {
        print("[baldur-assist] Still processing previous request, ignoring hotkey.")
        return
    }

    if !isRecording {
        do {
            try recorder.startRecording()
            isRecording = true
            playSound("Bottle")
        } catch {
            print("[baldur-assist] Failed to start recording: \(error)")
            playSound("Basso")
        }
    } else {
        isRecording = false

        let audioURL: URL
        do {
            audioURL = try recorder.stopRecording()
        } catch {
            print("[baldur-assist] Failed to stop recording: \(error)")
            playSound("Basso")
            return
        }

        playSound("Bottle")

        guard let imageData = screenCapture.capture() else {
            print("[baldur-assist] Failed to capture screenshot")
            playSound("Basso")
            return
        }

        processingRequest = true
        Task {
            do {
                try await serverClient.sendRequest(audioURL: audioURL, imageData: imageData)
            } catch {
                print("[baldur-assist] Request failed: \(error)")
                playSound("Basso")
            }
            processingRequest = false
        }
    }
}

func handleAbort() {
    if isRecording {
        isRecording = false
        _ = try? recorder.stopRecording()
        print("[baldur-assist] Recording aborted.")
        playSound("Basso")
    }
}

func hotkeyCallback(
    proxy: CGEventTapProxy,
    type: CGEventType,
    event: CGEvent,
    refcon: UnsafeMutableRawPointer?
) -> Unmanaged<CGEvent>? {
    // Re-enable the tap if macOS disabled it due to timeout
    if type == .tapDisabledByTimeout || type == .tapDisabledByUserInput {
        if let tap = eventTap {
            CGEvent.tapEnable(tap: tap, enable: true)
            print("[baldur-assist] Event tap re-enabled.")
        }
        return Unmanaged.passRetained(event)
    }

    if type == .keyDown {
        let keyCode = event.getIntegerValueField(.keyboardEventKeycode)
        // Backtick (`): keycode 50
        if keyCode == 50 {
            handleHotkey()
            return nil
        }
        // Escape: keycode 53 - abort recording
        if keyCode == 53 && isRecording {
            handleAbort()
            return nil
        }
    }
    return Unmanaged.passRetained(event)
}

@main
struct BaldurAssist {
    static func main() {
        let eventMask = (1 << CGEventType.keyDown.rawValue)
            | (1 << CGEventType.tapDisabledByTimeout.rawValue)
            | (1 << CGEventType.tapDisabledByUserInput.rawValue)

        guard let tap = CGEvent.tapCreate(
            tap: .cgSessionEventTap,
            place: .headInsertEventTap,
            options: .defaultTap,
            eventsOfInterest: CGEventMask(eventMask),
            callback: hotkeyCallback,
            userInfo: nil
        ) else {
            print("[baldur-assist] Failed to create event tap. Make sure the app has Accessibility permissions.")
            print("[baldur-assist] Go to System Settings > Privacy & Security > Accessibility and add this app.")
            exit(1)
        }

        let runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .commonModes)
        eventTap = tap
        CGEvent.tapEnable(tap: tap, enable: true)

        print("[baldur-assist] Hotkey listener active.")
        print("[baldur-assist] ` (backtick): Start/stop recording and send to advisor")
        print("[baldur-assist] Escape: Abort recording (while recording)")
        print("[baldur-assist] Ctrl+C: Quit")

        CFRunLoopRun()
    }
}
