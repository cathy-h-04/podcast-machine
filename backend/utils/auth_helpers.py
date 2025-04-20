"""
Authentication Helper Functions
------------------------------
Utility functions for user authentication, including:
- User database operations
- Password hashing and verification
- JWT token generation and validation
"""

import os
import json
import uuid
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# Path to the JSON file serving as our user database
DB_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/users.json"
)

# Ensure the data directory exists
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

# Create the users.json file if it doesn't exist
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"users": []}, f)


def read_users():
    """Read user data from the JSON file."""
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is empty or doesn't exist, return an empty users list
        return {"users": []}


def write_users(data):
    """Write user data to the JSON file."""
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_user(name, email, password):
    """Create a new user with hashed password."""
    # Create new user with hashed password
    new_user = {
        "id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "created_at": datetime.now().isoformat(),
    }

    return new_user


def user_exists(email):
    """Check if a user with the given email exists."""
    users_data = read_users()
    return any(user["email"] == email for user in users_data["users"])


def get_user_by_email(email):
    """Get a user by email."""
    users_data = read_users()
    return next((user for user in users_data["users"] if user["email"] == email), None)


def get_user_by_id(user_id):
    """Get a user by ID."""
    users_data = read_users()
    return next((user for user in users_data["users"] if user["id"] == user_id), None)


def validate_user_credentials(email, password):
    """Validate user credentials and return the user if valid."""
    user = get_user_by_email(email)

    if not user or not check_password_hash(user["password"], password):
        return None

    return user


def generate_jwt_token(user):
    """Generate a JWT token for the user."""
    secret_key = os.getenv("JWT_SECRET_KEY")
    if not secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is required")

    expiration = datetime.now() + timedelta(days=1)  # Token expires in 1 day

    token_payload = {
        "user_id": user["id"],
        "email": user["email"],
        "exp": expiration.timestamp(),
    }

    return jwt.encode(token_payload, secret_key, algorithm="HS256")


def verify_jwt_token(token):
    """Verify a JWT token and return the user ID if valid."""
    try:
        secret_key = os.getenv("JWT_SECRET_KEY")
        if not secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is required")

        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
