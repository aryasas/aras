#!/bin/bash
# start.sh — kill port lama, lalu jalankan server
cd /Users/aras/Dev/aras
source venv/bin/activate

echo "Killing any process on port 8080..."
kill -9 $(lsof -ti:8080) 2>/dev/null
sleep 1

echo "Checking port 8080 is free..."
if lsof -ti:8080 > /dev/null 2>&1; then
    echo "ERROR: Port 8080 still in use!"
    lsof -ti:8080
    exit 1
fi

echo "Starting arasCore on port 8080..."
python3 run.py
