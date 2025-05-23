# Diploma Generator

A web application that generates personalized diplomas from a template PDF and a list of names.

## Features

- Upload a PDF diploma template
- Upload a text file containing names (one per line)
- Specify placeholder text to be replaced with names
- Generate individual PDF diplomas for each name
- Download all generated diplomas as a ZIP file

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create the necessary directories:
```bash
mkdir uploads templates
```

3. Run the application:
```bash
python app.py
```

## Usage

1. Open your web browser and navigate to `http://localhost:5000`
2. Upload your PDF diploma template
3. Upload a text file containing names (one name per line)
4. Enter the placeholder text that should be replaced with names
5. Click "Generate Diplomas"
6. Download the ZIP file containing all generated diplomas

## Deployment on Render

1. Create a new Web Service on Render
2. Connect your repository
3. Set the following:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Deploy!

## Notes

- The application uses temporary storage for generated files
- All files are automatically cleaned up after download
- The template PDF should contain the placeholder text exactly as specified 