#!/bin/bash

echo "🚀 Starting Master Server..."
uvicorn master:app --host 0.0.0.0 --port 8000
