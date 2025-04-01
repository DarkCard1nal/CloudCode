# syntax=docker/dockerfile:1

# Use the official Python 3.10.6 slim image as the base image
FROM python:3.10.6-slim

# Set the working directory inside the container
WORKDIR /app

# Copy necessary files
COPY requirements.txt ./
COPY run_server.py ./
COPY Server ./Server/

# Copy requirements.txt into the container
COPY requirements.txt .

# Install the Python dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the server will run on
EXPOSE 5000

# (Optional) Declare a volume for persistent uploads
# VOLUME [ "/app/uploads" ]

# Define build arguments and environment variable for debug mode
ARG DEBUG=false
ENV DEBUG_MODE=${DEBUG}
ARG WATCH=false
ENV WATCH_MODE=${WATCH}
ARG VERSION=latest
LABEL version=$VERSION

# Run the server. If DEBUG_MODE is true, the --debug flag is added.
# You can also rely on Flask's auto-reload via FLASK_ENV and FLASK_DEBUG environment variables.
CMD ["sh", "-c", "python run_server.py ${DEBUG_MODE:+--debug}"]
