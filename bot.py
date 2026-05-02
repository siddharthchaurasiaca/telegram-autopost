import os
import requests
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

SYSTEM_PROMPT = """
You are a professional assistant for "Algo with CA Siddharth" trading group on Telegram.

Your job:
1. Answer questions about our strategies, subscription, Tradetron platform
2. For Tradetron-related questions, use the web search results provided to give accurate answers
3. Give clean, simple replies — no markdown, no asterisks, no bullet symbols
4. Be friendly, concise and accurate

=== SUBSCRIPTION MODEL ===
- There is absolutely NO upfront or fixed subscription fee
- Fee model: 10% profit sharing only — members pay ONLY when they make profit
- No profit = No fee
- For joining or fee queries → DM CA Siddharth directly

=== HOW TO SUBSCRIBE ===
1. DM CA Siddharth to confirm interest
2. Get the Share Code for your chosen strategy
3. Create free account on Tradetron (tradetron.tech)
4. Connect your broker to Tradetron
5. Use Share Code to deploy the strategy
6. Start on the first day of weekly expiry cycle

=== AVAILABLE STRATEGIES ===
1. Nifty Directional (Weekly)
Share Code: https://tradetron.tech/strategy/87727019a84fb4e-cae7-4b6e-ac6c-823eebcb10ce

2. Sensex Directional (Weekly)
Share Code: https://tradetron.tech/strategy/8821625b2c09e80-1ae6-42f8-b692-5b8fa8a488a9

3. Nifty + BNF Hybrid
BNF traded only in last week of monthly expiry, Nifty all other weeks
Share Code: https://tradetron.tech/strategy/883169739a41ef4-a846-4b7d-986b-6b88948c94cc

=== STRATEGY OVERVIEW ===
Directional Positional Options Strategy on Nifty, Sensex and Bank Nifty.
Option writing with close hedges. Positions carried till expiry.
No fixed SL or target — managed via dynamic banking-based adjustments.
Drawdowns possible up to 25%. Evaluate only after 3 months or max drawdown.

=== DEPLOYMENT RULES ===
- No manual intervention — let the system run
- Always exit via Tradetron to sync PnL
- If Tradetron is down, exit via broker and set positions to ZERO in Tradetron
- Partial exit + pause = misuse, strictly not allowed
- PnL mismatch must be raised within 2 days
- Strategy logic is not disclosed

=== PAYMENT (for profit sharing) ===
HDFC Bank: Siddharth Chaurasia, A/c: 50100075734852, IFSC: HDFC0000001
ICICI Bank: A/c: 003201540324, IFSC: ICIC0000032
UPI: siddharthchaurasiaca@okhdfc bank or siddharthchaurasiaca@okicici

=== REPLY STYLE ===
- Write like a helpful human, not a robot
- No markdown formatting — no **, no *, no #, no bullet dashes
- Use plain numbered lists if needed
- Short paragraphs, easy to read on mobile
- End trading advice with: "Past performance does not guarantee future returns. Trade responsibly."
- For anything outside scope, say: "For this query, please DM CA Siddharth directly."
"""

def web_search(query):
    try:
        headers = {
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "q": query,
            "num": 3
        }
        response = requests.post("https://google.serper.dev/search", headers=headers, json=data)
        results = response.json()
        
        search_text = ""
        if "organic" in results:
            for item in results["organic"][:3]:
                title = item.get("title", "")
                snippet = item.get("snippet", "")
                link = item.get("link", "")
                search_text += f"Title: {title}\nSummary: {snippet}\nSource: {link}\n\n"
        
        return search_text if search_text else "No results found."
    except Exception as e:
        print(f"Search error: {e}")
        return ""

def is_tradetron_query(message):
    tradetron_keywords = [
        "tradetron", "adjustment", "pnl", "deploy", "broker", 
        "connect", "share code", "strategy", "position", "exit",
        "pause", "validity", "subscription", "error", "token",
        "zerodha", "angelone", "upstox", "fyers", "groww"
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in tradetron_keywords)

def get_reply(message):
    # Search web for Tradetron queries
    search_context = ""
    if is_tradetron_query(message):
        search_query = f"tradetron {message} site:tradetron.tech OR tradetron help"
        print(f"Searching web for: {search_query}")
        search_context = web_search(search_query)
        print(f"Search results: {search_context}")

    # Build prompt with search context
    user_message = message
    if search_context:
        user_message = f"""User question: {message}

Relevant web search results:
{search_context}

Using the above search results and your knowledge, provide a clear and accurate answer. 
Ignore irrelevant search results. Give practical step-by-step help if needed."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.3
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    print("GROQ RESPONSE:", result)
    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    else:
        return "Sorry, I could not process your request. Please DM CA Siddharth directly."

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
            clean_text = text.replace("@CASIDDBOT", "").replace("@casiddbot", "").strip()

            if not clean_text:
                replied_msg = message.get("reply_to_message", {})
                replied_text = replied_msg.get("text", "")
                replied_name = replied_msg.get("from", {}).get("first_name", "A member")
                if replied_text:
                    clean_text = f"{replied_name} asked: {replied_text}"

            if clean_text:
                reply = get_reply(clean_text)
                send_message(chat_id, reply, reply_to_message_id=message_id)

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"
