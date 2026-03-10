#!/bin/bash
open -b com.larian.baldursgate3 2>/dev/null || open -a "Baldur's Gate 3" 2>/dev/null || {
    echo "Baldur's Gate 3 not found. Is it installed?" >&2
    exit 1
}

sleep 3

osascript -e '
tell application "System Events"
    tell process "Baldur'\''s Gate 3"
        click UI element "PLAY" of group 2 of UI element 1 of scroll area 1 of group 1 of group 1 of window 1
    end tell
end tell
'
