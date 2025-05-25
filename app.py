import os
import logging
import gc
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
DEFAULT_FONT = 'Times-Roman'  # Changed from MontessoriScript to Times-Roman

# Font mapping for common PDF fonts to system fonts
FONT_MAPPING = {
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
    # Remove any subset prefix (e.g., "ABCDEF+Times-Roman" -> "Times-Roman")
    base_font = font_name.split('+')[-1]
    return FONT_MAPPING.get(base_font, DEFAULT_FONT)

def create_pdf_with_name(template_path, name, placeholder):
    try:
        logger.info(f"Processing PDF for name: {name}")
        
        # Read the template PDF
        reader = PdfReader(template_path)
        if len(reader.pages) == 0:
            raise ValueError("The template PDF is empty")
        
        # Create a new PDF
        writer = PdfWriter()
        
        # Get the first page
        page = reader.pages[0]
        
        # Create a new page with the name
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        
        # Set font and size
        can.setFont("Times-Roman", 28)
        
        # Calculate text width for centering
        text_width = can.stringWidth(name, "Times-Roman", 28)
        page_width = float(page.mediabox.width)
        x = (page_width - text_width) / 2
        
        # Draw the text
        can.drawString(x, 400, name)  # y=400 is a reasonable position, adjust if needed
        can.save()
        
        # Move to the beginning of the StringIO buffer
        packet.seek(0)
        
        # Create a new PDF with the text
        new_pdf = PdfReader(packet)
        
        # Add the page from the template
        writer.add_page(page)
        
        # Overlay the text on the template page
        page.merge_page(new_pdf.pages[0])
        
        # Save the output
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        
        return output
    except Exception as e:
        logger.error(f"Error in create_pdf_with_name: {str(e)}")
        raise
    finally:
        gc.collect()

def process_names_in_batches(names, template_path, placeholder, temp_dir, batch_size=1):
    """Process names in smaller batches to manage memory usage."""
    for i in range(0, len(names), batch_size):
        batch = names[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} of {(len(names) + batch_size - 1)//batch_size}")
        
        for name in batch:
            try:
                logger.info(f"Processing name: {name}")
                # Get the PDF as a BytesIO object
                pdf_bytes = create_pdf_with_name(template_path, name, placeholder)
                
                # Create a clean filename from the name, preserving Swedish characters
                clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', 'Å', 'Ä', 'Ö', 'å', 'ä', 'ö')).strip()
                output_path = os.path.join(temp_dir, f"{clean_name}.pdf")
                
                # Write the PDF to disk
                with open(output_path, 'wb') as output_file:
                    output_file.write(pdf_bytes.getvalue())
                
                # Clean up the BytesIO object
                pdf_bytes.close()
                
            except ValueError as ve:
                flash(f'Error processing name "{name}": {str(ve)}')
                return False
            except Exception as e:
                logger.error(f"Error processing name {name}: {str(e)}")
                flash(f'Error processing name "{name}": {str(e)}')
                return False
            
            # Force garbage collection after each name
            gc.collect()
        
        # Force garbage collection after each batch
        gc.collect()
    
    return True

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # TODO: Implement file processing
        pass
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port) 