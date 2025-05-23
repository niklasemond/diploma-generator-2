import os
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import tempfile
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color
import fitz  # PyMuPDF

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_pdf_with_name(template_path, name, placeholder):
    # Open the PDF with PyMuPDF to get precise text positions
    doc = fitz.open(template_path)
    page = doc[0]  # Get first page
    
    # Search for the placeholder text
    text_instances = page.search_for(placeholder)
    
    if not text_instances:
        raise ValueError(f"Placeholder text '{placeholder}' not found in the template")
    
    # Get the first instance of the placeholder
    rect = text_instances[0]
    
    # Create a new PDF with the name
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page.rect.width, page.rect.height))
    
    # Calculate the position and size
    x = rect.x0
    y = page.rect.height - rect.y1  # Convert from PDF coordinates to canvas coordinates
    width = rect.width
    height = rect.height
    
    # Add the name text
    can.setFont("Helvetica", height * 0.8)  # Scale font size based on placeholder height
    can.setFillColor(Color(0, 0, 0))  # Black color
    
    # Draw the name centered in the placeholder's rectangle
    can.drawCentredString(x + width/2, y + height/2, name)
    
    can.save()
    
    # Move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfReader(packet)
    
    # Read the template PDF
    template = PdfReader(template_path)
    output = PdfWriter()
    
    # Process each page
    for page in template.pages:
        # Merge the name PDF with the template
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)
    
    return output

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # Check if files were uploaded
        if 'template' not in request.files or 'names' not in request.files:
            flash('Both template and names files are required')
            return redirect(request.url)
        
        template_file = request.files['template']
        names_file = request.files['names']
        placeholder = request.form.get('placeholder', '').strip()
        
        if not placeholder:
            flash('Placeholder text is required')
            return redirect(request.url)
        
        if template_file.filename == '' or names_file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if not (allowed_file(template_file.filename) and allowed_file(names_file.filename)):
            flash('Invalid file type')
            return redirect(request.url)
        
        # Save the template file
        template_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(template_file.filename))
        template_file.save(template_path)
        
        # Read names from the text file
        names = [line.strip() for line in names_file.readlines() if line.strip()]
        
        # Create a temporary directory for generated PDFs
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate PDFs for each name
            for name in names:
                output_pdf = create_pdf_with_name(template_path, name, placeholder)
                output_path = os.path.join(temp_dir, f"{name}.pdf")
                with open(output_path, 'wb') as output_file:
                    output_pdf.write(output_file)
            
            # Create a zip file containing all PDFs
            import zipfile
            zip_path = os.path.join(temp_dir, 'diplomas.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.pdf'):
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, os.path.basename(file_path))
            
            # Send the zip file
            return send_file(zip_path, as_attachment=True, download_name='diplomas.zip')
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True) 