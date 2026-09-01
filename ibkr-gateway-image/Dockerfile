# Custom wrapper image on top of gnzsnz/ib-gateway-docker's stable image.
#
# Key fix: patches /home/ibgateway/Jts/jts.ini.tmpl at BUILD TIME to add
# ApiReadOnly=0 under [Logon]. Every container restart, apply_settings()
# creates jts.ini from this template — so ApiReadOnly=0 is permanent
# without needing a volume or runtime hooks.
#
# Background: the gnzsnz template has no ApiReadOnly setting, so TWS
# defaults to Read-Only mode on every fresh container start, causing
# all order attempts to fail with Error 321.
FROM ghcr.io/gnzsnz/ib-gateway:stable

USER root
RUN apt-get update -y && \
    apt-get install --no-install-recommends --yes xdotool x11-utils x11-apps imagemagick && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Patch the jts.ini template to disable Read-Only API permanently.
# Template path: /home/ibgateway/Jts/jts.ini.tmpl (set by TWS_PATH + TWS_INI_TMPL env vars).
RUN sed -i '/^\[Logon\]/a ApiReadOnly=0' /home/ibgateway/Jts/jts.ini.tmpl && \
    echo "BUILD: Patched jts.ini.tmpl — ApiReadOnly=0 added" && \
    grep "ApiReadOnly" /home/ibgateway/Jts/jts.ini.tmpl

USER ibgateway
