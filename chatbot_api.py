from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# System prompt for context
SYSTEM_PROMPT = """
You are an e-commerce chatbot for EShop, an Indian online store. Answer all shopping-related queries based on user input, interpreting their intent naturally. Use INR for prices (convert USD to INR at 1 USD = 84 INR). Provide concise, relevant answers without opinions or unrelated comments. Maintain context from previous messages. If unclear, make a best guess or ask for clarification.
"""

# Static exchange rate
USD_TO_INR = 84

# Product categories with price ranges (in INR)
PRICE_RANGES = {
    "laptop": (30000, 150000),
    "mobile": (10000, 80000),
    "headphone": (1000, 15000),
    "tablet": (15000, 60000),
    "watch": (2000, 20000),
    "keyboard": (500, 5000),
    "mouse": (300, 3000),
    "monitor": (8000, 35000),
    "tv": (15000, 100000),
    "speaker": (1000, 20000),
    "camera": (5000, 50000),
    "printer": (4000, 25000),
    "router": (1000, 10000),
    "smart bulb": (500, 3000),
    "gaming console": (20000, 60000),
    "external drive": (3000, 15000),
    "power bank": (800, 5000),
    "smart home device": (2000, 15000),
    "accessory": (200, 5000),
    "software": (1000, 10000)
}

# Detail templates for each category
DETAIL_TEMPLATES = {
    "laptop": "{screen_size}-inch {display_type} display, {processor}, {ram}GB RAM, {storage}GB {storage_type}, {os}, weighs {weight}kg.",
    "mobile": "{screen_size}-inch {display_type} display, {processor}, {ram}GB RAM, {storage}GB storage, {os}.",
    "headphone": "{type}, Bluetooth {bluetooth}, up to {battery} hours battery life.",
    "tablet": "{screen_size}-inch {display_type} display, {processor}, {ram}GB RAM, {storage}GB storage, {os}.",
    "watch": "{screen_size}-inch {display_type} display, {features}, up to {battery} days battery life.",
    "keyboard": "{type} design, {connectivity} connectivity, {features}.",
    "mouse": "{type} mouse, {connectivity} connectivity, {dpi} DPI.",
    "monitor": "{screen_size}-inch {display_type} display, {resolution}, {refresh_rate}Hz refresh rate.",
    "tv": "{screen_size}-inch {display_type} TV, {resolution}, {features}.",
    "speaker": "{type} speaker, {connectivity}, {power}W output.",
    "camera": "{resolution} camera, {lens_type} lens, {features}.",
    "printer": "{type} printer, {connectivity}, {speed} pages per minute.",
    "router": "{speed}Mbps speed, {range}m range, {features}.",
    "smart bulb": "{brightness} lumens, {color} colors, {connectivity}.",
    "gaming console": "{processor}, {storage}GB storage, {features}.",
    "external drive": "{storage}GB {type}, {connectivity}, {speed}MB/s transfer rate.",
    "power bank": "{capacity}mAh capacity, {ports} USB ports, {features}.",
    "smart home device": "{type} device, {connectivity}, {features}.",
    "accessory": "{type} accessory, compatible with {compatibility}.",
    "software": "{type} software, compatible with {compatibility}."
}

