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

while true; do
    WID=$(xdotool search --name "IBKR Gateway" 2>/dev/null | head -1)
    if [ -n "${WID:-}" ] && [ "$CAPTURED" = "0" ]; then
        echo "ACCEPTWATCH: found window id=$WID"
        xwininfo -id "$WID" 2>&1 | sed 's/^/ACCEPTWATCH_INFO: /'
        xwd -id "$WID" -out /tmp/dialog.xwd 2>&1 | sed 's/^/ACCEPTWATCH_XWD: /'
        if [ -f /tmp/dialog.xwd ]; then
            convert /tmp/dialog.xwd /tmp/dialog.png 2>&1 | sed 's/^/ACCEPTWATCH_CONVERT: /'
            if [ -f /tmp/dialog.png ]; then
                echo "ACCEPTWATCH_PNG_BEGIN"
                base64 -w 100 /tmp/dialog.png | sed 's/^/ACCEPTWATCH_B64: /'
                echo "ACCEPTWATCH_PNG_END"
                CAPTURED=1
            else
                echo "ACCEPTWATCH: convert failed, no png produced"
            fi
        else
            echo "ACCEPTWATCH: xwd failed, no capture produced"
        fi
    fi
    sleep 0.5
done
