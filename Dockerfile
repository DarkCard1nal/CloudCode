# syntax=docker/dockerfile:1

# Use the official Python 3.10.6 slim image as the base image
FROM python:3.10.6-slim

RUN apt-get update && apt-get install -y \
    curl gnupg apt-transport-https ca-certificates \
    gcc g++ \
    unixodbc unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy necessary files
COPY requirements.txt ./
COPY run_server.py ./
COPY Server ./Server/
COPY Tests/server ./Tests/server/
COPY Tests/run_server_tests.py ./Tests/
COPY Tests/environment.py ./Tests/
COPY behave.ini ./
COPY WebClient ./WebClient/

# Copy requirements.txt into the container
COPY requirements.txt .

# Install the Python dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir behave pytest

# Expose the port the server will run on
EXPOSE 5000

# (Optional) Declare a volume for persistent uploads
VOLUME [ "/app/uploads" ]
VOLUME [ "/app/cloudcode_sql" ]

# Define build arguments and environment variable for debug mode
ARG DEBUG=false
ENV DEBUG_MODE=${DEBUG}
ARG WATCH=false
ENV WATCH_MODE=${WATCH}
ARG VERSION=latest
LABEL version=$VERSION

# Set Python path for imports
ENV PYTHONPATH=/app

# Run the server. If DEBUG_MODE is true, the --debug flag is added.
# You can also rely on Flask's auto-reload via FLASK_ENV and FLASK_DEBUG environment variables.
CMD ["sh", "-c", "cp /app/Server/SETUP.sql /cloudcode_sql/SETUP.sql && python run_server.py ${DEBUG_MODE:+--debug}"]
