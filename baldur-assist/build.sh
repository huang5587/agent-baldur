#!/bin/bash
set -e
cd "$(dirname "$0")"
swiftc -o baldur-assist \
  Sources/Constants.swift \
  Sources/ProjectPaths.swift \
  Sources/PartyManager.swift \
  Sources/AudioRecorder.swift \
  Sources/ScreenCapture.swift \
  Sources/ServerClient.swift \
  Sources/main.swift \
  -framework AVFoundation \
  -framework AppKit \
  -framework CoreGraphics \
  -parse-as-library \
  -target arm64-apple-macosx13.0 \
  -O
echo "Built: baldur-assist"
