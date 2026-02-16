import os
import requests
import mimetypes
from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client

app = Flask(__name__)

# Twilio Credentials (set these in Railway environment variables)
ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']

# Initialize Twilio Client
client = Client(ACCOUNT_SID, AUTH_TOKEN)
TWILIO_NUMBER = os.environ['TWILIO_NUMBER']

DOWNLOAD_DIR = "downloads_twilio"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def upload_file_to_api(filepath, sender):
    """
    Uploads a file to the external API endpoint.
    
    Args:
        filepath (str): Path to the file to upload
        sender (str): The sender's phone number
    
    Returns:
        dict: Response from the API
    """
    url = "https://web-production-f19a8.up.railway.app/api/upload-resume"
    
    # Determine the content type based on file extension
    content_type, _ = mimetypes.guess_type(filepath)
    if content_type is None:
        content_type = 'application/octet-stream'  # Default fallback
    
    try:
        with open(filepath, 'rb') as file:
            files = {'file': (os.path.basename(filepath), file, content_type)}
            # Optionally include job_offer_id if needed
            # data = {'job_offer_id': 'some-job-offer-id'}  # This could come from context or be optional
            
            response = requests.post(url, files=files)
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"[SUCCESS] File uploaded successfully: {result}")
                return result
            else:
                print(f"[ERROR] Upload failed with status {response.status_code}: {response.text}")
                return {"error": f"Upload failed with status {response.status_code}", "details": response.text}
    except Exception as e:
        print(f"[ERROR] Error uploading file to API: {e}")
        return {"error": str(e)}

@app.route('/twilio_webhook', methods=['POST'])
def bot():
    """Handle incoming Twilio WhatsApp messages."""
    # Get message details
    sender = request.values.get('From', '').replace('whatsapp:', '')
    message_sid = request.values.get('MessageSid', '')
    num_media = int(request.values.get('NumMedia', 0))
    message_body = request.values.get('Body', '').strip().lower()

    print(f"Received message from {sender} with {num_media} media files.")

    # Check if the message contains a request for file upload
    if message_body in ['send file', 'upload file', 'send cv', 'upload cv', 'send resume', 'upload resume']:
        resp = MessagingResponse()
        resp.message("I'm ready to receive your file! Please send me your CV/resume now.")
        return str(resp)

    response_message = None

    # Process media
    if num_media > 0:
        for i in range(num_media):
            media_url = request.values.get(f'MediaUrl{i}')
            content_type = request.values.get(f'MediaContentType{i}')
            print(f"Media {i}: url={media_url}, content_type={content_type}")

            if media_url:
                print(f"Downloading media: {media_url}")
                extension = mimetypes.guess_extension(content_type) or ".bin"
                filename = f"{sender}_{message_sid}_{i}{extension}"
                filepath = os.path.join(DOWNLOAD_DIR, filename)

                try:
                    # Twilio requires Basic Auth (Account SID + Auth Token) for media
                    dl_response = requests.get(media_url, auth=(ACCOUNT_SID, AUTH_TOKEN), stream=True)
                    if dl_response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            for chunk in dl_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"[SUCCESS] Saved: {filepath} (size: {os.path.getsize(filepath)} bytes)")

                        # Upload the file to the external API
                        upload_result = upload_file_to_api(filepath, sender)
                        print(f"Upload result: {upload_result}")

                        # Prepare response based on upload result
                        if "error" not in upload_result:
                            response_message = "File received and uploaded to database successfully!"
                        else:
                            response_message = f"File received but upload failed: {upload_result.get('error', 'Unknown error')}"
                    else:
                        print(f"[ERROR] Failed to download: {dl_response.status_code} {dl_response.text}")
                        response_message = "Sorry, I couldn't download your file. Please try again."
                except Exception as e:
                    print(f"[ERROR] Error downloading: {e}")
                    response_message = "Sorry, an error occurred while processing your file. Please try again."
    else:
        print(f"Message body: {request.values.get('Body')}")

    resp = MessagingResponse()
    
    if num_media > 0:
        resp.message(response_message or "File received and uploaded to database!")
    else:
        resp.message("Message received! Send me a file or type 'send file' to upload your CV/resume.")
        
    return str(resp)

@app.route('/invite', methods=['GET'])
def send_invite():
    """Endpoint to trigger an 'upload your cv' invite message."""
    target_number = request.args.get('to')
    if not target_number:
        return jsonify({"error": "Missing 'to' parameter (e.g. ?to=33744119134)"}), 400
    
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
    target_number = request.args.get('to', '33744119134')
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
        user_number = os.environ.get('NOTIFY_NUMBER', 'whatsapp:+33744119134')
        if not user_number.startswith('whatsapp:'):
            user_number = f'whatsapp:+{user_number.lstrip("+")}'
        print(f"Sending startup notification to {user_number}...")
        client.messages.create(
            from_=TWILIO_NUMBER,
            body='Agent is online and ready to receive your CV!',
            to=user_number
        )
        print("[SUCCESS] Startup notification sent.")
    except Exception as e:
        print(f"[WARNING] Could not send startup message: {e}")

    # Railway provides PORT env var; bind to 0.0.0.0 for external access
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    print("Configure Twilio Sandbox Webhook to: <your-railway-url>/twilio_webhook")
    app.run(host='0.0.0.0', port=port, debug=False)
