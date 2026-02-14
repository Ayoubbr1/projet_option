import os
import json
import requests
import mimetypes
import logging
from flask import Flask, request, jsonify

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Configuration
API_KEY = "9af22126dc9e2591c20affc88d06f2f3-647afdf4-dab8-4586-8fd7-22aaa550d695"
BASE_URL = "https://m9mz34.api.infobip.com"
DOWNLOAD_DIR = "downloads"

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
logging.info(f"Download directory set to: {os.path.abspath(DOWNLOAD_DIR)}")

def get_headers():
    return {
        'Authorization': f'App {API_KEY}',
        'Accept': 'application/json'
    }

def download_file(url, message_id, sender):
    """Downloads a file from the given URL."""
    try:
        logging.info(f"Attempting to download content from: {url}")
        
        # 1. Try with authentication headers first
        logging.debug("Method 1: Downloading with Authorization header...")
        response = requests.get(url, headers=get_headers(), stream=True)
        
        # 2. If that fails, try without headers (sometimes webhook URLs are temporary public links)
        if response.status_code != 200:
            logging.warning(f"Method 1 failed with status {response.status_code}. Method 2: Trying without headers...")
            response = requests.get(url, stream=True)
            
        if response.status_code == 200:
            # Guess extension from content-type
            content_type = response.headers.get('content-type')
            extension = mimetypes.guess_extension(content_type) or ".bin"
            
            # Create a filename
            filename = f"{sender}_{message_id}{extension}"
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            
            # Save the file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logging.info(f"SUCCESS: File saved to: {filepath}")
            return True
        else:
            logging.error(f"FAILURE: Could not download file. Final Status: {response.status_code}")
            logging.error(f"Response Body: {response.text}")
            return False
            
    except Exception as e:
        logging.exception(f"Exception occurred while downloading file: {str(e)}")
        return False

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    """Handle incoming Infobip webhooks."""
    print("\n----- WEBHOOK RECEIVED -----")
    if request.method == 'GET':
        print("Received GET request (Validation check?)")
        return "Webhook is active", 200

    try:
        data = request.json
        print("Raw Payload:")
        print(json.dumps(data, indent=2))
        
        results = data.get('results', [])
        
        for msg in results:
            message_id = msg.get('messageId')
            sender = msg.get('from')
            
            # Explore the message structure to find the URL
            message_data = msg.get('message', {})
            
            # Check for generic 'url' in message
            media_url = message_data.get('url')
            
            # Check deep content structure (sometimes used in specific integrations)
            if not media_url:
                media_url = message_data.get('content', {}).get('mediaUrl')
                
            if media_url:
                print(f"Found Media URL for message {message_id} from {sender}")
                download_file(media_url, message_id, sender)
            else:
                print(f"Message {message_id} from {sender} does not contain a recognized media URL.")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    print(f"Starting Agent...")
    print(f"1. Run 'ngrok http 5000' in a separate terminal.")
    print(f"2. Configure your Infobip Webhook URL to the ngrok URL + /webhook")
    print(f"3. Send a file to the WhatsApp number.")
    app.run(port=5000, debug=True)