# Spec options per category
SPEC_OPTIONS = {
    "laptop": {
        "screen_size": ["13.3", "14", "15.6", "17"], "display_type": ["IPS", "LED", "OLED"],
        "processor": ["Intel Core i3", "Intel Core i5", "Intel Core i7", "AMD Ryzen 5"],
        "ram": [8, 16, 32], "storage": [256, 512, 1024], "storage_type": ["SSD", "HDD"],
        "os": ["Windows 11 Home", "Windows 11 Pro"], "weight": [1.2, 1.5, 1.8, 2.0]
    },
    "mobile": {
        "screen_size": ["6.1", "6.5", "6.7"], "display_type": ["AMOLED", "LCD", "OLED"],
        "processor": ["Snapdragon 8", "MediaTek Dimensity", "Exynos 2200"], "ram": [4, 6, 8, 12],
        "storage": [64, 128, 256], "os": ["Android 13", "Android 14"]
    },
    "headphone": {
        "type": ["Over-ear", "In-ear", "On-ear"], "bluetooth": ["5.0", "5.2"], "battery": [10, 20, 30]
    },
    "tablet": {
        "screen_size": ["10.1", "11", "12.4"], "display_type": ["IPS", "AMOLED"],
        "processor": ["Snapdragon 7", "MediaTek Helio"], "ram": [4, 6, 8], "storage": [64, 128, 256],
        "os": ["Android 13"]
    },
    "watch": {
        "screen_size": ["1.3", "1.5", "1.8"], "display_type": ["AMOLED", "LCD"],
        "features": ["heart rate monitoring", "GPS"], "battery": [5, 7, 14]
    },
    "keyboard": {
        "type": ["Mechanical", "Membrane"], "connectivity": ["Wired", "Wireless"],
        "features": ["RGB lighting", "programmable keys"]
    },
    "mouse": {
        "type": ["Optical", "Laser"], "connectivity": ["Wired", "Wireless"], "dpi": [1600, 3200, 6400]
    },
    "monitor": {
        "screen_size": ["24", "27", "32"], "display_type": ["IPS", "LED"],
        "resolution": ["1080p", "1440p", "4K"], "refresh_rate": [60, 75, 120]
    },
    "tv": {
        "screen_size": ["32", "43", "55", "65"], "display_type": ["LED", "QLED", "OLED"],
        "resolution": ["1080p", "4K", "8K"], "features": ["Smart TV", "HDR", "Dolby Atmos"]
    },
    "speaker": {
        "type": ["Bluetooth", "Wired"], "connectivity": ["Bluetooth 5.0", "AUX"], "power": [5, 10, 20]
    },
    "camera": {
        "resolution": ["12MP", "20MP"], "lens_type": ["Wide-angle", "Standard"],
        "features": ["4K video", "night mode"]
    },
    "printer": {
        "type": ["Inkjet", "Laser"], "connectivity": ["USB", "Wi-Fi"], "speed": [10, 20]
    },
    "router": {
        "speed": [300, 600, 1200], "range": [20, 30], "features": ["Dual-band", "Mesh support"]
    },
    "smart bulb": {
        "brightness": [800, 1000], "color": ["16M colors", "Warm white"], "connectivity": ["Wi-Fi"]
    },
    "gaming console": {
        "processor": ["AMD Zen 2"], "storage": [512, 1000], "features": ["4K gaming"]
    },
    "external drive": {
        "storage": [500, 1000], "type": ["HDD", "SSD"], "connectivity": ["USB 3.0"], "speed": [100, 200]
    },
    "power bank": {
        "capacity": [10000, 20000], "ports": [1, 2], "features": ["fast charging"]
    },
    "smart home device": {
        "type": ["smart speaker", "smart plug"], "connectivity": ["Wi-Fi"], "features": ["voice control"]
    },
    "accessory": {
        "type": ["phone case", "cable"], "compatibility": ["most devices"]
    },
    "software": {
        "type": ["antivirus", "office suite"], "compatibility": ["Windows", "Android"]
    }
}

# Shipping options
SHIPPING_OPTIONS = {
    "standard": {"cost": "Free over ₹5000, else ₹99", "time": "3-5 business days"},
    "express": {"cost": "₹199", "time": "1-2 business days"}
}

# Intent keywords (synonyms for flexibility)
INTENT_KEYWORDS = {
    "buy": ["buy", "order", "purchase", "get", "want"],
    "price": ["price", "cost", "how much", "rate"],
    "details": ["details", "specs", "specification", "features", "info"],
    "stock": ["stock", "available", "availability", "in stock"],
    "shipping": ["shipping", "delivery", "ship", "transport"],
    "cart": ["cart", "basket", "add to cart", "checkout"]
}

# Simulated cart
cart = []

# Store conversation history and context
conversation_history = []
last_product = None

def extract_usd_amount(message):
    match = re.search(r'\$(\d+)', message)
    if match:
        return int(match.group(1))
    return None

def extract_product(message):
    message_lower = message.lower()
    categories = PRICE_RANGES.keys()
    for category in categories:
        if category in message_lower:
            words = message_lower.split()
            product_idx = words.index(category)
            if product_idx > 0 and words[product_idx - 1] not in ["a", "to", "i", "the"]:
                product_name = f"{words[product_idx - 1]} {category}"
            else:
                product_name = category
            return {"name": product_name, "category": category, "price": random.randint(*PRICE_RANGES[category])}
    return None

