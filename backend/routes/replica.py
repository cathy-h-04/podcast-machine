# routes/replica.py
import os
import json
import uuid
from flask import jsonify, request, abort
from services.replica import replicaClient


def start_conversation_route():
    """
    Route handler to start a new conversation with a replica
    """
    try:
        # Get podcast context from request
        data = request.get_json()
        podcast_id = data.get("podcast_id")

        if not podcast_id:
            return jsonify({"error": "Podcast ID is required"}), 400

        # Load the podcast data to get context
        from routes.podcasts import _load_podcasts

        podcasts = _load_podcasts()
        podcast = next((p for p in podcasts if p.get("id") == podcast_id), None)

        if not podcast:
            return jsonify({"error": "Podcast not found"}), 404

        # Get the podcast script/context
        podcast_context = podcast.get("script", "")

        # Initialize replica client
        client = replicaClient()

        # Start conversation
        result = client.start_conversation(podcast_context)

        # Return the conversation details
        return jsonify(
            {
                "success": True,
                "conversation_id": result.get("conversation_id"),
                "conversation_url": result.get("conversation_url"),
            }
        )
    except Exception as e:
        print(f"Error starting conversation: {str(e)}")
        return jsonify({"error": str(e)}), 500


def get_conversation_route(conversation_id):
    """
    Route handler to get conversation details
    """
    try:
        # Initialize replica client
        client = replicaClient()

        # Get conversation details
        result = client.get_conversation(conversation_id)

        return jsonify({"success": True, "conversation": result})
    except Exception as e:
        print(f"Error getting conversation: {str(e)}")
        return jsonify({"error": str(e)}), 500


def list_conversations_route():
    """
    Route handler to list all conversations
    """
    try:
        # Initialize replica client
        client = replicaClient()

        # List conversations
        result = client.list_conversations()

        return jsonify({"success": True, "conversations": result})
    except Exception as e:
        print(f"Error listing conversations: {str(e)}")
        return jsonify({"error": str(e)}), 500


def end_conversation_route(conversation_id):
    """
    Route handler to end a conversation
    """
    try:
        # Initialize replica client
        client = replicaClient()

        # End conversation
        result = client.end_conversation(conversation_id)

        return jsonify({"success": True, "result": result})
    except Exception as e:
        print(f"Error ending conversation: {str(e)}")
        return jsonify({"error": str(e)}), 500


def delete_conversation_route(conversation_id):
    """
    Route handler to delete a conversation
    """
    try:
        # Initialize replica client
        client = replicaClient()

        # Delete conversation
        result = client.delete_conversation(conversation_id)

        return jsonify({"success": True, "result": result})
    except Exception as e:
        print(f"Error deleting conversation: {str(e)}")
        return jsonify({"error": str(e)}), 500
