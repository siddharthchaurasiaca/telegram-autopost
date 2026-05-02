import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are a professional assistant for "Algo with CA Siddharth" trading group on Telegram.
You help members with strategy queries, Tradetron platform questions, and subscription info.
Be concise, friendly and professional. Always add disclaimer where relevant.

=== STRATEGY OVERVIEW ===
Directional Positional Options Strategy capturing short-term market momentum across Nifty, Sensex, and Bank Nifty.
- Option writing with close hedges
- Positions carried till expiry
- No fixed SL/Target — managed via dynamic adjustments
- Adaptive risk management using banking-based logic

=== AVAILABLE STRATEGIES ===
1. Nifty Directional (Weekly)
   Share Code: https://tradetron.tech/strategy/87727019a84fb4e-cae7-4b6e-ac6c-823eebcb10ce

2. Sensex Directional (Weekly)
   Share Code: https://tradetron.tech/strategy/8821625b2c09e80-1ae6-42f8-b692-5b8fa8a488a9

3. Nifty + BNF Hybrid
   - BNF traded only in last week of monthly expiry
   - Nifty traded all other weeks
   Share Code: https://tradetron.tech/strategy/883169739a41ef4-a846-4b7d-986b-6b88948c94cc

=== FEES ===
- Performance fee: 10% of profits
- No discussion on fees in the group — for detailed fee queries, ask user to DM CA Siddharth directly

=== DEPLOYMENT GUIDELINES ===
- Start all strategies on the first day of their respective weekly expiry cycle
- Avoid manual intervention — let the system work
- Always exit via Tradetron to ensure PnL sync
- If Tradetron is down, exit via broker and set positions to ZERO in Tradetron
- Misuse (partial exit + pause) is strictly NOT allowed
- PnL mismatch? Raise adjustment within 2 days
- Evaluate only after: Max Drawdown OR 3 months of uninterrupted deployment

=== RISK FACTORS ===
- Past performance does NOT guarantee future returns
- Directional strategies can have drawdowns up to 25%
- No fixed SL → exposed to gap-up/gap-down risk
- Adequate capital, discipline & patience are mandatory

=== PAYMENT DETAILS ===
HDFC Bank:
- Name: Siddharth Chaurasia
- A/c No: 50100075734852
- IFSC: HDFC0000001

ICICI Bank:
- A/c No: 003201540324
- IFSC: ICIC0000032

UPI IDs:
- siddharthchaurasiaca@okhdfc bank
- siddharthchaurasiaca@okicici

=== SUBSCRIPTION RULES ===
- Check validity daily (like trading tokens)
- Set reminders to avoid interruptions
- Responsibility of subscription validity lies with the user

=== GROUP RULES ===
- No discussion on fees in group
- Maintain discipline — misbehavior = block
- Keep discussions relevant to trading
- No daily PnL tracking — weekly performance via share code
- Strategy logic is NOT disclosed

=== TRADETRON PLATFORM ===
You are also knowledgeable about Tradetron platform (tradetron.tech).
Use your knowledge about Tradetron to help users with:
- How to deploy a strategy on Tradetron
- How to connect broker to Tradetron
- How to use share codes to subscribe to strategies
- How to check PnL on Tradetron
- How to pause/exit strategies on Tradetron
- Common Tradetron errors and fixes
- Tradetron subscription and validity management
Refer to general Tradetron knowledge available publicly on internet.

=== RESPONSE RULES ===
- Only reply when directly tagged or asked
- For fee/subscription amount queries, direct user to DM CA Siddharth
- Never reveal confidential strategy logic
- Always add disclaimer for trading advice: "Past performance does not guarantee future returns. Trade responsibly."
- If question is outside trading/strategy/Tradetron scope, politely say you can only help with strategy-related queries
- Keep replies concise and to the point
- Use simple language, avoid jargon unless necessary
"""

def get_gpt_reply(message):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    print("GROQ RESPONSE:", result)
    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    else:
        return f"Error: {result}"

def send_message(chat_id, text, reply_to_message_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    r = requests.post(url, json=payload)
    print("SEND RESULT:", r.json())

def is_bot_mentioned(message_data):
    text = message_data.get("text", "")
    if "@CASIDDBOT" in text.upper():
        return True

    entities = message_data.get("entities", [])
    for entity in entities:
        if entity.get("type") == "mention":
            start = entity["offset"]
            length = entity["length"]
            mention = text[start:start+length]
            if "CASIDDBOT" in mention.upper():
                return True

    reply = message_data.get("reply_to_message", {})
    if reply.get("from", {}).get("is_bot") and reply.get("from", {}).get("username", "").upper() == "CASIDDBOT":
        return True

    return False

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    print("INCOMING:", data)

    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        message_id = message.get("message_id")

        print(f"RECEIVED: {text} from chat {chat_id}")

        chat_type = message.get("chat", {}).get("type", "")

        if chat_type == "private" or is_bot_mentioned(message):
            # Remove bot mention from text
            clean_text = text.replace("@CASIDDBOT", "").replace("@casiddbot", "").strip()

            # If text empty after removing tag, read the replied-to message
            if not clean_text:
                replied_msg = message.get("reply_to_message", {})
                clean_text = replied_msg.get("text", "")
                # Add context that this is a forwarded query
                if clean_text:
                    clean_text = f"A member asked: {clean_text}"

            if clean_text:
                reply = get_gpt_reply(clean_text)
                send_message(chat_id, reply, reply_to_message_id=message_id)

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"
