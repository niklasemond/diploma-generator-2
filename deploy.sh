#!/bin/bash

# Create fonts directory
mkdir -p fonts

# Copy the font file if it exists in the source
if [ -f "/Users/niklasemond/Dropbox/Mac (2)/Downloads/MontessoriScript.ttf" ]; then
    cp "/Users/niklasemond/Dropbox/Mac (2)/Downloads/MontessoriScript.ttf" fonts/
    echo "Font file copied successfully"
else
    echo "Warning: Font file not found in source location"
fi

# Install dependencies
pip install -r requirements.txt

# Set Python memory management
export PYTHONMALLOC=malloc
export PYTHONUNBUFFERED=1

# Start the application with memory optimization
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 1 --timeout 300 --max-requests 1 --max-requests-jitter 0 