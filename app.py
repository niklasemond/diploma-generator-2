import os
import logging
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import io
import tempfile
import zipfile
from datetime import datetime

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def replace_text_in_pdf(template_path, name, placeholder):
    try:
        # Open the PDF
        doc = fitz.open(template_path)
        
        # Process each page
        for page in doc:
            # Search for the placeholder text
            text_instances = page.search_for(placeholder)
            
            if not text_instances:
                logger.warning(f"Placeholder '{placeholder}' not found on page")
                continue
            
            # Get the first instance of the placeholder
            rect = text_instances[0]
            
            # Get the original text's properties
            text_info = page.get_text("dict")
            
            # Calculate text width for centering
            font_size = 28
            text_width = fitz.get_text_length(name, fontname="helv", fontsize=font_size)
            
            # Calculate the center position
            center_x = rect.x0 + (rect.width - text_width) / 2
            
            # Remove the placeholder text
            page.add_redact_annot(rect)
            page.apply_redactions()
            
            # Insert the new name centered in the same area
            page.insert_text(
                (center_x, rect.y0),  # centered position
                name,
                fontsize=font_size,
                color=(0, 0, 0),
                render_mode=0
            )
        
        # Save to BytesIO with compression
        output = io.BytesIO()
        doc.save(
            output,
            garbage=4,  # Maximum garbage collection
            deflate=True,  # Compress streams
            clean=True,  # Clean redundant elements
            pretty=False,  # Don't pretty-print
            linear=True  # Optimize for web viewing
        )
        output.seek(0)
        doc.close()
        
        return output
    except Exception as e:
        logger.error(f"Error in replace_text_in_pdf: {str(e)}")
        raise

def create_pdf_with_name(template_path, name, placeholder):
    try:
        logger.info(f"Processing PDF for name: {name}")
        return replace_text_in_pdf(template_path, name, placeholder)
    except Exception as e:
        logger.error(f"Error in create_pdf_with_name: {str(e)}")
        raise

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        try:
            # Check if files were uploaded
            if 'template' not in request.files or 'names' not in request.files:
                flash('Both template and names files are required')
                return redirect(request.url)
            
            template_file = request.files['template']
            names_file = request.files['names']
            placeholder = request.form.get('placeholder', '{{name}}').strip()
            
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
            names_file.seek(0)
            content = names_file.read().decode('utf-8')
            names = [line.strip() for line in content.splitlines() if line.strip()]
            
            if not names:
                flash('The names file is empty')
                return redirect(request.url)
            
            if len(names) > 500:
                flash('Maximum 500 names allowed')
                return redirect(request.url)
            
            logger.info(f"Processing {len(names)} names")
            
            # Create a temporary directory for generated PDFs
            with tempfile.TemporaryDirectory() as temp_dir:
                # Process each name
                for name in names:
                    try:
                        # Get the PDF as a BytesIO object
                        pdf_bytes = create_pdf_with_name(template_path, name, placeholder)
                        
                        # Create a clean filename from the name
                        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', 'Å', 'Ä', 'Ö', 'å', 'ä', 'ö')).strip()
                        output_path = os.path.join(temp_dir, f"{clean_name}.pdf")
                        
                        # Write the PDF to disk
                        with open(output_path, 'wb') as output_file:
                            output_file.write(pdf_bytes.getvalue())
                        
                        # Clean up the BytesIO object
                        pdf_bytes.close()
                        
                    except Exception as e:
                        logger.error(f"Error processing name {name}: {str(e)}")
                        flash(f'Error processing name "{name}": {str(e)}')
                        return redirect(request.url)
                
                # Create a zip file containing all PDFs
                zip_path = os.path.join(temp_dir, 'diplomas.zip')
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file in os.listdir(temp_dir):
                        if file.endswith('.pdf'):
                            file_path = os.path.join(temp_dir, file)
                            # Add files directly to the root of the zip
                            zipf.write(file_path, file)
                
                # Send the zip file
                return send_file(zip_path, as_attachment=True, download_name='diplomas.zip')
            
        except Exception as e:
            logger.error(f"Error in upload_files: {str(e)}")
            flash(f'Error processing files: {str(e)}')
            return redirect(request.url)
        finally:
            # Clean up the template file
            if os.path.exists(template_path):
                os.remove(template_path)
    
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port) 