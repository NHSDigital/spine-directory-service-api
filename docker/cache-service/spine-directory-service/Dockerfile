FROM redis

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD /usr/local/bin/redis-cli PING || exit 1

CMD [ "redis-server" ]
