# Diploma Generator

A web application that generates personalized diplomas by replacing placeholders in a PDF template with names from a text file.

## Features

- Upload a PDF diploma template
- Upload a text file containing names (one per line)
- Specify the placeholder text to be replaced
- Generate individual PDF diplomas for each name
- Download all generated diplomas as a ZIP file

## Setup

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to `http://localhost:5000`

## Usage

1. Prepare your files:
   - A PDF template with a placeholder (e.g., "{{name}}")
   - A text file with one name per line

2. On the web interface:
   - Upload your PDF template
   - Upload your names text file
   - Enter the placeholder text (default: "{{name}}")
   - Click "Generate Diplomas"

3. A ZIP file containing all generated diplomas will be downloaded automatically

## Requirements

- Python 3.8 or higher
- Modern web browser
- PDF template with text placeholders
- Text file with names (one per line)

## Notes

- Maximum file size: 16MB
- Supported file types: PDF (template) and TXT (names)
- The application processes files in memory and does not store them on the server

## Deployment on Render

1. Create a new Web Service on Render
2. Connect your repository
3. Set the following:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Deploy! 