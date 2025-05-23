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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'pdf', 'txt'}

# Font configuration
FONT_PATH = os.path.join(os.path.dirname(__file__), 'fonts', 'MontessoriScript.ttf')
DEFAULT_FONT = 'Helvetica'

# Try to register the MontessoriScript font, fall back to Helvetica if not available
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont('MontessoriScript', FONT_PATH))
        DEFAULT_FONT = 'MontessoriScript'
except Exception as e:
    print(f"Warning: Could not load MontessoriScript font: {e}")

# Font mapping for common PDF fonts to system fonts
FONT_MAPPING = {
    'MontessoriScript': DEFAULT_FONT,  # Use our embedded font or fallback
    'Times-Roman': 'Times-Roman',
    'Times-Bold': 'Times-Bold',
    'Times-Italic': 'Times-Italic',
    'Times-BoldItalic': 'Times-BoldItalic',
    'Helvetica': 'Helvetica',
    'Helvetica-Bold': 'Helvetica-Bold',
    'Helvetica-Oblique': 'Helvetica-Oblique',
    'Helvetica-BoldOblique': 'Helvetica-BoldOblique',
    'Courier': 'Courier',
    'Courier-Bold': 'Courier-Bold',
    'Courier-Oblique': 'Courier-Oblique',
    'Courier-BoldOblique': 'Courier-BoldOblique',
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_system_font(font_name):
    """Convert PDF font name to a system font that ReportLab can use."""
    # Remove any subset prefix (e.g., "ABCDEF+MontessoriScript" -> "MontessoriScript")
    base_font = font_name.split('+')[-1]
    return FONT_MAPPING.get(base_font, DEFAULT_FONT)

def create_pdf_with_name(template_path, name, placeholder):
    # Open the PDF with PyMuPDF
    doc = fitz.open(template_path)
    
    # Check if the PDF has any pages
    if len(doc) == 0:
        raise ValueError("The template PDF is empty")
    
    page = doc[0]  # Get first page
    
    # Search for the placeholder text
    text_instances = page.search_for(placeholder)
    
    if not text_instances:
        raise ValueError(f"Placeholder text '{placeholder}' not found in the template")
    
    # Get the first instance of the placeholder
    rect = text_instances[0]
    
    # Get the font information from the placeholder text
    text_blocks = page.get_text("dict")["blocks"]
    font_size = None
    font_name = None
    
    for block in text_blocks:
        if "lines" in block:
            for line in block["lines"]:
                if "spans" in line:
                    for span in line["spans"]:
                        if placeholder in span["text"]:
                            font_size = span["size"]
                            font_name = span["font"]
                            break
    
    # If we couldn't find the font information, use defaults
    if not font_size:
        font_size = 12
    if not font_name:
        font_name = DEFAULT_FONT
    
    # Convert PDF font to system font
    system_font = get_system_font(font_name)
    
    # Create a new PDF with the name
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page.rect.width, page.rect.height))
    
    # Calculate the position and size
    x = rect.x0
    y = page.rect.height - rect.y1  # Convert from PDF coordinates to canvas coordinates
    width = rect.width
    height = rect.height
    
    # Add the name text with the system font
    can.setFont(system_font, font_size)
    can.setFillColor(Color(0, 0, 0))  # Black color
    
    # Ensure the name is properly encoded and handle Swedish characters
    if isinstance(name, bytes):
        name = name.decode('utf-8')
    
    # Draw the name centered in the placeholder's rectangle
    # Use drawString instead of drawCentredString for better character support
    text_width = can.stringWidth(name, system_font, font_size)
    x_centered = x + (width - text_width) / 2
    y_centered = y + (height - font_size) / 2
    can.drawString(x_centered, y_centered, name)
    
    can.save()
    
    # Move to the beginning of the StringIO buffer
    packet.seek(0)
    new_pdf = PdfReader(packet)
    
    # Read the template PDF
    template = PdfReader(template_path)
    output = PdfWriter()
    
    # Process each page
    for i in range(len(template.pages)):
        # Get the page
        page = template.pages[i]
        
        # Create a new page with the same content
        new_page = page
        
        # Remove the placeholder text by replacing it with an empty string
        page_text = page.extract_text()
        if placeholder in page_text:
            # Create a new PDF without the placeholder text
            packet_clean = io.BytesIO()
            can_clean = canvas.Canvas(packet_clean, pagesize=(page.mediabox.width, page.mediabox.height))
            can_clean.save()
            packet_clean.seek(0)
            clean_pdf = PdfReader(packet_clean)
            
            # Merge the clean PDF to remove the placeholder
            new_page.merge_page(clean_pdf.pages[0])
        
        # Only merge the name PDF on the first page
        if i == 0:
            new_page.merge_page(new_pdf.pages[0])
        
        output.add_page(new_page)
    
    # Close the PyMuPDF document
    doc.close()
    
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
        
        template_path = None
        try:
            # Save the template file
            template_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(template_file.filename))
            template_file.save(template_path)
            
            # Read names from the text file with UTF-8 encoding
            names_file.seek(0)
            content = names_file.read()
            try:
                # Try to decode as UTF-8
                decoded_content = content.decode('utf-8')
            except UnicodeDecodeError:
                # If UTF-8 fails, try with latin-1 (which can handle Swedish characters)
                decoded_content = content.decode('latin-1')
            
            # Split into lines and clean up
            names = [line.strip() for line in decoded_content.splitlines() if line.strip()]
            
            if not names:
                flash('The names file is empty')
                return redirect(request.url)
            
            # Create a temporary directory for generated PDFs
            with tempfile.TemporaryDirectory() as temp_dir:
                # Generate PDFs for each name
                for name in names:
                    try:
                        # Ensure name is a string and properly encoded
                        if isinstance(name, bytes):
                            name = name.decode('utf-8')
                        
                        output_pdf = create_pdf_with_name(template_path, name, placeholder)
                        # Create a clean filename from the name, preserving Swedish characters
                        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', 'Å', 'Ä', 'Ö', 'å', 'ä', 'ö')).strip()
                        output_path = os.path.join(temp_dir, f"{clean_name}.pdf")
                        with open(output_path, 'wb') as output_file:
                            output_pdf.write(output_file)
                    except ValueError as ve:
                        flash(f'Error processing name "{name}": {str(ve)}')
                        return redirect(request.url)
                    except Exception as e:
                        flash(f'Error processing name "{name}": {str(e)}')
                        return redirect(request.url)
                
                # Create a zip file containing all PDFs
                import zipfile
                zip_path = os.path.join(temp_dir, 'diplomas.zip')
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file in os.listdir(temp_dir):
                        if file.endswith('.pdf'):
                            file_path = os.path.join(temp_dir, file)
                            # Add files directly to the root of the zip
                            zipf.write(file_path, file)
                
                # Send the zip file
                return send_file(zip_path, as_attachment=True, download_name='diplomas.zip')
        except ValueError as ve:
            flash(f'Error: {str(ve)}')
            return redirect(request.url)
        except Exception as e:
            flash(f'Error processing files: {str(e)}')
            return redirect(request.url)
        finally:
            # Clean up the template file
            if template_path and os.path.exists(template_path):
                os.remove(template_path)
    
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port) 