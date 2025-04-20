"""
User Authentication Routes
-------------------------
Handles user registration and login functionality.
Uses helper functions from utils/auth_helpers.py for database operations and authentication.
"""

import os
import sys
from flask import request, jsonify
from utils.auth_helpers import (
    read_users,
    write_users,
    create_user,
    user_exists,
    validate_user_credentials,
    generate_jwt_token,
    verify_jwt_token,
)


# Add parent directory to sys.path to make the utils module accessible
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def register_route():
    """Handle user registration."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate required fields
    required_fields = ["name", "email", "password"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Check if email already exists
    if user_exists(data["email"]):
        return jsonify({"error": "Email already registered"}), 409

    # Create new user with helper function
    new_user = create_user(data["name"], data["email"], data["password"])

    # Add user to database
    users_data = read_users()
    users_data["users"].append(new_user)
    write_users(users_data)

    # Return success but don't include password in response
    user_response = {k: v for k, v in new_user.items() if k != "password"}
    return jsonify({"message": "Registration successful", "user": user_response}), 201


def login_route():
    """Handle user login."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate required fields
    if "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password are required"}), 400

    # Validate credentials
    user = validate_user_credentials(data["email"], data["password"])

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    # Generate JWT token
    token = generate_jwt_token(user)

    return jsonify(
        {
            "message": "Login successful",
            "token": token,
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
        }
    ), 200


def verify_token(token):
    """Verify a JWT token and return the user ID if valid."""
    return verify_jwt_token(token)


def logout_route():
    """Handle user logout."""
    # Since we're using JWT tokens that are stored client-side,
    # we don't need to do anything server-side for logout.
    # The client is responsible for removing the token.

    # However, we'll return a success response to confirm the logout action
    return jsonify({"message": "Logout successful"}), 200
