ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Python
RUN apk add --no-cache \
    python3 \
    py3-pip

ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Copy application
WORKDIR /app
COPY app/ /app/

# Copy run script
COPY run.sh /
RUN chmod a+x /run.sh

# Copy default policies
RUN mkdir -p /data
COPY policies.yaml /data/policies.yaml
