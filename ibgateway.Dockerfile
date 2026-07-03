FROM waytrade/ibkr-gateway:latest

EXPOSE 4001 4002

ENV TWSUSER=${TWSUSER}
ENV TWSPASS=${TWSPASS}
ENV TRADING_MODE=paper
ENV IBC_INI=/home/ibgateway/ibc/config.ini

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:4001/status || exit 1
