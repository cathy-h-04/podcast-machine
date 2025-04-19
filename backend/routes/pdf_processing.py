# routes/audio_generation.py
from flask import request, jsonify
from . import pdf_processing
from . import script_generation

def generate_script_route():
    """API endpoint to convert PDF(s) to podcast, debate, or teaching script based on user preferences"""
    try:
        # Check if mode is 'summaritive' - only process this mode
        mode = request.form.get('mode', '').lower()
        if mode != 'summaritive':
            return jsonify({"error": "This endpoint only processes 'summaritive' mode requests"}), 400
        
        # Check if any files were uploaded
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400
        
        # Get all uploaded files
        files = request.files.getlist('files')
        
        # Check if any files were actually selected
        if not files or files[0].filename == '':
            return jsonify({"error": "No files selected"}), 400
        
        # Check if all files are PDFs
        if not all(pdf_processing.allowed_file(file.filename) for file in files):
            return jsonify({"error": "All files must be PDFs"}), 400
        
        # Get user message and style
        user_message = request.form.get('context', '')
        style = request.form.get('style', 'podcast').lower()
        
        # Validate style
        if style not in ['podcast', 'debate', 'duck']:
            return jsonify({"error": "Invalid style. Must be 'podcast', 'debate', or 'duck'"}), 400
        
        # Process PDF files
        pdf_texts, temp_files = pdf_processing.process_pdf_files(files)
        
        # Check if content is suitable
        is_suitable, reason = pdf_processing.check_content_suitability(pdf_texts)
        if not is_suitable:
            # Clean up temporary files
            pdf_processing.cleanup_temp_files(temp_files)
            
            return jsonify({
                "error": "Content unsuitable",
                "message": reason
            }), 400
        
        # Generate script using Claude
        script, settings = script_generation.generate_script(pdf_texts, style, user_message)
        
        # Clean up the temporary files
        pdf_processing.cleanup_temp_files(temp_files)
        
        # Return the generated script and the default settings
        return jsonify({
            "success": True, 
            "script": script,
            "settings_used": settings,
            "style": style
        }), 200
        
    except Exception as e:
        # Clean up any temporary files if they exist
        if 'temp_files' in locals():
            pdf_processing.cleanup_temp_files(temp_files)
        
        return jsonify({
            "error": "Failed to convert PDF to script",
            "message": str(e)
        }), 500