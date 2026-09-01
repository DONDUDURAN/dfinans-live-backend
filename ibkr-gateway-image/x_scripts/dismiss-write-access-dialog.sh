#!/bin/bash
# dismiss-write-access-dialog.sh
#
# Runs as an X_SCRIPTS hook (after X11 is ready) to auto-close the
# "API client needs write access action confirmation" dialog that appears
# when an API client first connects to IB Gateway.
#
# IBC 3.24.1 detects this dialog but cannot close it (no "Accept" button).
# This script monitors for the dialog using xdotool and presses Enter to
# dismiss it, allowing the client to proceed with write access.
#
# Activated via Railway env var: X_SCRIPTS=/home/ibgateway/x_scripts

export DISPLAY=:1

echo "[dismiss-write-access] Starting dialog monitor loop"

while true; do
    # Look for the write-access confirmation dialog
    WIN_ID=$(xdotool search --name "API client needs write access" 2>/dev/null | head -1)

    if [ -n "$WIN_ID" ]; then
        echo "[dismiss-write-access] Found dialog (window $WIN_ID), pressing Enter to dismiss"
        xdotool windowactivate --sync "$WIN_ID" 2>/dev/null
        sleep 0.3
        # Press Enter — on this dialog, Enter activates the default (Close) button.
        # We also try Tab+Enter to move focus to the second button if needed.
        xdotool key --window "$WIN_ID" Return 2>/dev/null
        sleep 1
        # Double-check it's gone; if still open, try Escape
        WIN_ID2=$(xdotool search --name "API client needs write access" 2>/dev/null | head -1)
        if [ -n "$WIN_ID2" ]; then
            echo "[dismiss-write-access] Dialog still open, trying Escape"
            xdotool key --window "$WIN_ID2" Escape 2>/dev/null
        fi
        sleep 2
    fi

    sleep 3
done
