from flask import Flask, request, jsonify
import requests, json
import linebot

app = Flask(__name__)

# ここ気にしないで
import os

if os.getenv("RUNNIG_GITHUB_CI") is None:
    from app.env import *
    from app import deploy

    app.register_blueprint(deploy.bp)


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    events = data.get("events", [])
    if not events:
        return jsonify({"status": "no events"}), 200

    event = events[0]
    reply_token = event.get("replyToken")
    received_message = event["message"].get("text")
    user_id = event["source"].get("userId")

    if not reply_token:
        return jsonify({"status": "no reply token"}), 200

    if received_message == "認証":
        messages = [
            {
                "type": "text",
                "text": f"https://mails.amano.mydns.jp/gmail/auth?openExternalBrowser=1&clientid={user_id}",
            }
        ]
    elif received_message == "要約":
        loading_spinner(user_id)
        res = requests.get(
            f"https://mails.amano.mydns.jp/gmail/emails/summary?line_id={user_id}"
        )
        data = res.json()
        summaries = data["summary"]
        messages = [
            {
                "type": "text",
                "text": "\n--------\n".join(summaries),
            }
        ]
    elif received_message == "既読":
        res = requests.get(
            f"https://mails.amano.mydns.jp/gmail/emails/read?line_id={user_id}"
        )
        response_text = res.text.strip('"')
        messages = [
            {
                "type": "text",
                "text": response_text,
            }
        ]
    elif received_message == "version":
        messages = [
            {
                "type": "text",
                "text": "0.0.1\n2021/10/10\nAmano",
            }
        ]
    else:
        messages = [
            {
                "type": "text",
                "text": "cant understand your message.",
            }
        ]

    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": f"Bearer {CHANNEL_TOKEN}",
    }

    payload = {
        "replyToken": reply_token,
        "messages": messages,
    }

    response = requests.post(REPLY_URL, headers=headers, json=payload)

    if response.status_code != 200:
        return jsonify({"status": "error", "detail": response.text}), 500

    return jsonify({"status": "success"}), 200


def loading_spinner(user_id):
    url = "https://api.line.me/v2/bot/chat/loading/start"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer `{CHANNEL_TOKEN}`",
    }

    data = {
        "chatId": user_id,
        "loadingSeconds": 5,
    }

    response = requests.post(url, headers=headers, json=json.dumps(data))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=49515)
