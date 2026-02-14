ARG BUILD_FROM
FROM ${BUILD_FROM}

RUN apk add --no-cache python3 py3-pip

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

COPY app/ /app
COPY policies.yaml /data/policies.yaml

CMD ["/bin/sh", "-c", "python3 /app/main.py"]

