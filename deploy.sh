#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Set Python memory management
export PYTHONMALLOC=malloc
export PYTHONUNBUFFERED=1

# Start the application with memory optimization
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 1 --timeout 300 --max-requests 1 --max-requests-jitter 0 