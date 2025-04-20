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
        
        # Extract title and format from podcast_id if available
        title = "Podcast"
        format = "podcast"
        
        if podcast_id:
            try:
                from routes.podcasts import _load_podcasts
                podcasts = _load_podcasts()
                podcast = next((p for p in podcasts if p["id"] == podcast_id), None)
                if podcast:
                    title = podcast.get("title", "Podcast")
                    format = podcast.get("format", "podcast")
            except Exception as e:
                print(f"Error getting podcast details: {str(e)}")
        
        # Step 1: Generate SVG cover art using Claude with artifacts tool
        try:
            print("Using Claude with artifacts tool for SVG generation")
            
            # Prepare the user message
            user_message = f"Create an SVG podcast cover art for a {format} about \"{title}\""
            
            if script:
                # Add script excerpt if available (limited to 1000 chars to avoid token limits)
                user_message += f"\n\nHere's an excerpt from the podcast script:\n\n{script[:1000]}"
            elif prompt:
                # Add the prompt if provided
                user_message += f"\n\nUse this description: {prompt}"
            
            print(f"User message: {user_message[:100]}...")
            
            # Call Claude with the artifacts tool
            response = claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                messages=[{
                    "role": "user", 
                    "content": user_message
                }],
                tools=[
                    {
                        "name": "artifacts",
                        "description": "Create SVG cover art for podcasts",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "command": {"type": "string"},
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["command", "id", "type", "content"]
                        }
                    }
                ]
            )
            
            # Extract the SVG content from the response
            svg_content = None
            tool_use_info = ""
            
            for content in response.content:
                if hasattr(content, 'tool_use') and content.tool_use.name == 'artifacts':
                    tool_use_info += f"Tool used: {content.tool_use.name}\n"
                    if content.tool_use.input.get('type') == 'svg':
                        svg_content = content.tool_use.input.get('content')
                        tool_use_info += f"SVG ID: {content.tool_use.input.get('id')}\n"
                        print(f"Found SVG content of length: {len(svg_content) if svg_content else 0}")
            
            if tool_use_info:
                print(f"Tool use information:\n{tool_use_info}")
            
            if not svg_content:
                print("No SVG content found in Claude response, falling back to text response")
                # If no SVG was generated, use Claude's text response as a prompt for Hugging Face
                visual_prompt = response.content[0].text.strip()
                print(f"Using Claude text response as fallback: {visual_prompt[:100]}...")
                
                # Continue with Hugging Face API as fallback
                return generate_image_with_huggingface(visual_prompt, podcast_id)
            
            # Save the SVG content
            filename = f"{uuid.uuid4().hex}.svg"
            image_path = os.path.join("static", "covers", filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            
            with open(image_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
            
            print(f"Saved SVG cover image to {image_path}")
            cover_url = f"/static/covers/{filename}"
            
            # Update podcast if ID was provided
            if podcast_id:
                try:
                    print(f"Updating podcast {podcast_id} with cover URL")
                    updated_podcast = update_podcast_cover(podcast_id, cover_url)
                    return jsonify({
                        "success": True,
                        "cover_url": cover_url,
                        "podcast": updated_podcast,
                        "type": "svg"
                    })
                except Exception as e:
                    print(f"Error updating podcast: {str(e)}")
            
            return jsonify({"success": True, "cover_url": cover_url, "type": "svg"})
            
        except Exception as e:
            print(f"Error using Claude with artifacts tool: {str(e)}")
            print("Falling back to Hugging Face image generation")
            
            # Generate a prompt from the script or use the provided prompt
            if prompt:
                visual_prompt = prompt
            elif script:
                try:
                    # Generate a prompt using Claude
                    with open("image_prompt.txt") as f:
                        template = f.read()
                    
                    prompt_input = template.replace("{{SCRIPT_GOES_HERE}}", script[:3000])
                    response = claude_client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=300,
                        system="You are a visual artist prompt generator for AI models.",
                        messages=[{"role": "user", "content": prompt_input}],
                    )
                    visual_prompt = response.content[0].text.strip()
                except Exception as prompt_error:
                    print(f"Error generating prompt: {str(prompt_error)}")
                    visual_prompt = f"Podcast cover art for '{title}' in {format} style"
            else:
                return jsonify({"error": "Either 'prompt' or 'script' is required"}), 400
            
            # Call Hugging Face as fallback
            return generate_image_with_huggingface(visual_prompt, podcast_id)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


def generate_image_with_huggingface(visual_prompt, podcast_id=None):
    """Generate an image using Hugging Face API as a fallback"""
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

        # Step 3: Save the image
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
                    "podcast": updated_podcast,
                    "type": "png"
                })
            except Exception as e:
                print(f"Error updating podcast: {str(e)}")
                # still return cover URL
        return jsonify({"success": True, "cover_url": cover_url, "type": "png"})
    except Exception as e:
        print(f"Error calling Hugging Face API: {str(e)}")
        return jsonify({"error": f"Error generating image: {str(e)}"}), 500
