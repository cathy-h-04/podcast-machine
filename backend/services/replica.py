import os
import requests
from dotenv import load_dotenv


class replicaClient:
    def __init__(self):

        self.API_KEY = os.getenv('api_key')
        self.REPLICA_ID = os.getenv('replica_id')
        if not self.API_KEY or not self.REPLICA_ID:
            raise ValueError("API credentials not found in environment variables")
        
        self.headers = headers = {
                "x-api-key": self.API_KEY,
                "Content-Type": "application/json"
            }

    def start_conversation(self, podcast_context):
        '''
        Starts a live conversation with a replica using the Tarus API
        '''

        url = "https://tavusapi.com/v2/conversations"

        custom_greeting = "Hey how's it going? I hope you enjoyed the podcast. I am here to help you reflect on what you learned and clarify any questions you might have. Let's dive in! Can you start with a quick summary of what you learned?"

        context = "You're about to speak with a student who has just finished listening to a podcast designed to explain a concept for which they uploaded resources for. Your role is to encourage the student to articulate their understanding of the concept, reflect on how much they grasped, and identify any areas of confusion. The goal is to guide the student toward greater self-awareness of their knowledge gaps and help them formulate thoughtful follow-up questions. Here is the script / planning that went into the exact podcast the student listened to:" + podcast_context
        
        payload = {
            "replica_id": self.REPLICA_ID,
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

        response = requests.request("POST", url, json=payload, headers=self.headers)

        data = response.json()
        conversation_id = data['conversation_id']
        conversation_url = data['conversation_url']

        print(conversation_url)


    def get_conversation(self, conversation_id):

        url = f"https://tavusapi.com/v2/conversations/{conversation_id}"
        response = requests.request("GET", url, headers=self.headers)

        print(response.text)

    def list_conversations(self):
        url = "https://tavusapi.com/v2/conversations"

        response = requests.request("GET", url, headers=self.headers)

        print(response.text)
        return response.text

    def end_conversation(self, conversation_id):
        url = f"https://tavusapi.com/v2/conversations/{conversation_id}/end"

        response = requests.request("POST", url, headers=self.headers)

        print(response.text)

    def delete_conversation(self, conversation_id):
        url = f"https://tavusapi.com/v2/conversations/{conversation_id}"

        response = requests.request("DELETE", url, headers=self.headers)

        print(response.text)


if __name__ == "__main__":
    load_dotenv()

    with open("../output.txt", "r") as file:
        podcast_context = file.read()

    client = replicaClient()
    client.start_conversation(podcast_context)






