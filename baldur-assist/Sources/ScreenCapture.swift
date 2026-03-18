import AppKit
import CoreGraphics
import Foundation

class ScreenCapture {
    /// Capture the BG3 window, or fall back to the full screen.
    func capture() -> Data? {
        // Try to find the BG3 window
        if let windowID = findBG3WindowID() {
            print("[baldur-assist] Capturing BG3 window (ID: \(windowID))")
            let windowList = [windowID] as CFArray
            if let cgImage = CGImage(
                windowListFromArrayScreenBounds: .null,
                windowArray: windowList,
                imageOption: .bestResolution
            ) {
                return pngData(from: cgImage)
            }
        }

        // Fallback: capture the main display
        print("[baldur-assist] BG3 window not found, capturing main display")
        guard let cgImage = CGDisplayCreateImage(CGMainDisplayID()) else {
            print("[baldur-assist] Failed to capture screen")
            return nil
        }
        return pngData(from: cgImage)
    }

    private func findBG3WindowID() -> CGWindowID? {
        guard let windowList = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] else {
            return nil
        }

        for window in windowList {
            let ownerName = (window[kCGWindowOwnerName as String] as? String ?? "").lowercased()
            let windowName = (window[kCGWindowName as String] as? String ?? "").lowercased()

            // Match on owner "bg3" or window name containing "baldur"
            // Skip windows with empty names (helper windows)
            let isMatch = ownerName == Constants.bg3OwnerName || ownerName.contains(Constants.baldurWindowSubstring) || windowName.contains(Constants.baldurWindowSubstring)
            let hasContent = !windowName.isEmpty

            if isMatch && hasContent {
                let windowID = window[kCGWindowNumber as String] as? CGWindowID
                print("[baldur-assist] Found BG3 window: owner=\"\(ownerName)\" name=\"\(windowName)\"")
                return windowID
            }
        }
        return nil
    }

    private func pngData(from cgImage: CGImage) -> Data? {
        let rep = NSBitmapImageRep(cgImage: cgImage)
        return rep.representation(using: .png, properties: [:])
    }
}
