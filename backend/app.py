#!/usr/bin/env python3
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
import anthropic
import PyPDF2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure upload settings
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {"pdf"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB limit

# Path to the system prompt template file
PROMPT_TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "system_prompt.txt"
)

# Initialize Claude client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_system_prompt_template():
    """Load the system prompt template from the external file"""
    try:
        with open(PROMPT_TEMPLATE_PATH, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"System prompt template file not found at {PROMPT_TEMPLATE_PATH}"
        )
    except Exception as e:
        raise Exception(f"Error loading system prompt template: {str(e)}")


def extract_text_from_pdf(pdf_path):
    """Extract text content from a PDF file"""
    text = ""

    with open(pdf_path, "rb") as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Extract text from each page
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"

    return text


def generate_podcast_script(pdf_text, options):
    """Generate a podcast script from PDF text using Claude"""
    # Unpack options with defaults
    host_name = options.get("host_name", "Host")
    guest_name = options.get("guest_name", "Guest")
    podcast_title = options.get("podcast_title", "PDF Discussion")
    length_in_minutes = options.get("length_in_minutes", 15)
    tone = options.get("tone", "conversational")
    include_intro_outro = options.get("include_intro_outro", True)

    # Set the intro/outro text based on the option
    intro_outro_text = (
        "Include a brief introduction and conclusion"
        if include_intro_outro
        else "Skip introduction and conclusion"
    )

    # Load the system prompt template
    system_prompt_template = load_system_prompt_template()

    # Fill in the template with the specific values
    system_prompt = system_prompt_template.format(
        host_name=host_name,
        guest_name=guest_name,
        podcast_title=podcast_title,
        length_in_minutes=length_in_minutes,
        tone=tone,
        intro_outro_text=intro_outro_text,
        pdf_text=pdf_text,
    )

    # Call Claude API
    response = claude_client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": "Please convert this content to a podcast script according to the guidelines.",
            }
        ],
    )

    # Extract the generated script from Claude's response
    return response.content[0].text


@app.route("/api/pdf-to-podcast", methods=["POST"])
def convert_pdf_to_podcast():
    """API endpoint to convert PDF to podcast script"""
    try:
        # Check if a file was uploaded
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]

        # Check if file was actually selected
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Check if file is a PDF
        if not allowed_file(file.filename):
            return jsonify({"error": "File must be a PDF"}), 400

        # Save the uploaded file to a temporary location
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Extract options from request form
        options = {
            "host_name": request.form.get("host_name", "Host"),
            "guest_name": request.form.get("guest_name", "Guest"),
            "podcast_title": request.form.get("podcast_title", "PDF Discussion"),
            "length_in_minutes": int(request.form.get("length_in_minutes", 15)),
            "tone": request.form.get("tone", "conversational"),
            "include_intro_outro": request.form.get(
                "include_intro_outro", "true"
            ).lower()
            == "true",
        }

        # Extract text from PDF
        pdf_text = extract_text_from_pdf(file_path)

        # Generate podcast script using Claude
        script = generate_podcast_script(pdf_text, options)

        # Clean up the temporary file
        os.remove(file_path)

        # Return the generated script
        return jsonify({"success": True, "script": script}), 200

    except Exception as e:
        # Clean up any temporary files if they exist
        if "file_path" in locals() and os.path.exists(file_path):
            os.remove(file_path)

        return jsonify(
            {"error": "Failed to convert PDF to podcast script", "message": str(e)}
        ), 500


if __name__ == "__main__":
    # Ensure the system prompt template file exists
    if not os.path.exists(PROMPT_TEMPLATE_PATH):
        print(
            f"WARNING: System prompt template file not found at {PROMPT_TEMPLATE_PATH}"
        )
        print("Please create this file before running the application.")
        exit(1)

    # Start the application
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
