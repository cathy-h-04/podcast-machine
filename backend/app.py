#!/usr/bin/env python3
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
import re
import anthropic
import PyPDF2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure upload settings
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {"pdf"}
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB limit (for multiple PDFs)

# Paths to the system prompt template files
PODCAST_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "podcast_prompt.txt"
)
DEBATE_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "debate_prompt.txt"
)
DUCK_PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "duck_prompt.txt"
)

# Default settings
DEFAULT_HOST_NAME = "Host"
DEFAULT_GUEST_NAME = "Guest"
DEFAULT_PODCAST_TITLE = "PDF Discussion"
DEFAULT_LENGTH_MINUTES = 15
DEFAULT_TONE = "conversational"
DEFAULT_INCLUDE_INTRO_OUTRO = True

# Style-specific default names
STYLE_DEFAULTS = {
    "podcast": {"host_name": "Host", "guest_name": "Guest"},
    "debate": {"host_name": "Debater A", "guest_name": "Debater B"},
    "duck": {"host_name": "Teacher", "guest_name": "Student"},
}

# Initialize Claude client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_prompt_template(style="podcast"):
    """Load the appropriate system prompt template based on style"""
    try:
        if style.lower() == "debate":
            prompt_path = DEBATE_PROMPT_PATH
        elif style.lower() == "duck":
            prompt_path = DUCK_PROMPT_PATH
        else:  # Default to podcast
            prompt_path = PODCAST_PROMPT_PATH

        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"System prompt template file not found at {prompt_path}"
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


def extract_user_preferences(user_message, style="podcast"):
    """
    Extract user preferences for the audio script from the message.
    Returns a dictionary with the extracted settings or default values.
    """
    # Use style-specific defaults for host and guest names
    style_defaults = STYLE_DEFAULTS.get(style.lower(), STYLE_DEFAULTS["podcast"])

    settings = {
        "host_name": style_defaults["host_name"],
        "guest_name": style_defaults["guest_name"],
        "title": DEFAULT_PODCAST_TITLE,
        "length_in_minutes": DEFAULT_LENGTH_MINUTES,
        "tone": DEFAULT_TONE,
        "include_intro_outro": DEFAULT_INCLUDE_INTRO_OUTRO,
    }

    # Skip processing if no message provided
    if not user_message:
        return settings

    # Extract host name
    host_patterns = [
        r'host(?:\s+name)?(?:\s+(?:is|should be|to be|as))?\s+["\']?([A-Za-z\s]+)["\']?',
        r'["\']?([A-Za-z\s]+)["\']?\s+(?:as|is|should be|to be)\s+(?:the)?\s*host',
    ]

    for pattern in host_patterns:
        host_match = re.search(pattern, user_message, re.IGNORECASE)
        if host_match:
            settings["host_name"] = host_match.group(1).strip()
            break

    # Extract guest name
    guest_patterns = [
        r'guest(?:\s+name)?(?:\s+(?:is|should be|to be|as))?\s+["\']?([A-Za-z\s]+)["\']?',
        r'["\']?([A-Za-z\s]+)["\']?\s+(?:as|is|should be|to be)\s+(?:the)?\s*guest',
    ]

    for pattern in guest_patterns:
        guest_match = re.search(pattern, user_message, re.IGNORECASE)
        if guest_match:
            settings["guest_name"] = guest_match.group(1).strip()
            break

    # Extract title
    title_patterns = [
        r'(?:podcast|show|debate|discussion|title)(?:\s+title)?(?:\s+(?:is|should be|to be|as))?\s+["\']([^"\']+)["\']',
        r'title(?:\s+(?:is|should be|to be|as))?\s+["\']([^"\']+)["\']',
        r'call(?:\s+(?:the podcast|the show|the debate|it))?\s+["\']([^"\']+)["\']',
        r'name(?:\s+(?:the podcast|the show|the debate|it))?\s+["\']([^"\']+)["\']',
    ]

    for pattern in title_patterns:
        title_match = re.search(pattern, user_message, re.IGNORECASE)
        if title_match:
            settings["title"] = title_match.group(1).strip()
            break

    # Extract length
    length_match = re.search(r"(\d+)(?:\s*|-)?minute", user_message, re.IGNORECASE)
    if length_match:
        try:
            settings["length_in_minutes"] = int(length_match.group(1))
        except ValueError:
            pass  # Keep default if conversion fails

    # Extract tone
    tone_patterns = [
        r"tone(?:\s+(?:is|should be|to be|as))?\s+([a-zA-Z]+)",
        r"([a-zA-Z]+)\s+tone",
    ]

    for pattern in tone_patterns:
        tone_match = re.search(pattern, user_message, re.IGNORECASE)
        if tone_match:
            tone = tone_match.group(1).lower()
            # Verify the tone is reasonable, otherwise keep default
            valid_tones = [
                "conversational",
                "casual",
                "formal",
                "professional",
                "friendly",
                "humorous",
                "serious",
                "educational",
                "intense",
                "respectful",
                "energetic",
                "enthusiastic",
                "calm",
                "passionate",
            ]
            if tone in valid_tones:
                settings["tone"] = tone
            break

    # Check for intro/outro preference
    if re.search(
        r"no\s+intro|skip\s+intro|without\s+intro", user_message, re.IGNORECASE
    ):
        settings["include_intro_outro"] = False
    elif re.search(r"with\s+intro|include\s+intro", user_message, re.IGNORECASE):
        settings["include_intro_outro"] = True

    return settings


