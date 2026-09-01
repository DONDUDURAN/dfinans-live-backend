# Custom wrapper image on top of gnzsnz/ib-gateway-docker's stable image.
#
# Key fixes:
# 1. Adds a START_SCRIPTS startup hook (00-fix-readonly.sh) that pre-creates
#    jts.ini with ApiReadOnly=0 before gnzsnz's apply_settings() runs.
#    apply_settings() skips jts.ini creation when the file already exists,
#    so our version with ApiReadOnly=0 is kept for the container's lifetime.
#    Without this, every restart resets Read-Only API to the default (enabled),
#    causing all orders to fail with Error 321.
#
# 2. Adds xdotool/x11-utils for the accept-write-access.sh watcher script.
FROM ghcr.io/gnzsnz/ib-gateway:stable

USER root
RUN apt-get update -y && \
    apt-get install --no-install-recommends --yes xdotool x11-utils x11-apps imagemagick && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
USER ibgateway

COPY --chown=ibgateway:ibgateway accept-write-access.sh /home/ibgateway/accept-write-access.sh
RUN chmod +x /home/ibgateway/accept-write-access.sh

# Copy startup hook that pre-creates jts.ini with ApiReadOnly=0.
# Enabled via START_SCRIPTS=start_scripts env var (set in Railway service).
COPY --chown=ibgateway:ibgateway start_scripts/ /home/ibgateway/start_scripts/
RUN chmod +x /home/ibgateway/start_scripts/*.sh
