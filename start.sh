#!/bin/bash
# Handle the PORT environment variable properly
if [[ "$PORT" =~ ^[0-9]+$ ]]; then
    echo "Using port: $PORT"
    exec uvicorn main:app --host 0.0.0.0 --port $PORT
else
    echo "Invalid or missing PORT, using default 10000"
    exec uvicorn main:app --host 0.0.0.0 --port 10000
fi