def check_content_suitability(pdf_texts):
    """
    Check if the PDF content is suitable for script generation.
    Returns (is_suitable, reason) tuple.
    """
    # Combine all text for overall checks
    combined_text = " ".join(pdf_texts)

    # Check if there's enough content
    min_length = 200  # Characters
    if len(combined_text.strip()) < min_length:
        return False, "Insufficient content in the uploaded PDF(s)"

    # Check if the content appears to be meaningful text
    # (e.g., not just numbers or formatting characters)
    if len(re.findall(r"\w+", combined_text)) < 50:  # At least 50 words
        return False, "Uploaded PDF(s) don't contain enough text content"

    # All checks passed
    return True, "Content is suitable"


def generate_script(pdf_texts, settings, style, user_message=""):
    """Generate a podcast, debate, or teaching script from PDF texts using Claude"""
    # Combine PDF texts (with markers to separate different PDFs)
    combined_text = ""
    for i, text in enumerate(pdf_texts):
        if i > 0:
            combined_text += "\n\n--- NEW DOCUMENT ---\n\n"
        combined_text += text

    # Set the intro/outro text based on the option
    intro_outro_text = (
        "Include a brief introduction and conclusion"
        if settings["include_intro_outro"]
        else "Skip introduction and conclusion"
    )

    # Load the appropriate prompt template
    system_prompt_template = load_prompt_template(style)

    # Fill in the template with the specific values
    system_prompt = system_prompt_template.format(
        host_name=settings["host_name"],
        guest_name=settings["guest_name"],
        title=settings["title"],
        length_in_minutes=settings["length_in_minutes"],
        tone=settings["tone"],
        intro_outro_text=intro_outro_text,
        pdf_text=combined_text,
        user_instructions=user_message,
    )

    # Call Claude API
    response = claude_client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=4000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": "Please convert this content to a script according to my instructions.",
            }
        ],
    )

    # Extract the generated script from Claude's response
    return response.content[0].text


@app.route("/generate", methods=["POST"])
def convert_pdf_to_script():
    """API endpoint to convert PDF(s) to podcast, debate, or teaching script based on user preferences"""
    try:
        # Check if mode is 'summaritive' - only process this mode
        mode = request.form.get("mode", "").lower()
        if mode != "summaritive":
            return jsonify(
                {"error": "This endpoint only processes 'summaritive' mode requests"}
            ), 400

        # Check if any files were uploaded
        if "files" not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        # Get all uploaded files
        files = request.files.getlist("files")

        # Check if any files were actually selected
        if not files or files[0].filename == "":
            return jsonify({"error": "No files selected"}), 400

        # Check if all files are PDFs
        if not all(allowed_file(file.filename) for file in files):
            return jsonify({"error": "All files must be PDFs"}), 400

        # Get user message and style
        user_message = request.form.get("context", "")
        style = request.form.get("style", "podcast").lower()

        # Validate style
        if style not in ["podcast", "debate", "duck"]:
            return jsonify(
                {"error": "Invalid style. Must be 'podcast', 'debate', or 'duck'"}
            ), 400

        # Extract user preferences from message
        settings = extract_user_preferences(user_message, style)

        # Save uploaded files to temporary locations and process them
        pdf_texts = []
        temp_files = []

        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            temp_files.append(file_path)

            # Extract text from PDF
            pdf_text = extract_text_from_pdf(file_path)
            pdf_texts.append(pdf_text)

        # Check if content is suitable
        is_suitable, reason = check_content_suitability(pdf_texts)
        if not is_suitable:
            # Clean up temporary files
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.remove(file_path)

            return jsonify({"error": "Content unsuitable", "message": reason}), 400

        # Generate script using Claude
        script = generate_script(pdf_texts, settings, style, user_message)

        # Clean up the temporary files
        for file_path in temp_files:
            if os.path.exists(file_path):
                os.remove(file_path)

        # Return the generated script and the settings that were used
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
            for file_path in temp_files:
                if os.path.exists(file_path):
                    os.remove(file_path)

        return jsonify(
            {"error": "Failed to convert PDF to script", "message": str(e)}
        ), 500


if __name__ == "__main__":
    # Ensure the system prompt template files exist
    for prompt_path in [PODCAST_PROMPT_PATH, DEBATE_PROMPT_PATH, DUCK_PROMPT_PATH]:
        if not os.path.exists(prompt_path):
            filename = os.path.basename(prompt_path)
            print(f"WARNING: System prompt template file not found at {prompt_path}")
            print(f"Please create the {filename} file before running the application.")
            exit(1)

    # Start the application
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
