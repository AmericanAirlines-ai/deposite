import os
import requests
from flask import Flask, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ENV
TATUM_API_KEY = "t-6942d963d8d4f0d60814073d-a75e067a71ab44ebb663d01e"
MONGO_URI = "mongodb+srv://sardfgafdg_db_user:xtARhRbScHTc8bxh@cluster0.ajih9yx.mongodb.net/dicebot"
MASTER_XPUB = "xpub6DJDCtDZH8TCLyVfcRTpjjDbiVg8NoxeoDnSJZMzvqyKZv1BSwFGExecAZ5E9pkRk6qpyBnTdT3SHpJPzqX99KfFMM5QRzog7Tr8sTaHx2Q"  # ← VERY IMPORTANT

client = MongoClient(MONGO_URI)
db = client["casino"]
users = db["users"]

HEADERS = {
    "x-api-key": TATUM_API_KEY
}

# ---------------- HEALTH ----------------
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ---------------- GENERATE ADDRESS ----------------
@app.route("/generate-address/<int:user_id>", methods=["POST","GET"])
def generate_address(user_id):
    try:
        user = users.find_one({"user_id": user_id})

        if user and user.get("deposit_address"):
            return jsonify({"address": user["deposit_address"]})

        # determine index (unique per user)
        index = users.count_documents({})

        url = f"https://api.tatum.io/v3/bsc/address/{MASTER_XPUB}/{index}"
        r = requests.get(url, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            print("❌ Tatum error:", r.text)
            return jsonify({"error": "Tatum error"}), 500

        data = r.json()

        if "address" not in data:
            print("❌ Invalid response:", data)
            return jsonify({"error": "Invalid Tatum response"}), 500

        address = data["address"]

        users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "deposit_address": address,
                    "index": index,
                    "balance": 0
                }
            },
            upsert=True
        )

        return jsonify({"address": address})

    except Exception as e:
        print("❌ SERVER ERROR:", e)
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(port=5000,host='0.0.0.0')
