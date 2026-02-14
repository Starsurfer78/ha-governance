ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
COPY requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy data for add-on
WORKDIR /app
COPY app/ /app
COPY requirements.txt .

# Run the application
CMD [ "python3", "app/main.py" ]
