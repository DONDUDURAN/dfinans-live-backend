#!/bin/bash
# Watches for IBKR's "API client needs write access action confirmation"
# dialog. This dialog is purely informational (confirmed via screenshot):
# it has NO grant/accept button, only "Configure API Settings" (mnemonic
# Alt+C) and "Close". It tells the operator that the "Read-Only API"
# checkbox under Global Configuration -> API -> Settings must be manually
# unchecked. This script presses Alt+C to open that Global Configuration
# screen and then screenshots the root window so we can visually confirm
# the real state of the checkbox there (IBC's own config-wizard automation
# claims to already uncheck it, but the dialog reappearing on every client
# connection suggests it isn't actually taking effect).
#
# Dedup is done per-window-id (not a single global flag) since this dialog
# reopens on every API client connection attempt/retry - each occurrence
# gets its own X11 window id, so we can safely react to each new one.

set -u
export DISPLAY=:1

echo "ACCEPTWATCH: watcher started"

SEEN_TITLES_FILE=/tmp/seen_titles.txt
HANDLED_WIDS_FILE=/tmp/handled_wids.txt
: > "$SEEN_TITLES_FILE"
: > "$HANDLED_WIDS_FILE"

while true; do
    # Lightweight diagnostic: log any newly-seen window title.
    for WID_ALL in $(xdotool search --name "" 2>/dev/null); do
        TITLE=$(xdotool getwindowname "$WID_ALL" 2>/dev/null || true)
        if [ -n "$TITLE" ] && ! grep -qxF "$TITLE" "$SEEN_TITLES_FILE" 2>/dev/null; then
            echo "$TITLE" >> "$SEEN_TITLES_FILE"
            echo "ACCEPTWATCH_TITLE: id=$WID_ALL title=\"$TITLE\""
        fi
    done

    for WID in $(xdotool search --name "write access" 2>/dev/null); do
        if grep -qxF "$WID" "$HANDLED_WIDS_FILE" 2>/dev/null; then
            continue
        fi
        echo "$WID" >> "$HANDLED_WIDS_FILE"
        echo "ACCEPTWATCH: found new write-access window id=$WID"

        xdotool windowfocus --sync "$WID" 2>&1 | sed 's/^/ACCEPTWATCH_FOCUS: /'
        sleep 0.2
        echo "ACCEPTWATCH: sending Alt+C mnemonic for Configure API Settings"
        xdotool key --window "$WID" alt+c 2>&1 | sed 's/^/ACCEPTWATCH_KEY: /'
        sleep 2

        echo "ACCEPTWATCH_TITLES_AFTER_KEY_BEGIN"
        xdotool search --name "" 2>/dev/null | while read -r W2; do
            T2=$(xdotool getwindowname "$W2" 2>/dev/null || true)
            [ -n "$T2" ] && echo "ACCEPTWATCH_POSTKEY_TITLE: id=$W2 title=\"$T2\""
        done
        echo "ACCEPTWATCH_TITLES_AFTER_KEY_END"

        xwd -root -out /tmp/dialog.xwd 2>&1 | sed 's/^/ACCEPTWATCH_XWD: /'
        if [ -f /tmp/dialog.xwd ]; then
            ls -la /tmp/dialog.xwd | sed 's/^/ACCEPTWATCH_XWD_SIZE: /'
            convert /tmp/dialog.xwd -resize 40% /tmp/dialog.png 2>&1 | sed 's/^/ACCEPTWATCH_CONVERT: /'
            if [ -f /tmp/dialog.png ]; then
                ls -la /tmp/dialog.png | sed 's/^/ACCEPTWATCH_PNG_SIZE: /'
                echo "ACCEPTWATCH_PNG_BEGIN"
                base64 -w 400 /tmp/dialog.png > /tmp/dialog.b64
                wc -l /tmp/dialog.b64 | sed 's/^/ACCEPTWATCH_B64_LINES: /'
                while IFS= read -r line; do
                    echo "ACCEPTWATCH_B64: $line"
                    sleep 0.05
                done < /tmp/dialog.b64
                echo "ACCEPTWATCH_PNG_END"
            else
                echo "ACCEPTWATCH: convert failed, no png produced"
            fi
        else
            echo "ACCEPTWATCH: xwd failed, no capture produced"
        fi
    done
    sleep 0.3
done