def generate_product_details(category):
    specs = SPEC_OPTIONS[category]
    template = DETAIL_TEMPLATES[category]
    return template.format(**{key: random.choice(values) for key, values in specs.items()})

def match_intent(message, intent):
    return any(keyword in message.lower() for keyword in INTENT_KEYWORDS[intent])

def get_ai_response(message):
    global conversation_history, last_product, cart
    
    if not conversation_history:
        conversation_history.append(SYSTEM_PROMPT)
    
    conversation_history.append(f"User: {message}")
    message_lower = message.lower()
    usd_amount = extract_usd_amount(message)
    product_info = extract_product(message)
    
    # Greeting
    if "hi" in message_lower or "hello" in message_lower:
        return "Hi there! Welcome to EShop. How can I help you with your shopping today?"
    
    # Buy/Order intent
    if match_intent(message, "buy"):
        if product_info:
            last_product = product_info
            cart.append(last_product)
            return f"At EShop, a {product_info['name']} costs around ₹{product_info['price']:,}. Added to your cart. Want more details?"
        elif last_product and ("yes" in message_lower or "confirm" in message_lower):
            return f"Got it! A {last_product['name']} (₹{last_product['price']:,}) is in your cart. Anything else to add?"
        else:
            return "What would you like to order from EShop today?"
    
    # Price intent
    if match_intent(message, "price") and not match_intent(message, "shipping"):
        if product_info:
            last_product = product_info
            return f"At EShop, a {product_info['name']} costs around ₹{product_info['price']:,}. Want more details?"
        elif last_product:
            return f"At EShop, a {last_product['name']} costs around ₹{last_product['price']:,}. Want more details?"
        else:
            return "Which product’s price are you looking for?"
    
    # Details intent
    if match_intent(message, "details") or ("yes" in message_lower and last_product and any(kw in " ".join(conversation_history[-2:]).lower() for kw in INTENT_KEYWORDS["buy"] + INTENT_KEYWORDS["price"])):
        if product_info:
            last_product = product_info
            details = generate_product_details(last_product["category"])
            return f"At EShop, a {last_product['name']} has: {details} Anything else you’d like to know?"
        elif last_product:
            details = generate_product_details(last_product["category"])
            return f"At EShop, a {last_product['name']} has: {details} Anything else you’d like to know?"
        else:
            return "Which product do you want details for?"
    
    # Cart intent
    if match_intent(message, "cart"):
        if cart:
            cart_summary = ", ".join(f"{item['name']} (₹{item['price']:,})" for item in cart)
            total = sum(item["price"] for item in cart)
            return f"Your EShop cart contains: {cart_summary}. Total: ₹{total:,}. Ready to checkout?"
        else:
            return "Your cart is empty. What would you like to add?"
    
    # Shipping intent
    if match_intent(message, "shipping") or ("cost" in message_lower and "ship" in " ".join(conversation_history[-2:]).lower()):
        if "express" in message_lower:
            return f"Express shipping at EShop costs {SHIPPING_OPTIONS['express']['cost']} and takes {SHIPPING_OPTIONS['express']['time']}."
        elif "standard" in message_lower:
            return f"Standard shipping at EShop is {SHIPPING_OPTIONS['standard']['cost']} and takes {SHIPPING_OPTIONS['standard']['time']}."
        else:
            return f"At EShop, we offer Standard shipping ({SHIPPING_OPTIONS['standard']['cost']}, {SHIPPING_OPTIONS['standard']['time']}) and Express shipping ({SHIPPING_OPTIONS['express']['cost']}, {SHIPPING_OPTIONS['express']['time']}). Which one do you want to know about?"
    
    # USD conversion
    if usd_amount:
        inr_amount = usd_amount * USD_TO_INR
        return f"That’s around ₹{inr_amount:,} in Indian Rupees. What item are we talking about?"
    
    # Fallback with intent guess
    if last_product:
        return f"Did you mean something about a {last_product['name']}? I can help with price, details, shipping, or adding it to your cart."
    return "I’m not sure what you mean. Could you tell me more about what you’re looking for?"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    response = get_ai_response(message)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(port=5000)