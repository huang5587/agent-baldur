import AppKit
import CoreGraphics
import Foundation

let recorder = AudioRecorder()
let screenCapture = ScreenCapture()
let serverClient = ServerClient()

var isRecording = false
var processingRequest = false
var eventTap: CFMachPort?

func handleHotkey() {
    if processingRequest {
        print("[baldur-assist] Still processing previous request, ignoring hotkey.")
        return
    }

    if !isRecording {
        do {
            try recorder.startRecording()
            isRecording = true
            NSSound.beep()
        } catch {
            print("[baldur-assist] Failed to start recording: \(error)")
        }
    } else {
        isRecording = false
        let audioURL = recorder.stopRecording()
        NSSound.beep()

        guard let imageData = screenCapture.capture() else {
            print("[baldur-assist] Failed to capture screenshot")
            return
        }

        processingRequest = true
        Task {
            do {
                try await serverClient.sendRequest(audioURL: audioURL, imageData: imageData)
            } catch {
                print("[baldur-assist] Request failed: \(error)")
            }
            processingRequest = false
        }
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
        let flags = event.flags
        // Shift+Space: space = keycode 49, check for shift modifier
        if keyCode == 49 && flags.contains(.maskShift) {
            handleHotkey()
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

        print("[baldur-assist] Hotkey listener active. Press Shift+Space to start/stop recording.")
        print("[baldur-assist] Press Shift+Space once to start recording your question.")
        print("[baldur-assist] Press Shift+Space again to stop and send to the advisor.")
        print("[baldur-assist] Press Ctrl+C to quit.")

        CFRunLoopRun()
    }
}
