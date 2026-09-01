#!/bin/bash
# dismiss-write-access-dialog.sh
#
# Runs as an X_SCRIPTS hook (after X11 is ready) to auto-handle the
# "API client needs write access action confirmation" dialog.
#
# With Gateway 10.50.1e + IBC 3.24.2, IBC may natively handle this dialog.
# This script serves as a fallback. Strategy: wait 3s for IBC to do its
# ReadOnly uncheck, then dismiss dialog via Tab+Return or Alt+F4.
#
# Activated via Railway env var: X_SCRIPTS=x_scripts
# IMPORTANT: run_scripts() calls bash synchronously — MUST background + exit 0.

export DISPLAY=:1

echo "[dismiss-write-access] Launching dialog monitor in background"

nohup bash -c '
export DISPLAY=:1
echo "[dismiss-write-access] Monitor loop started (PID $$)"
while true; do
    WIN_ID=$(xdotool search --name "API client needs write access" 2>/dev/null | head -1)
    if [ -n "$WIN_ID" ]; then
        echo "[dismiss-write-access] Found write-access dialog (window $WIN_ID)"
        xdotool windowactivate --sync "$WIN_ID" 2>/dev/null
        # Wait for IBC to do its Alt+C / ReadOnly uncheck
        sleep 3
        WIN_ID=$(xdotool search --name "API client needs write access" 2>/dev/null | head -1)
        if [ -n "$WIN_ID" ]; then
            echo "[dismiss-write-access] Dismissing via Tab+Return"
            xdotool windowactivate --sync "$WIN_ID" 2>/dev/null
            xdotool key --window "$WIN_ID" Tab 2>/dev/null
            sleep 0.3
            xdotool key --window "$WIN_ID" Return 2>/dev/null
            sleep 2
        fi
        # Force close if still open
        WIN_ID=$(xdotool search --name "API client needs write access" 2>/dev/null | head -1)
        if [ -n "$WIN_ID" ]; then
            echo "[dismiss-write-access] Force closing with alt+F4"
            xdotool windowactivate --sync "$WIN_ID" 2>/dev/null
            xdotool key --window "$WIN_ID" alt+F4 2>/dev/null
        fi
        sleep 3
    fi
    sleep 2
done
' > /tmp/dismiss-write-access.log 2>&1 &

echo "[dismiss-write-access] Monitor started in background (PID $!)"
exit 0
