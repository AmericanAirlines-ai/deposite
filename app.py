import os
import requests
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ENV
TATUM_API_KEY = "t-6942d963d8d4f0d60814073d-a75e067a71ab44ebb663d01e"
MONGO_URI = "mongodb+srv://sardfgafdg_db_user:xtARhRbScHTc8bxh@cluster0.ajih9yx.mongodb.net/dicebot"

# DB
client = MongoClient(MONGO_URI)
db = client["casino"]
users = db["users"]

# ---------------- ADDRESS GENERATION ----------------
@app.route("/generate-address/<int:user_id>", methods=["POST"])
def generate_address(user_id):
    user = users.find_one({"user_id": user_id})
    if user and user.get("deposit_address"):
        return jsonify({"address": user["deposit_address"]})

    url = "https://api.tatum.io/v3/bsc/address"
    headers = {"x-api-key": TATUM_API_KEY}

    r = requests.post(url, headers=headers)
    data = r.json()

    address = data["address"]

    users.update_one(
        {"user_id": user_id},
        {"$set": {"deposit_address": address}},
        upsert=True
    )

    return jsonify({"address": address})


# ---------------- WEBHOOK (DEPOSIT) ----------------
@app.route("/webhook/deposit", methods=["POST"])
def deposit_webhook():
    data = request.json

    # SECURITY CHECK
    if data.get("currency") != "USDT":
        return "ignored"

    address = data["to"]
    amount = float(data["amount"])

    user = users.find_one({"deposit_address": address})
    if not user:
        return "unknown address"

    users.update_one(
        {"user_id": user["user_id"]},
        {
            "$inc": {
                "balance": amount,
                "total_deposited": amount
            }
        }
    )

    # (Optional) notify user via Telegram later
    return "ok"


if __name__ == "__main__":
    app.run(port=5000,host='0.0.0.0')
