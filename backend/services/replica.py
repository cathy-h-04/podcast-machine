import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('api_key')
REPLICA_ID = os.getenv('replica_id')


#TODO: create custom greetings and context depending on the application input. 

custom_greeting = "Hello Hannah, let's talk about Model Predictive Control. Can you give me a short summary of the topic? "

context = "You're about to speak with a student who has just finished listening to a podcast designed to explain the concept of model predictive control in a unique and concise way. Your role is to encourage the student to articulate their understanding of the concept, reflect on how much they grasped, and identify any areas of confusion. The goal is to guide the student toward greater self-awareness of their knowledge gaps and help them formulate thoughtful follow-up questions. The podcast they listened to was delivered in a student-teacher format, meaning it followed an approach where the podcast had two people, one playing the role of a student asking questions about the topic and the other playing the role of the teacher answering the questions and trying to explain the concepts well. "


url = "https://tavusapi.com/v2/conversations"

payload = {
    "replica_id": REPLICA_ID,
    "conversation_name": "rubber ducky",
    "custom_greeting": custom_greeting,
    "conversational_context": context,
    "properties": {
        "enable_recording": False,
        "enable_closed_captions": False,
        "apply_greenscreen": False,
        "language": "english",
    }
}

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)


