import sys
import os

# Add the subdirectory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'infobip_whatsapp_agent'))

from twilio_agent import app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
