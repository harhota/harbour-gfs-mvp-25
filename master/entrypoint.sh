#!/bin/bash

echo "Starting master server..."
uvicorn master:app --host 0.0.0.0 --port 8000