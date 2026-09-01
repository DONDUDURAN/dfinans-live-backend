# Custom wrapper image on top of gnzsnz/ib-gateway-docker's stable image.
#
# Key fixes:
# 1. Patches jts.ini.tmpl at build time to set ApiReadOnly=0 permanently.
#    Without this, every container restart resets Read-Only API mode to the
#    default (enabled), causing all order attempts to fail with Error 321.
#    The gnzsnz startup script creates jts.ini from this template only when
#    jts.ini doesn't already exist — so patching the template is the safest
#    permanent fix for ephemeral Railway containers (no persistent volume).
#
# 2. Adds xdotool/x11-utils for the accept-write-access.sh watcher script
#    (handles the "API client needs write access action confirmation" dialog
#    that appears when Read-Only mode changes while a client is connected).
FROM ghcr.io/gnzsnz/ib-gateway:stable

USER root
RUN apt-get update -y && \
    apt-get install --no-install-recommends --yes xdotool x11-utils x11-apps imagemagick && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Patch the jts.ini template to permanently disable Read-Only API mode.
# The [Logon] section already exists in the template; we insert ApiReadOnly=0
# right after it. This runs at BUILD time so it survives every container restart.
RUN find /home/ibgateway -name "jts.ini.tmpl" 2>/dev/null | while read tmpl; do \
        if ! grep -q "ApiReadOnly" "$tmpl"; then \
            sed -i '/^\[Logon\]/a ApiReadOnly=0' "$tmpl"; \
            echo "Patched Read-Only fix into: $tmpl"; \
        fi; \
    done

USER ibgateway

COPY --chown=ibgateway:ibgateway accept-write-access.sh /home/ibgateway/accept-write-access.sh
RUN chmod +x /home/ibgateway/accept-write-access.sh
