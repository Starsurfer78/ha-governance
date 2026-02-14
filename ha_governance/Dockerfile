ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    && ln -sf python3 /usr/bin/python

ENV PYTHONUNBUFFERED=1

# Copy requirements and install
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Copy application files
WORKDIR /app
COPY app/ /app/

# Copy s6-overlay service definitions
COPY rootfs/ /

# Copy default policies (will be overridden by /data mount)
RUN mkdir -p /data
COPY policies.yaml /data/policies.yaml

# Make scripts executable
RUN chmod a+x /etc/s6-overlay/s6-rc.d/ha_governance/run
RUN chmod a+x /etc/s6-overlay/s6-rc.d/ha_governance/finish
