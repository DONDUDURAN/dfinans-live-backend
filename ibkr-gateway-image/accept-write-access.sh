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

        # Click the "Configure API Settings" button (bottom-left button of
        # this dialog, no "grant access" button exists - the dialog is
        # purely informational, telling the user Read-Only API is still
        # checked in Global Configuration and must be manually unchecked
        # there). Button offset determined empirically from a prior
        # screenshot capture of this exact dialog (602x210 window).
        GEOM=$(xdotool getwindowgeometry --shell "$WID" 2>/dev/null)
        WX=$(echo "$GEOM" | grep '^X=' | cut -d= -f2)
        WY=$(echo "$GEOM" | grep '^Y=' | cut -d= -f2)
        if [ -n "${WX:-}" ] && [ -n "${WY:-}" ]; then
            CLICK_X=$((WX + 260))
            CLICK_Y=$((WY + 185))
            echo "ACCEPTWATCH: activating window and clicking Configure API Settings at $CLICK_X,$CLICK_Y"
            xdotool windowactivate --sync "$WID" 2>&1 | sed 's/^/ACCEPTWATCH_ACTIVATE: /'
            xdotool windowfocus --sync "$WID" 2>&1 | sed 's/^/ACCEPTWATCH_FOCUS: /'
            xdotool windowraise "$WID" 2>&1 | sed 's/^/ACCEPTWATCH_RAISE: /'
            sleep 0.3
            xdotool mousemove --sync "$CLICK_X" "$CLICK_Y"
            sleep 0.2
            xdotool click --clearmodifiers 1
            sleep 1.5
        else
            echo "ACCEPTWATCH: could not determine window geometry, skipping click"
        fi

        # Capture the resulting screen (the write-access dialog itself may
        # have closed/been replaced by the actual Global Configuration
        # window at this point) - capture the whole root window so we can
        # see whatever appeared after clicking.
        xwd -root -out /tmp/dialog.xwd 2>&1 | sed 's/^/ACCEPTWATCH_XWD: /'
        if [ -f /tmp/dialog.xwd ]; then
            convert /tmp/dialog.xwd -resize 40% /tmp/dialog.png 2>&1 | sed 's/^/ACCEPTWATCH_CONVERT: /'
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
