# routes/pdf_processing.py
from flask import request, jsonify
from . import script_generation
import base64
import tempfile
import os


def allowed_file(filename):
    """Check if the file is a PDF"""
    return filename.lower().endswith(".pdf")


def cleanup_temp_files(temp_files):
    """Clean up temporary files"""
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def process_pdf_files(base64_files):
    """Process base64-encoded PDF files and return extracted text"""
    import PyPDF2  # Import PyPDF2 for PDF text extraction

    pdf_texts = []
    temp_files = []

    for file_data in base64_files:
        # Decode base64 data
        try:
            # Create a temporary file
            fd, temp_path = tempfile.mkstemp(suffix=".pdf")
            temp_files.append(temp_path)

            # Write decoded PDF to temporary file
            with os.fdopen(fd, "wb") as tmp:
                pdf_content = base64.b64decode(file_data)
                tmp.write(pdf_content)

            # Extract text from the PDF file using PyPDF2
            text = ""
            with open(temp_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                # Extract text from each page
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"

            pdf_texts.append(text)

        except Exception as e:
            # Clean up if there's an error
            cleanup_temp_files(temp_files)
            raise e

    return pdf_texts, temp_files


def check_content_suitability(pdf_texts):
    """Check if content is suitable for processing"""
    # Implementation would check for inappropriate content
    # For now, returning True for simplicity
    return True, ""


def generate_script_route():
    """API endpoint to convert PDF(s) to podcast, debate, or teaching script based on user preferences"""
    try:
        # Get JSON data from request
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Check if mode is 'summaritive' - only process this mode
        mode = data.get("mode", "").lower()
        if mode != "summaritive":
            return jsonify(
                {"error": "This endpoint only processes 'summaritive' mode requests"}
            ), 400

        # Check if any files were uploaded
        if "files" not in data or not data["files"]:
            return jsonify({"error": "No files uploaded"}), 400

        # Get all base64 encoded files
        base64_files = data["files"]

        # Get user message and style
        user_message = data.get("context", "")
        style = data.get("style", "podcast").lower()

        # Validate style
        if style not in ["podcast", "debate", "duck"]:
            return jsonify(
                {"error": "Invalid style. Must be 'podcast', 'debate', or 'duck'"}
            ), 400

        # Process PDF files
        pdf_texts, temp_files = process_pdf_files(base64_files)

        # Check if content is suitable
        is_suitable, reason = check_content_suitability(pdf_texts)
        if not is_suitable:
            # Clean up temporary files
            cleanup_temp_files(temp_files)

            return jsonify({"error": "Content unsuitable", "message": reason}), 400

        # Generate script using Claude
        script, settings = script_generation.generate_script(
            pdf_texts, style, user_message
        )

        # Clean up the temporary files
        cleanup_temp_files(temp_files)

        # Return the generated script and the default settings
        return jsonify(
            {
                "success": True,
                "script": script,
                "settings_used": settings,
                "style": style,
            }
        ), 200

    except Exception as e:
        # Clean up any temporary files if they exist
        if "temp_files" in locals():
            cleanup_temp_files(temp_files)

        return jsonify(
            {"error": "Failed to convert PDF to script", "message": str(e)}
        ), 500
