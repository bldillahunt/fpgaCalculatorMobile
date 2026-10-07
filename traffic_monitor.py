import json
from urllib import request
from fastapi import Request
from nicegui import app, ui

# Paste your copied Discord URL here
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1556447261037174934/4P1RFSj1CJj3JAwWDrc9zRY6-9LuWBNOzOZidWkFcvSDirRYwF9P7SV2qvN7oC2XZsyj"

def send_discord_alert(user_ip, user_agent):
    # Detect if they are likely on a mobile device or desktop
    device = " Mobile" if any(x in user_agent.lower() for x in ["iphone", "android", "mobile"]) else " Desktop/PC"

    payload = {
        "content": f" **New Visitor Detected!**\n **IP:** `{user_ip}`\n **Device:** {device}\n *Time to see if they copy-paste some hex!*"
    }
    
    req = request.Request(
        DISCORD_WEBHOOK_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with request.urlopen(req) as response:
            pass # Successfully sent
    except Exception as e:
        print(f"Failed to send Discord alert: {e}", flush=True)

def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "Unknown"

@ui.page('/')
def main_page(request: Request):
    user_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Strictly filter out Render's internal 10.x.x.x network checks
    if not user_ip.startswith("10.") and user_ip != "Unknown":
        # Fires the webhook safely in the background so your app remains fast
        app.background_tasks.create(send_discord_alert(user_ip, user_agent))
    
    # Your beautiful 5-data-type calculator UI code goes here
    ui.label("Multi-Format Engineer Calculator")

ui.run()
