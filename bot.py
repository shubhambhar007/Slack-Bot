import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter
import threading
import time
 
app = Flask(__name__)
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'], '/slack/events', app)
 
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']
 
# Define a variable to keep track of the stop message
STOP_MESSAGE = "stop"  # You can change this to your desired stop message
 
# Dictionary to keep track of thread timestamps and user IDs
thread_timestamps = {}
 
# Dictionary to store user IDs from workflow messages
workflow_user_ids = {}
 
client.chat_postMessage(channel='#fa-spectra-support', text="hello world")
# Function to send a reminder message
def send_reminder(channel_id, thread_ts, user_id):
    time.sleep(5)  # 5 minutes delay
    if user_id != BOT_ID:
        client.chat_postMessage(channel=channel_id, text=f"<@{user_id}> It's been 5 minutes. Do you want to continue or close this conversation?", thread_ts=thread_ts)
 
# Function to handle messages
@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    thread_ts = event.get('ts')
 
    # Check if the message is from a workflow
    if 'username' in event and event['username'] == 'Report an Incident':
        # This is a message from a workflow, handle it differently
        handle_workflow_message(channel_id, user_id, text, thread_ts)
    elif BOT_ID != user_id:
        # This is a regular message, handle it as described below
 
        # Send the reminder message if the thread is not already being tracked
        if thread_ts not in thread_timestamps:
            thread_timestamps[thread_ts] = user_id
            reminder_thread = threading.Thread(target=send_reminder, args=(channel_id, thread_ts, user_id))
            reminder_thread.start()
 
# Function to handle messages from workflows
def handle_workflow_message(channel_id, user_id, text, thread_ts):
    # Extract user ID from the workflow-generated message
    lines = text.split('\n')
    workflow_user_id = lines[-1][2:-1]
 
    # Store the user ID in the dictionary
    workflow_user_ids[thread_ts] = workflow_user_id
    #POST METHOD TO PUSH 
    client.chat_postMessage(channel=channel_id, text=f"<@{workflow_user_id}> Your issue is now in queue, an analyst will look at it soon.Thanks", thread_ts=thread_ts)
 
    # Handle the workflow-generated message differently
    # Implement your custom logic for workflow messages here
    pass
 
@slack_event_adapter.on('reaction_added')
def reaction_added(payload):
    event = payload.get('event', {})
    reaction = event.get('reaction')
    item_user = event.get('item_user')
    item = event.get('item')
    print(reaction)
 
    # Check if the reaction is a white check mark and if the item is a message
 
    if reaction == 'white_check_mark' :
        channel_id = item.get('channel')
        thread_ts = item.get('ts')
 
        # Reply with a thank you and close the conversation
        client.chat_postMessage(channel=channel_id, text="Thank you for resolving this issue. The conversation is now closed.", thread_ts=thread_ts)
 
 
if __name__ == "__main__":
    app.run(debug=True, port=8000)
