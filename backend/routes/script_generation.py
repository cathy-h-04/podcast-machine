# routes/script_generation.py
import os
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Style-specific default names
STYLE_DEFAULTS = {
    "podcast": {
        "host_name": "Host",
        "guest_name": "Guest"
    },
    "debate": {
        "host_name": "Debater A",
        "guest_name": "Debater B"
    },
    "duck": {
        "host_name": "Teacher",
        "guest_name": "Student"
    }
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
        
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"System prompt template file not found at {prompt_path}")
    except Exception as e:
        raise Exception(f"Error loading system prompt template: {str(e)}")

def get_default_settings(style):
    """Get default settings for display in the response"""
    style_defaults = STYLE_DEFAULTS.get(style.lower(), STYLE_DEFAULTS["podcast"])
    
    return {
        "host_name": style_defaults["host_name"],
        "guest_name": style_defaults["guest_name"],
        "title": "PDF Discussion",
        "length_in_minutes": 15,
        "tone": "conversational",
        "include_intro_outro": True
    }

def generate_script(pdf_texts, style, user_message=""):
    """Generate a podcast, debate, or teaching script from PDF texts using Claude"""
    # Get default settings for the style (for including in the response)
    settings = get_default_settings(style)
    
    # Combine PDF texts (with markers to separate different PDFs)
    combined_text = ""
    for i, text in enumerate(pdf_texts):
        if i > 0:
            combined_text += "\n\n--- NEW DOCUMENT ---\n\n"
        combined_text += text
    
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
    
    # Fill in the template
    system_prompt = system_prompt_template.format(
        host_name="{host_name}",
        guest_name="{guest_name}",
        title="{title}",
        length_in_minutes="{length_in_minutes}",
        tone="{tone}",
        intro_outro_text="{intro_outro_text}",
        pdf_text=combined_text,
        user_instructions=user_preferences
    )

    # Call Claude API
    response = claude_client.messages.create(
        model="claude-3-7-sonnet-20250219",  # use updated Claude 3.7 Sonnet model
        max_tokens=4000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": "Please convert this content to a script according to my instructions."
            }
        ],
    )

    # Extract the generated script
    generated_script = response.content[0].text

    # Log script to file
    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(generated_script)

    # Also print to console
    print("Generated script written to output.txt")

    return generated_script, settings
