"""
User Prompts Routes
------------------
Handles the storage and retrieval of user-specific prompts.
These prompts are used to store user preferences that should be remembered by Claude.
"""

import os
import json
import uuid
from datetime import datetime
from flask import request, jsonify, g
import functools
from utils.auth_helpers import verify_jwt_token

# Path to the prompts database file
PROMPTS_DB_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../data/prompts.json"
)

# Ensure the data directory exists
os.makedirs(os.path.dirname(PROMPTS_DB_FILE), exist_ok=True)

# Create the prompts.json file if it doesn't exist
if not os.path.exists(PROMPTS_DB_FILE):
    with open(PROMPTS_DB_FILE, "w") as f:
        json.dump({"prompts": []}, f)


def read_prompts():
    """Read prompt data from the JSON file."""
    try:
        with open(PROMPTS_DB_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is empty or doesn't exist, return an empty prompts list
        return {"prompts": []}


def write_prompts(data):
    """Write prompt data to the JSON file."""
    with open(PROMPTS_DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_user_prompts(user_id):
    """Get all prompts for a specific user."""
    data = read_prompts()
    return [p for p in data["prompts"] if p.get("user_id") == user_id]


def find_prompt_by_id(prompt_id, user_id):
    """Find a prompt by ID for a specific user."""
    prompts_data = read_prompts()
    for i, prompt in enumerate(prompts_data["prompts"]):
        if prompt.get("id") == prompt_id and prompt.get("user_id") == user_id:
            return i, prompt
    return None, None


def token_required(f):
    """Decorator to require a valid JWT token for authentication."""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check if token is in the headers
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        # Use auth helper to verify token
        user_id = verify_jwt_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Store the user ID in the global context
        g.user_id = user_id

        return f(*args, **kwargs)

    return decorated


def get_prompts_route():
    """Get all prompts for the currently authenticated user."""

    @token_required
    def handle():
        user_id = g.user_id

        # Get prompts for current user using the helper function
        user_prompts = get_user_prompts(user_id)

        return jsonify({"prompts": user_prompts})

    return handle()


def create_prompt_route():
    """Create a new prompt for the currently authenticated user."""

    @token_required
    def handle():
        user_id = g.user_id

        # Get the request data
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        title = data.get("title")
        content = data.get("content")

        if not title or not content:
            return jsonify({"error": "Title and content are required"}), 400

        # Create new prompt object
        new_prompt = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "content": content,
            "createdAt": datetime.now().isoformat(),
        }

        # Read existing prompts
        prompts_data = read_prompts()

        # Add to prompts list
        prompts_data["prompts"].append(new_prompt)

        # Save updated prompts data
        write_prompts(prompts_data)

        return jsonify(
            {"message": "Prompt created successfully", "prompt": new_prompt}
        ), 201

    return handle()


def update_prompt_route(prompt_id):
    """Update an existing prompt for the currently authenticated user."""

    @token_required
    def handle():
        user_id = g.user_id

        # Get the request data
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        title = data.get("title")
        content = data.get("content")

        if not title or not content:
            return jsonify({"error": "Title and content are required"}), 400

        # Read existing prompts
        prompts_data = read_prompts()

        # Find the prompt to update using helper function
        index, prompt = find_prompt_by_id(prompt_id, user_id)

        if not prompt:
            return jsonify({"error": "Prompt not found or unauthorized"}), 404

        # Update prompt
        prompts_data["prompts"][index]["title"] = title
        prompts_data["prompts"][index]["content"] = content
        updated_prompt = prompts_data["prompts"][index]

        # Save updated prompts data
        write_prompts(prompts_data)

        return jsonify(
            {"message": "Prompt updated successfully", "prompt": updated_prompt}
        )

    return handle()


def delete_prompt_route(prompt_id):
    """Delete a prompt for the currently authenticated user."""

    @token_required
    def handle():
        user_id = g.user_id

        # Read existing prompts
        prompts_data = read_prompts()

        # Find the prompt to delete using helper function
        index, prompt = find_prompt_by_id(prompt_id, user_id)

        if not prompt:
            return jsonify({"error": "Prompt not found or unauthorized"}), 404

        # Remove the prompt
        prompts_data["prompts"].pop(index)

        # Save updated prompts data
        write_prompts(prompts_data)

        return jsonify({"message": "Prompt deleted successfully"})

    return handle()
