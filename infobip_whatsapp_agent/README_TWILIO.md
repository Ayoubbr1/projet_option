# Twilio WhatsApp Agent Setup

Since Infobip blocked your shared number configuration, we use Twilio's free sandbox.

## 1. Sign Up for Twilio
1.  Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio) (Free).
2.  Verify your email and phone number.

## 2. Connect to Sandbox
1.  In Twilio Console, go to **Messaging** > **Try it out** > **Send a WhatsApp message**.
2.  Follow instructions to connect your phone (usually sending a code like `join sudden-giant` to `+1 415 523 8886`).
3.  Once connected, go to **Sandbox Settings** (left menu usually under Messaging > Settings > WhatsApp Sandbox Settings).

## 3. Configure Webhook
1.  Run ngrok if not running:
    ```powershell
    & "C:\Users\HP\Downloads\ngrok-v3-stable-windows-amd64\ngrok.exe" http 5000
    ```
2.  Copy the URL (e.g., `https://xxxx.ngrok-free.app`).
3.  In Twilio Sandbox Settings, paste this URL into **"When a message comes in"**:
    Append `/twilio_webhook` at the end.
    Example: `https://xxxx.ngrok-free.app/twilio_webhook`
4.  Set method to **POST**.
5.  Click **Save**.

## 4. Run the Agent
1.  Stop any other python scripts.
2.  Run:
    ```bash
    python twilio_agent.py
    ```
3.  Send a file to the Twilio WhatsApp number!
