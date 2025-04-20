# routes/script_generation.py
import os
import base64
import anthropic
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Style-specific default names
STYLE_DEFAULTS = {
    "podcast": {"host_name": "Host", "guest_name": "Guest"},
    "debate": {"host_name": "Debater A", "guest_name": "Debater B"},
    "duck": {"host_name": "Teacher", "guest_name": "Student"},
}

# Paths to the system prompt template files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PODCAST_PROMPT_PATH = os.path.join(BASE_DIR, "podcast_prompt.txt")
DEBATE_PROMPT_PATH = os.path.join(BASE_DIR, "debate_prompt.txt")
DUCK_PROMPT_PATH = os.path.join(BASE_DIR, "duck_prompt.txt")

# Initialize Claude client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


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


def get_default_settings(style, filename=None):
    """Get default settings for display in the response"""
    style_defaults = STYLE_DEFAULTS.get(style.lower(), STYLE_DEFAULTS["podcast"])

    # Create title from filename if available
    if filename:
        title = f"{filename} Discussion"
    else:
        title = "Podcast Discussion"

    return {
        "host_name": style_defaults["host_name"],
        "guest_name": style_defaults["guest_name"],
        "title": title,
        "length_in_minutes": 10,
        "tone": "conversational",
        "include_intro_outro": True,
    }


def generate_script(pdf_contents, style, user_message="", filename=None):
    """Generate a podcast, debate, or teaching script from PDFs using Claude's native PDF handling"""
    print("=== Starting generate_script ===")
    print("PDF contents:", pdf_contents)
    print("Style:", style)
    print("Filename:", filename)

    # Get default settings for the style (for including in the response)
    settings = get_default_settings(style, filename)

    # Load the appropriate prompt template
    system_prompt_template = load_prompt_template(style)

    # Add user preferences to the prompt
    if user_message:
        user_preferences = f"""
USER PREFERENCES:
{user_message}

Use the preferences above to determine host name, guest name, title, length, tone, and whether to include intro/outro.
If any preferences are not specified, use reasonable defaults.
"""
    else:
        user_preferences = "No specific preferences provided. Use default settings."

    # Prepare system prompt without PDF content (will be sent as attachments)
    system_prompt = system_prompt_template.format(
        host_name="{host_name}",
        guest_name="{guest_name}",
        title="{title}",
        length_in_minutes="{length_in_minutes}",
        tone="{tone}",
        intro_outro_text="{intro_outro_text}",
        pdf_text="[PDF content will be analyzed directly]",
        user_instructions=user_preferences,
    )

    # Extract file paths from pdf_contents
    pdf_files = []
    for i, pdf_content in enumerate(pdf_contents):
        print(f"Processing PDF {i + 1} for Claude API: {pdf_content['filename']}")
        try:
            # Check if the type is correct
            if pdf_content["type"] != "document":
                print(
                    f"Warning: PDF content type is {pdf_content['type']}, changing to 'document'"
                )
                pdf_content["type"] = "document"

            with open(pdf_content["path"], "rb") as f:
                file_data = f.read()
                print(f"Read {len(file_data)} bytes from {pdf_content['filename']}")

                pdf_files.append(
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": base64.b64encode(file_data).decode("utf-8"),
                        },
                    }
                )
        except Exception as e:
            print(f"Error processing PDF for Claude API: {str(e)}")
            import traceback

            print(traceback.format_exc())
            raise

    # Call Claude API with multimodal content
    response = claude_client.messages.create(
        model="claude-3-7-sonnet-20250219",  # use updated Claude 3.7 Sonnet model
        max_tokens=4000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze these PDFs and convert the content to a script according to my instructions.",
                    },
                    *pdf_files,
                ],
            }
        ],
    )

    # Extract the generated script
    generated_script = response.content[0].text

    # Make a separate Claude API call to generate a title
    title_prompt = f"""
You are an expert podcast title generator. Your task is to create a catchy, engaging title for a podcast episode based on the script I will provide.

The title should:
- Be concise (30-60 characters)
- Be engaging and draw the listener in
- Accurately reflect the main topic of the conversation
- Be suitable for a podcast episode
- Avoid clickbait or sensationalism

Script:
{generated_script[:2000]}  # Send first 2000 characters of script for context

Generate only the title as your response, with no additional commentary or explanations.
"""

    title_response = claude_client.messages.create(
        model="claude-3-5-sonnet-20240620",  # Can use a smaller model for title generation
        max_tokens=100,
        messages=[{"role": "user", "content": title_prompt}],
    )

    # Extract the generated title
    generated_title = title_response.content[0].text.strip()
    print(f"Generated title: {generated_title}")

    # Update settings with the generated title
    settings["title"] = generated_title

    # Determine output filename
    if filename:
        output_filename = f"{filename}.txt"
    else:
        output_filename = "output.txt"

    # Log how many PDFs were processed
    print(f"Processed {len(pdf_files)} PDFs for script generation")

    # Log script to file
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(generated_script)

    # Also print to console
    print(f"Generated script written to {output_filename}")

    return generated_script, settings


def extract_settings_from_script(script, filename=None):
    """Extract settings from a generated script"""
    settings = {}

    # Set a default title based on filename if available
    if filename:
        settings["title"] = filename
    else:
        settings["title"] = "Untitled Podcast"

    # Try to extract a better title from the script
    lines = script.split("\n")

    # First look for a title in the standard format (first 10 lines)
    for line in lines[:10]:  # Check first 10 lines for a title
        if line.strip().startswith("#") or line.strip().startswith("Title:"):
            # Found a title line
            title = line.strip().replace("#", "").replace("Title:", "").strip()
            if title:  # If title is not empty
                settings["title"] = title
                break

    # Search for Clause 3.5 in the entire script
    clause_3_5_title = None
    clause_pattern = r"(?i)Clause\s+3\.5\s*[:-]?\s*(.*?)(?:\n|$)"

    # Search through all lines for Clause 3.5
    for i, line in enumerate(lines):
        if "Clause 3.5" in line or "clause 3.5" in line:
            # Found a reference to Clause 3.5
            # Try to extract the title from this line
            match = re.search(clause_pattern, line)
            if match and match.group(1).strip():
                clause_3_5_title = match.group(1).strip()
            else:
                # If title not on same line, check next line for potential title
                if (
                    i + 1 < len(lines)
                    and lines[i + 1].strip()
                    and not lines[i + 1].strip().startswith("Clause")
                ):
                    clause_3_5_title = lines[i + 1].strip()
            break

    # If found a title in Clause 3.5, use it
    if clause_3_5_title:
        settings["title"] = clause_3_5_title

    # Extract other potential settings
    settings["host_name"] = "Host"
    settings["guest_name"] = "Guest"

    # Look for host/guest names in the script
    for line in lines[:30]:  # Check first 30 lines
        if ":" in line:
            speaker = line.split(":", 1)[0].strip()
            if (
                speaker
                and speaker != settings["host_name"]
                and speaker != settings["guest_name"]
            ):
                if settings["host_name"] == "Host":
                    settings["host_name"] = speaker
                elif settings["guest_name"] == "Guest":
                    settings["guest_name"] = speaker

    return settings
