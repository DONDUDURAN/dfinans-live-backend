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
# Activated via Railway env var: X_SCRIPTS=x_scripts
# IMPORTANT: run_scripts() calls bash synchronously, so we MUST
# detach the loop to background and exit immediately.

export DISPLAY=:1

echo "[dismiss-write-access] Launching dialog monitor in background"

nohup bash -c '
export DISPLAY=:1
echo "[dismiss-write-access] Monitor loop started (PID $$)"
while true; do
    WIN_ID=$(xdotool search --name "API client needs write access" 2>/dev/null | head -1)
    if [ -n "$WIN_ID" ]; then
        echo "[dismiss-write-access] Found dialog (window $WIN_ID), pressing Enter"
        xdotool windowactivate --sync "$WIN_ID" 2>/dev/null
        sleep 0.5
        xdotool key --window "$WIN_ID" Return 2>/dev/null
        sleep 1
        WIN_ID2=$(xdotool search --name "API client needs write access" 2>/dev/null | head -1)
        if [ -n "$WIN_ID2" ]; then
            xdotool key --window "$WIN_ID2" Escape 2>/dev/null
        fi
        sleep 2
    fi
    sleep 3
done
' > /tmp/dismiss-write-access.log 2>&1 &

echo "[dismiss-write-access] Monitor started in background (PID $!)"
# Exit immediately so run_scripts() is not blocked
exit 0
