import os
import uuid
import tempfile
from flask import Flask, Blueprint, request, send_file, render_template, jsonify, url_for, current_app
from app.utils.downloader import download_content, DOWNLOAD_DIR

bp = Blueprint('main', __name__)

# Create a temporary directory that will be cleaned up automatically
DOWNLOAD_DIR = tempfile.mkdtemp()

@bp.route('/', methods=['GET', 'POST'])
def download_youtube():
    if request.method == 'POST':
        current_app.logger.info("POST request received")
        
        youtube_url = request.form['url']
        format_type = request.form['format']
        quality = request.form.get('quality', 'best')
        
        try:
            current_app.logger.info(f"Attempting to download: {youtube_url} as {format_type} with quality {quality}")
            
            # Generate a unique filename
            unique_filename = f"{uuid.uuid4().hex}.{format_type}"
            output_path = os.path.join(DOWNLOAD_DIR, unique_filename)
            
            file_path = download_content(youtube_url, output_path, format_type, quality)
            
            if not file_path or not os.path.exists(file_path):
                current_app.logger.error(f"Failed to find the downloaded {format_type.upper()} file.")
                return jsonify({"error": f"Failed to find the downloaded {format_type.upper()} file."}), 400
            
            current_app.logger.info(f"File saved to: {file_path}")
            
            # Return the download URL
            download_url = url_for('main.serve_file', filename=os.path.basename(file_path), _external=True)
            return jsonify({"download_url": download_url, "message": "Download started, please wait..."})
                
        except Exception as e:
            current_app.logger.error(f"An error occurred: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    return render_template('index.html')

@bp.route('/download/<filename>')
def serve_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    response = send_file(file_path, as_attachment=True)
    
    # Delete the file after sending it to the client
    @response.call_on_close
    def remove_file():
        try:
            os.remove(file_path)
            current_app.logger.info(f"Deleted temporary file: {file_path}")
        except Exception as e:
            current_app.logger.error(f"Failed to delete temporary file: {str(e)}")
    
    return response