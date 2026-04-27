# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for mariadb client
RUN apt-get update && apt-get install -y 
    default-libmysqlclient-dev 
    build-essential 
    pkg-config 
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
# Using 'python run.py' as confirmed from run.py
CMD ["python", "run.py"]
