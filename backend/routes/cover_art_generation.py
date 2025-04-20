import os
import requests
import anthropic
import uuid
from flask import request, jsonify
from dotenv import load_dotenv

from routes.podcasts import update_podcast_cover

# Load environment variables
load_dotenv()

# Initialize Claude client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Hugging Face Token
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in environment variables")

# Hugging Face model URL
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"


def generate_cover_art():
    try:
        print("Starting cover art generation")
        data = request.get_json()
        print(f"Request data: {data}")
        podcast_id = data.get("podcast_id")
        script = data.get("script", "")
        prompt = data.get("prompt", "")
        
        print(f"podcast_id: {podcast_id}, prompt length: {len(prompt)}, script length: {len(script)}")
        
        # Step 1: Use provided prompt or generate one using Claude
        if prompt:
            visual_prompt = prompt
            print(f"Using provided prompt: {prompt[:100]}...")
        elif script:
            try:
                with open("image_prompt.txt") as f:
                    template = f.read()
                print("Successfully loaded template")
            except Exception as e:
                return jsonify({"error": f"Error loading template: {str(e)}"}), 500

            prompt_input = template.replace("{{SCRIPT_GOES_HERE}}", script[:3000])
            try:
                print("Calling Claude API")
                # Add a timestamp to ensure uniqueness in each prompt
                import time
                timestamp = int(time.time())
                
                # Enhanced system prompt to encourage variety
                system_prompt = (
                    "You are a visual artist prompt generator for AI models. "
                    "Create unique, varied, and visually distinct prompts for each request. "
                    "Avoid generic imagery and focus on specific, distinctive visual elements. "
                    "Incorporate unexpected color schemes and artistic styles to ensure variety."
                )
                
                response = claude_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=300,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": f"{prompt_input}\n\nTimestamp: {timestamp} - Please create a completely unique image description different from any you've created before."}
                    ],
                )
                visual_prompt = response.content[0].text.strip()
                print(f"Claude generated prompt: {visual_prompt[:100]}...")
            except Exception as e:
                return jsonify({"error": f"Error calling Claude API: {str(e)}"}), 500
        else:
            return jsonify({"error": "Either 'prompt' or 'script' is required"}), 400

        # Step 2: Call Hugging Face Inference API with the visual prompt
        try:
            print(f"Calling Hugging Face API with token: {HF_TOKEN[:5]}...")
            print(f"Visual prompt: {visual_prompt[:100]}...")
            print(f"API URL: {HF_API_URL}")
            
            # Print token details (safely)
            token_length = len(HF_TOKEN) if HF_TOKEN else 0
            print(f"Token length: {token_length}")
            print(f"Token first 5 chars: {HF_TOKEN[:5] if token_length >= 5 else 'N/A'}")
            print(f"Token last 5 chars: {HF_TOKEN[-5:] if token_length >= 5 else 'N/A'}")
            
            # Prepare headers and payload
            headers = {"Authorization": f"Bearer {HF_TOKEN}"}
            
            # Use consistent parameters without random seed
            payload = {
                "inputs": visual_prompt,
                "parameters": {
                    "guidance_scale": 7.5,  # Controls how closely the image follows the prompt
                    "num_inference_steps": 50  # More steps = higher quality but slower
                }
            }
            
            print(f"Request headers: {headers}")
            print(f"Request payload: {payload}")
            print(f"Request payload length: {len(str(payload))}")

            # Make the API call with detailed logging
            print("Sending request to Hugging Face...")
            hf_response = requests.post(
                HF_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            # Log detailed response information
            print(f"Hugging Face response status: {hf_response.status_code}")
            print(f"Response headers: {dict(hf_response.headers)}")
            
            # Try to parse response content
            try:
                if 'application/json' in hf_response.headers.get('Content-Type', ''):
                    print(f"Response JSON: {hf_response.json()}")
                else:
                    print(f"Response content type: {hf_response.headers.get('Content-Type', 'unknown')}")
                    print(f"Response content length: {len(hf_response.content)}")
            except Exception as e:
                print(f"Error parsing response: {str(e)}")
            
            if hf_response.status_code != 200:
                error_text = hf_response.text
                print(f"Error text: {error_text}")
                return jsonify({"error": "Hugging Face API error", "details": error_text}), 500

        except Exception as e:
            print(f"Error calling Hugging Face API: {str(e)}")
            return jsonify({"error": f"Error generating image: {str(e)}"}), 500

        # Step 3: Save the image
        try:
            filename = f"{uuid.uuid4().hex}.png"
            image_path = os.path.join("static", "covers", filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            with open(image_path, "wb") as f:
                f.write(hf_response.content)
            print(f"Saved cover image to {image_path}")

            cover_url = f"/static/covers/{filename}"

            # Step 4: Optionally update podcast
            if podcast_id:
                try:
                    print(f"Updating podcast {podcast_id} with cover URL")
                    updated_podcast = update_podcast_cover(podcast_id, cover_url)
                    return jsonify({
                        "success": True,
                        "cover_url": cover_url,
                        "podcast": updated_podcast
                    })
                except Exception as e:
                    print(f"Error updating podcast: {str(e)}")
                    # still return cover URL
            return jsonify({"success": True, "cover_url": cover_url})
        except Exception as e:
            return jsonify({"error": f"Error saving image: {str(e)}"}), 500

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
