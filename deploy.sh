#!/bin/bash

# Create fonts directory if it doesn't exist
mkdir -p fonts

# Copy the font file if it exists in the source
if [ -f "/Users/niklasemond/Dropbox/Mac (2)/Downloads/MontessoriScript.ttf" ]; then
    cp "/Users/niklasemond/Dropbox/Mac (2)/Downloads/MontessoriScript.ttf" fonts/
fi

# Install dependencies
pip install -r requirements.txt

# Start the application
gunicorn app:app --bind 0.0.0.0:$PORT 