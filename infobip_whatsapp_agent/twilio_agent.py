import os
import requests
import mimetypes
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

app = Flask(__name__)

# Twilio Credentials (Use environment variables for security)
ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "YOUR_ACCOUNT_SID_HERE")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "YOUR_AUTH_TOKEN_HERE")

# Initialize Twilio Client
client = Client(ACCOUNT_SID, AUTH_TOKEN)
TWILIO_NUMBER = 'whatsapp:+14155238886'

DOWNLOAD_DIR = "downloads_twilio"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/twilio_webhook', methods=['POST'])
def bot():
    """Handle incoming Twilio WhatsApp messages."""
    # Get message details
    sender = request.values.get('From', '').replace('whatsapp:', '')
    message_sid = request.values.get('MessageSid', '')
    num_media = int(request.values.get('NumMedia', 0))

    print(f"Received message from {sender} with {num_media} media files.")

    # Process media
    if num_media > 0:
        for i in range(num_media):
            media_url = request.values.get(f'MediaUrl{i}')
            content_type = request.values.get(f'MediaContentType{i}')
            
            if media_url:
                print(f"Downloading media: {media_url}")
                extension = mimetypes.guess_extension(content_type) or ".bin"
                filename = f"{sender}_{message_sid}_{i}{extension}"
                filepath = os.path.join(DOWNLOAD_DIR, filename)

                try:
                    # Twilio requires Basic Auth (Account SID + Auth Token) for media
                    response = requests.get(media_url, auth=(ACCOUNT_SID, AUTH_TOKEN), stream=True)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"✅ Saved: {filepath}")
                    else:
                        print(f"❌ Failed to download: {response.status_code}")
                except Exception as e:
                    print(f"Error downloading: {e}")
    else:
        print(f"Message body: {request.values.get('Body')}")

    resp = MessagingResponse()
    resp.message("File received!" if num_media > 0 else "Message received! Send me a file.")
    return str(resp)

@app.route('/invite', methods=['GET'])
def send_invite():
    """Endpoint to trigger an 'upload your cv' invite message."""
    target_number = request.args.get('to')
    if not target_number:
        return jsonify({"error": "Missing 'to' parameter (e.g. ?to=33756941611)"}), 400
    
    # Ensure whatsapp: prefix
    if not target_number.startswith('whatsapp:'):
        target_number = f'whatsapp:+{target_number.lstrip("+")}'

    try:
        message = client.messages.create(
            from_=TWILIO_NUMBER,
            body='upload your cv',
            to=target_number
        )
        return jsonify({
            "status": "success",
            "message_sid": message.sid,
            "info": f"Invite sent to {target_number}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/template', methods=['GET'])
def send_template():
    """Endpoint to send a Twilio content template."""
    target_number = request.args.get('to', '33756941611')
    content_sid = request.args.get('sid', 'HXb5b62575e6e4ff6129ad7c8efe1f983e')
    # Default variables from user's sample
    content_vars = request.args.get('vars', '{"1":"12/1","2":"3pm"}')

    if not target_number.startswith('whatsapp:'):
        target_number = f'whatsapp:+{target_number.lstrip("+")}'

    try:
        message = client.messages.create(
            from_=TWILIO_NUMBER,
            content_sid=content_sid,
            content_variables=content_vars,
            to=target_number
        )
        return jsonify({
            "status": "success",
            "message_sid": message.sid,
            "info": f"Template {content_sid} sent to {target_number}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("--- Twilio WhatsApp Agent Started ---")
    
    # Send startup message to user
    try:
        user_number = 'whatsapp:+33756941611'
        print(f"Sending startup notification to {user_number}...")
        client.messages.create(
            from_=TWILIO_NUMBER,
            body='Agent is online and ready to receive your CV!',
            to=user_number
        )
        print("✅ Startup notification sent.")
    except Exception as e:
        print(f"⚠️ Could not send startup message: {e}")

    print("1. Run 'ngrok http 5000'")
    print("2. Configure Twilio Sandbox Webhook to: <your-ngrok-url>/twilio_webhook")
    app.run(port=5000, debug=True)
