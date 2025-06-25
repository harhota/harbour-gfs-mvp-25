#!/bin/bash

# Start backend (starter.py) in background
python3 /app/starter.py &

# Build frontend static assets
cd /app/webapp
npm run build

# Optionally, serve the built frontend or just keep backend running
wait -n