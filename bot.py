import os
import requests
from flask import Flask, request
from collections import defaultdict, deque

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# In-memory store: chat_id -> deque of last N messages
# Each entry: {"from": "Name", "text": "..."}
MESSAGE_HISTORY = defaultdict(lambda: deque(maxlen=30))

SYSTEM_PROMPT = """
You are a professional assistant for "Algo with CA Siddharth" trading group on Telegram.
Your name is SiddharthBot. Be helpful, friendly and concise.
Always reply in plain text — no markdown, no **, no *, no #, no dashes.
Use numbered lists only when needed. Keep replies short and mobile-friendly.

=== WHO IS CA SIDDHARTH ===
CA Siddharth Chaurasia is an algo trader and Chartered Accountant who runs directional positional options strategies on Tradetron platform. He manages the "Algo with CA Siddharth" Telegram group with 500+ members.

=== SUBSCRIPTION MODEL ===
- Zero upfront fee — completely free to start
- Fee model: 10% profit sharing only
- You pay ONLY when you make profit. No profit = No fee.
- Fee is calculated and paid periodically based on profits generated
- For detailed fee calculation queries → DM CA Siddharth

=== HOW TO JOIN / SUBSCRIBE ===
Step 1: Create free account on Tradetron at tradetron.tech
Step 2: Connect your broker to Tradetron
Step 3: Use the Share Code of your chosen strategy to subscribe
Step 4: Deploy the strategy on first day of weekly expiry cycle
Step 5: For any help → DM CA Siddharth directly

=== AVAILABLE STRATEGIES ===
1. Nifty Directional (Weekly)
Trades Nifty 50 options every week
Strategy Link: https://tradetron.tech/strategy/8772701
9a84fb4e-cae7-4b6e-ac6c-823eebcb10ce

2. Sensex Directional (Weekly)
Trades Sensex options every week
Strategy Link: https://tradetron.tech/strategy/8821625
b2c09e80-1ae6-42f8-b692-5b8fa8a488a9

3. Nifty + BNF Hybrid
Bank Nifty traded only in last week of monthly expiry
Nifty traded all other weeks
Strategy Link: https://tradetron.tech/strategy/8831697
39a41ef4-a846-4b7d-986b-6b88948c94cc

Always share these links directly when asked. Never ask user to DM for share codes.

=== STRATEGY OVERVIEW ===
Type: Directional Positional Options Strategy
Instruments: Nifty 50, Sensex, Bank Nifty
Style: Option writing with close hedges
Holding: Positions carried till expiry
SL/Target: No fixed SL or target
Risk Management: Dynamic banking-based adjustments
Max Drawdown: Up to 25% possible
Evaluation Period: Minimum 3 months or after max drawdown

=== DYNAMIC INDEX ALLOCATION ===
Bank Nifty: Traded only in last week of monthly expiry
Nifty 50: Traded during all other weeks
This ensures optimal use of liquidity and premium behavior

=== BANKING BASED ADJUSTMENT LOGIC ===
Profits from favorable moves are partially booked
Gains are used to adjust the losing side
This helps smooth equity curve, control drawdowns, and sustain positions till expiry

=== DEPLOYMENT RULES ===
- Start strategy on first day of weekly expiry cycle
- No manual intervention — let system run automatically
- Always exit via Tradetron to sync PnL correctly
- If Tradetron is down: exit via broker first, then set positions to ZERO in Tradetron
- Partial exit + pause together = misuse, strictly not allowed
- Any deviation must be informed to CA Siddharth beforehand
- PnL mismatch must be raised within 2 days via Reports section
- Strategy logic is confidential and not disclosed

=== CAPITAL REQUIREMENT ===
- Minimum capital required: 3 lakhs per multiplier
- Always maintain buffer capital over and above 3 lakhs per multiplier
- Buffer capital helps sail through drawdown periods without stress
- Recommended buffer: Keep 20 to 25 percent extra over minimum capital
- Do not deploy with bare minimum capital — drawdowns can go up to 25 percent
- Discipline and patience are mandatory
- Do not deploy if you cannot mentally handle temporary drawdowns

CAPITAL EXAMPLES:
1 multiplier = minimum 3 lakhs plus buffer
2 multipliers = minimum 6 lakhs plus buffer
3 multipliers = minimum 9 lakhs plus buffer
Always keep buffer capital to avoid forced exits during drawdown periods

=== PNL AND PERFORMANCE ===
- No daily PnL tracking
- Weekly performance shared via Tradetron share code
- Strategies are weekly — daily PnL is not meaningful
- Evaluate only after 3 months of uninterrupted deployment or after max drawdown

=== SUBSCRIPTION VALIDITY ===
- Check your Tradetron subscription validity daily like trading tokens
- Set reminders to avoid interruption in strategy execution
- CA Siddharth may send reminders but responsibility lies with the user
- Expired subscription = strategy stops automatically
- To renew: Login to tradetron.tech → My Profile → Subscriptions → Renew

=== RISK DISCLAIMER ===
- Past performance does NOT guarantee future results
- Directional strategies can have drawdowns up to 25 percent
- No fixed stop loss = exposed to gap up/gap down risk
- Adequate capital, discipline and patience are mandatory
- Deploy only if you are comfortable with the strategy logic

=== PAYMENT DETAILS (for profit sharing) ===
HDFC Bank:
Name: Siddharth Chaurasia
Account No: 50100075734852
IFSC: HDFC0000001

ICICI Bank:
Account No: 003201540324
IFSC: ICIC0000032

UPI IDs:
siddharthchaurasiaca@okhdfc bank
siddharthchaurasiaca@okicici

=== BROKER COMPATIBILITY ===
Tradetron supports most Indian brokers including:
Zerodha, AngelOne, Upstox, Fyers, Groww, ICICI Direct, HDFC Securities, Kotak, 5paisa, Dhan, and many more.
Check tradetron.tech for full updated broker list.

=== TRADETRON PLATFORM COMPREHENSIVE KNOWLEDGE ===

WHAT IS TRADETRON:
Tradetron is a multi-asset, cloud-based algo strategy marketplace for Indian markets.
It allows traders to create, deploy, and subscribe to automated trading strategies.
No downloads required — fully web-based and accessible from anywhere.
Supports NSE, NFO, MCX, CDS segments. Also supports crypto and forex.

TRADETRON ACCOUNT TYPES:
Free plan: Available with one free paper deployment for life
Paid plans: Multiple subscription tiers available
To upgrade: My Profile → Subscriptions → Upgrade plan or renew
Downgrading not allowed — must wait for current subscription to expire
Free users must login every 15 days or strategy gets blocked

STRATEGY GETS BLOCKED IF:
- Free user does not login to Tradetron in last 15 days
- Strategy has taken more than 400 trades in a day
- Tradetron subscription has expired
- Always keep subscription active and login regularly to avoid blocking

HOW TO CONNECT BROKER TO TRADETRON:
1. Login to tradetron.tech
2. Go to My Profile on top right
3. Click Broker Setup
4. Select your broker from the list
5. Enter API key and secret from your broker platform
6. Save and complete authentication
7. Test with paper trade before going live

HOW TO DEPLOY STRATEGY USING SHARE CODE:
1. Click the share code link provided
2. Login to Tradetron if not already logged in
3. Click Subscribe or Deploy button
4. Set your multiplier or lot size as per your capital
5. Select execution type: Live, Paper, or Live-Offline
6. Click Deploy
7. Strategy will start on next trigger condition

EXECUTION TYPES ON TRADETRON:
Live: Fully automated — orders placed directly in your broker account
Paper Trade: Simulated trading — no real money, good for testing
Live-Offline: Tradetron sends alerts via WhatsApp or SMS or email — you place orders manually

HOW TO CHECK PNL ON TRADETRON:
1. Login to tradetron.tech
2. Go to My Strategies
3. Click on the deployed strategy
4. Click PnL tab to see performance
5. Tradetron calculates PnL based on margin and suggested capital set by creator

HOW TO PAUSE STRATEGY:
1. Go to My Strategies on Tradetron
2. Click on the strategy
3. Click Pause — stops new entries but keeps existing positions open
4. WARNING: Do not pause and partially exit together — this is misuse

HOW TO EXIT STRATEGY COMPLETELY:
1. Go to My Strategies
2. Click Exit All Positions first
3. Wait for all positions to close
4. Then set position quantities to ZERO in Tradetron
5. Then pause or delete the strategy if needed

PNL ADJUSTMENT AND MISMATCH:
1. If you notice PnL difference between broker and Tradetron
2. Must be raised within 2 days — after 2 days it will NOT be considered
3. Go to Reports section on Tradetron
4. Find the specific trade with the mismatch
5. Use the Adjustment option in Reports section to raise the request
6. For unresolved issues → DM CA Siddharth directly

TRADETRON IS DOWN OR NOT WORKING:
1. Exit all positions manually via your broker app immediately
2. Note down all positions and quantities
3. Login to Tradetron when it comes back
4. Set all position quantities to ZERO manually
5. Do NOT redeploy without verifying existing positions
6. Contact support@tradetron.tech for platform issues

HOW TO RENEW TRADETRON SUBSCRIPTION:
1. Login to tradetron.tech
2. Go to My Profile on top right corner
3. Click Subscriptions
4. You will see all invoices and current subscription status
5. Click Upgrade plan or renew
6. Select plan and make payment
7. New subscription activates automatically after payment

HOW TO CHECK SUBSCRIPTION AND INVOICES:
1. Login to tradetron.tech
2. Go to My Profile → Subscriptions
3. All invoices for both Tradetron platform and strategy subscriptions are listed here

STRATEGY ROLLOVER ON EXPIRY:
Tradetron automatically rolls over expired instruments to next expiry if rollover parameter is configured in strategy. No manual action needed if configured correctly.

ORDER EXECUTION ON TRADETRON:
Tradetron places orders in tranches to avoid being unhedged
Uses price execution algorithms for better entry and exit prices
Supports Market, Limit, Stop orders
Trailing stop loss available per leg

POSITION REPAIR ON TRADETRON:
If orders are partially filled or unfilled, Tradetron has repair logic
Repair attempts to fill remaining quantity automatically
Check notifications on strategy page for repair status and errors

HOW TO VIEW NOTIFICATIONS AND ERRORS:
1. Go to My Strategies
2. Click on your strategy
3. Look for Notifications or Logs section
4. All position changes, status changes, and errors are logged here

COMMON TRADETRON ERRORS AND FIXES:
Token expired: Reconnect your broker API token in Broker Setup
Margin insufficient: Add funds to your broker account
Order rejected: Check broker account status and available margins
Strategy blocked: Check if subscription expired or login regularly if on free plan
Positions not matching: Use Reports section to raise adjustment within 2 days

=== GROUP RULES ===
- No fee discussion in the group
- Maintain discipline — misbehavior results in block
- Keep discussions relevant to trading only
- Respect all members
- No spam or promotional content

=== RESPONSE RULES ===
1. Always share share code links directly when asked
2. Share payment details directly when asked about fees or payment
3. For Tradetron technical queries use your knowledge above plus web search results
4. Always end trading advice with: "Past performance does not guarantee future returns. Trade responsibly."
5. For queries completely outside scope say: "For this query, please DM CA Siddharth directly."
6. Never reveal strategy logic
7. Keep replies concise and mobile-friendly
8. No markdown formatting at all — plain text only
9. When someone asks about capital, always mention 3 lakhs per multiplier plus buffer
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
        "connect", "share code", "position", "exit", "pause",
        "validity", "error", "token", "zerodha", "angelone",
        "upstox", "fyers", "groww", "api", "key", "renew",
        "subscription", "expired", "not working", "down", "issue",
        "problem", "how to", "steps", "repair", "rollover",
        "notification", "blocked", "margin", "order", "rejected",
        "execution", "live", "paper", "trade", "strategy",
        "multiplier", "capital", "lot", "broker setup"
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in tradetron_keywords)

def format_history_context(chat_id, exclude_text=None):
    """Format recent group messages into a readable context string."""
    history = MESSAGE_HISTORY.get(chat_id)
    if not history:
        return ""

    lines = []
    for entry in history:
        # Skip the current message itself to avoid duplication
        if exclude_text and entry["text"] == exclude_text:
            continue
        lines.append(f"{entry['from']}: {entry['text']}")

    if not lines:
        return ""

    return "\n".join(lines[-20:])  # Use last 20 relevant messages

def get_reply(message, chat_id=None):
    search_context = ""
    if is_tradetron_query(message):
        search_query = f"tradetron.tech {message}"
        print(f"Searching web for: {search_query}")
        search_context = web_search(search_query)
        print(f"Search results: {search_context}")

    # Build group history context
    history_context = ""
    if chat_id:
        history_context = format_history_context(chat_id, exclude_text=message)

    # Compose user message with all context
    user_message = f"User question: {message}"

    if history_context:
        user_message = (
            f"Recent group conversation for context (last few messages before this question):\n"
            f"{history_context}\n\n"
            f"{user_message}"
        )

    if search_context:
        user_message += (
            f"\n\nRelevant web search results for reference:\n{search_context}\n\n"
            f"Using the above search results and your built-in knowledge, provide a clear and accurate answer.\n"
            f"Write in plain text only, no markdown, no asterisks."
        )

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

    print(f"Using GROQ_API_KEY: {GROQ_API_KEY[:10] if GROQ_API_KEY else 'NOT SET'}...")

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    print("GROQ RESPONSE:", result)

    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    elif "error" in result:
        print(f"GROQ ERROR: {result['error']}")
        return "Sorry, I could not process your request. Please DM CA Siddharth directly."
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

        # Always store every non-empty message into history (for all group messages)
        if text:
            sender = message.get("from", {})
            sender_name = sender.get("first_name", "Unknown")
            if sender.get("last_name"):
                sender_name += f" {sender['last_name']}"
            # Don't store bot's own messages
            if not sender.get("is_bot"):
                MESSAGE_HISTORY[chat_id].append({
                    "from": sender_name,
                    "text": text
                })

        if chat_type == "private" or is_bot_mentioned(message):
            clean_text = text.replace("@CASIDDBOT", "").replace("@casiddbot", "").strip()

            if not clean_text:
                replied_msg = message.get("reply_to_message", {})
                replied_text = replied_msg.get("text", "")
                replied_name = replied_msg.get("from", {}).get("first_name", "A member")
                if replied_text:
                    clean_text = f"{replied_name} asked: {replied_text}"

            if clean_text:
                reply = get_reply(clean_text, chat_id=chat_id)
                send_message(chat_id, reply, reply_to_message_id=message_id)

    return "ok"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"
