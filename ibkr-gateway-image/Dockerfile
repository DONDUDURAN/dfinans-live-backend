# Custom wrapper image on top of gnzsnz/ib-gateway-docker's LATEST image.
#
# Using 'latest' (Gateway 10.50.1e + IBC 3.24.2) instead of 'stable'
# (Gateway 10.45.1j + IBC 3.24.1). IBC 3.24.2 is designed for Gateway 10.48+
# and handles the write-access confirmation dialog that causes Error 321.
#
# Key fix: patches /home/ibgateway/Jts/jts.ini.tmpl at BUILD TIME to add
# ApiReadOnly=0 under [Logon]. Every container restart, apply_settings()
# creates jts.ini from this template — so ApiReadOnly=0 is permanent.
FROM ghcr.io/gnzsnz/ib-gateway:latest

USER root
RUN apt-get update -y && \
    apt-get install --no-install-recommends --yes xdotool x11-utils x11-apps imagemagick curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Patch the jts.ini template to disable Read-Only API permanently.
# Template path: /home/ibgateway/Jts/jts.ini.tmpl (set by TWS_PATH + TWS_INI_TMPL env vars).
RUN sed -i '/^\[Logon\]/a ApiReadOnly=0' /home/ibgateway/Jts/jts.ini.tmpl && \
    echo "BUILD: Patched jts.ini.tmpl — ApiReadOnly=0 added" && \
    grep "ApiReadOnly" /home/ibgateway/Jts/jts.ini.tmpl

# Script to auto-dismiss the "API client needs write access action confirmation" dialog.
# This dialog appears when a client connects; IBC 3.24.1 doesn't handle it.
# We run it as an X_SCRIPTS hook so it starts after X11 is ready.
COPY ibkr-gateway-image/x_scripts/dismiss-write-access-dialog.sh /home/ibgateway/x_scripts/dismiss-write-access-dialog.sh
RUN chmod +x /home/ibgateway/x_scripts/dismiss-write-access-dialog.sh && \
    chown ibgateway:ibgateway /home/ibgateway/x_scripts/dismiss-write-access-dialog.sh

USER ibgateway

# Use noVNC (port 6080, HTTP) as health check since it starts before IBKR Gateway.
# start-period=120s gives the container time to initialize before health checks begin.
HEALTHCHECK --interval=15s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -sf http://localhost:6080/ > /dev/null || exit 1
