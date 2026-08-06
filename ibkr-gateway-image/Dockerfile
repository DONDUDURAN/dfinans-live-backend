# Custom wrapper image on top of gnzsnz/ib-gateway-docker's stable image.
#
# Adds xdotool/x11-utils so a watcher script (configured via the Railway
# service's custom start command, not baked in here) can detect and
# auto-accept IBKR's "API client needs write access action confirmation"
# dialog within its ~16 second auto-timeout window. IBC (IbcAlpha/IBC
# 3.24.1) has no built-in automation support for this dialog (it's new in
# IBKR's rebranded "IBKR Gateway" UI), so orders are silently rejected as
# Read-Only when the dialog times out unanswered.
#
# Baking these tools into the image (instead of apt-get at container start)
# removes ~10-15s of install latency that would otherwise eat into the
# narrow accept window.
FROM ghcr.io/gnzsnz/ib-gateway:stable

USER root
RUN apt-get update -y && \
    apt-get install --no-install-recommends --yes xdotool x11-utils x11-apps imagemagick && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
USER ibgateway

COPY --chown=ibgateway:ibgateway accept-write-access.sh /home/ibgateway/accept-write-access.sh
RUN chmod +x /home/ibgateway/accept-write-access.sh
