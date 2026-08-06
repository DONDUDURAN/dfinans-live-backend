#!/bin/bash
# Watches for IBKR's "API client needs write access action confirmation"
# dialog (IBC's internal name; the visible window title is "IBKR Gateway")
# and, on first detection, dumps an xwd screenshot as base64 to stdout so
# it can be captured via `railway logs` and reconstructed for visual
# inspection of the actual button layout (IBC has no automation support
# for this dialog - see repo history/checkpoints for context).
#
# Deliberately non-destructive in this phase: it only OBSERVES and logs,
# it does not click anything yet. Once we know the button coordinates from
# the captured screenshot, this script will be updated to also send a
# click within the ~16s window before IBKR auto-denies the request.

set -u
export DISPLAY=:1

echo "ACCEPTWATCH: watcher started"

CAPTURED=0
SEEN_TITLES_FILE=/tmp/seen_titles.txt
: > "$SEEN_TITLES_FILE"

while true; do
    # Lightweight diagnostic: log any newly-seen window title (helps
    # confirm the exact title IBKR uses for the write-access dialog,
    # in case it differs from IBC's internal "API client needs write
    # access action confirmation" label).
    for WID_ALL in $(xdotool search --name "" 2>/dev/null); do
        TITLE=$(xdotool getwindowname "$WID_ALL" 2>/dev/null || true)
        if [ -n "$TITLE" ] && ! grep -qxF "$TITLE" "$SEEN_TITLES_FILE" 2>/dev/null; then
            echo "$TITLE" >> "$SEEN_TITLES_FILE"
            echo "ACCEPTWATCH_TITLE: id=$WID_ALL title=\"$TITLE\""
        fi
    done

    WID=$(xdotool search --name "write access" 2>/dev/null | head -1)
    if [ -n "${WID:-}" ] && [ "$CAPTURED" = "0" ]; then
        echo "ACCEPTWATCH: found window id=$WID"
        xwininfo -id "$WID" 2>&1 | sed 's/^/ACCEPTWATCH_INFO: /'
        xwd -id "$WID" -out /tmp/dialog.xwd 2>&1 | sed 's/^/ACCEPTWATCH_XWD: /'
        if [ -f /tmp/dialog.xwd ]; then
            convert /tmp/dialog.xwd -resize 50% /tmp/dialog.png 2>&1 | sed 's/^/ACCEPTWATCH_CONVERT: /'
            if [ -f /tmp/dialog.png ]; then
                echo "ACCEPTWATCH_PNG_BEGIN"
                base64 -w 400 /tmp/dialog.png > /tmp/dialog.b64
                while IFS= read -r line; do
                    echo "ACCEPTWATCH_B64: $line"
                    sleep 0.05
                done < /tmp/dialog.b64
                echo "ACCEPTWATCH_PNG_END"
                CAPTURED=1
            else
                echo "ACCEPTWATCH: convert failed, no png produced"
            fi
        else
            echo "ACCEPTWATCH: xwd failed, no capture produced"
        fi
    fi
    sleep 0.3
done
