ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip
RUN pip3 install "deepgram-sdk>=4.8.0" "wyoming>=1.8.0" --break-system-packages

WORKDIR /app
COPY rootfs /

COPY deepgram_server.py /app

HEALTHCHECK --start-period=10m --interval=30s --timeout=5s --retries=3 \
    CMD python3 -c "import socket; s = socket.socket(); s.settimeout(2); s.connect(('localhost', 10301)); s.sendall(b'{\"type\":\"describe\"}'); data = s.recv(1024); s.close(); exit(0 if b'deepgram' in data.lower() else 1)" \
        || exit 1
