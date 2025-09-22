FROM alpine:3.22.1
RUN addgroup -S appuser && \
    adduser -S appuser -G appuser && \
    mkdir /preload && \
    chown -R appuser:appuser /preload
COPY  preload.sqlite3 /preload/
RUN chown appuser:appuser /preload/preload.sqlite3
RUN mkdir /data
RUN chown appuser:appuser /data
USER root
CMD ["sh"]

