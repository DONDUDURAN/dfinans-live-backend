#!/bin/bash
# Pre-create jts.ini with ApiReadOnly=0 BEFORE apply_settings() runs.
#
# Why this works:
#   gnzsnz/ib-gateway's apply_settings() in common.sh checks:
#     if [ ! -f "$_JTS_PATH/$TWS_INI" ]; then create from template
#   If jts.ini already exists, it is never overwritten.
#   The template itself does not contain ApiReadOnly, so the default
#   value applied by the Gateway is 1 (Read-Only enabled), causing
#   Error 321 on every order attempt after a container restart.
#
# This script runs via START_SCRIPTS before apply_settings, so the
# jts.ini we create here is kept — and ApiReadOnly=0 is permanent
# for the lifetime of this container.

SETTINGS_DIR="${TWS_SETTINGS_PATH:-/home/ibgateway/Jts}"
mkdir -p "$SETTINGS_DIR"
JTS_FILE="$SETTINGS_DIR/jts.ini"

if [ -f "$JTS_FILE" ]; then
    # File already exists (e.g. mounted volume). Patch ApiReadOnly in-place.
    if grep -qi "ApiReadOnly" "$JTS_FILE"; then
        sed -i 's/ApiReadOnly=1/ApiReadOnly=0/gI' "$JTS_FILE"
        sed -i 's/ApiReadOnly=yes/ApiReadOnly=no/gI' "$JTS_FILE"
        sed -i 's/ApiReadOnly=true/ApiReadOnly=false/gI' "$JTS_FILE"
        echo "fix-readonly: Patched existing ApiReadOnly in $JTS_FILE"
    else
        # Add ApiReadOnly=0 under [Logon] if present, else append to file
        if grep -q "^\[Logon\]" "$JTS_FILE"; then
            sed -i '/^\[Logon\]/a ApiReadOnly=0' "$JTS_FILE"
        else
            echo "ApiReadOnly=0" >> "$JTS_FILE"
        fi
        echo "fix-readonly: Inserted ApiReadOnly=0 into existing $JTS_FILE"
    fi
else
    # File does not exist — create a minimal jts.ini with ApiReadOnly=0.
    # apply_settings() will skip creation because the file will exist.
    cat > "$JTS_FILE" << JTSEOF
[IBGateway]
WriteDebug=false
TrustedIPs=*
ApiOnly=true

[Logon]
Locale=en
TimeZone=${TIME_ZONE:-Etc/UTC}
displayedproxymsg=1
UseSSL=true
s3store=true
ApiReadOnly=0

[Communication]
JTSEOF
    echo "fix-readonly: Created $JTS_FILE with ApiReadOnly=0"
fi
