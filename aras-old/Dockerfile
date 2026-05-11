# Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

# Install dependencies for adding MariaDB repository and downloading
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Add MariaDB official repository and install newer libmariadb-dev
RUN curl -LsS https://downloads.mariadb.com/MariaDB/mariadb_repo_setup | bash \
    && apt-get update && apt-get install -y --no-install-recommends \
    libmariadb-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Define environment variable for Flask
ENV FLASK_APP=run.py
ENV FLASK_RUN_PORT=8080

# Command to run the application
CMD ["python", "run.py"]
CMD ["python", "run.py"]
