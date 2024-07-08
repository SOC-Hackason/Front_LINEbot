from flask import Flask, request, jsonify
import requests, json
import linebot

app = Flask(__name__)

# ここ気にしないで
import os
'''
if os.getenv("RUNNIG_GITHUB_CI") is None:
    from app.env import *
    from app import deploy

    app.register_blueprint(deploy.bp)
    '''
from app.env import *

BACKEND_URL = "https://mails.amano.mydns.jp"

#Flaskの書き方
@app.route("/")
def hello():
    return "Hello, World!"

#LINEプラットフォームがwebhook URLのサーバにアクセスしたときにこのプログラムがサーバに返す関数
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

    #受け取ったメッセージから送るメッセージmessagesを決定
    if received_message == "認証":
        messages = [
            {
                "type": "text",
                "text": f"https://mails.amano.mydns.jp/gmail/auth?openExternalBrowser=1&clientid={user_id}",
            }
        ]
    elif received_message == "要約":
        print(user_id)
        print(loading_spinner(user_id))
        res = requests.get(
            f"https://mails.amano.mydns.jp/gmail/emails/summary?line_id={user_id}"
        )
        data = res.json()
        summaries = data["message"]
        msg_ids = data["msg_ids"]
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
                "text": "0.0.1\n2023\nAmano",
            }
        ]
    elif received_message == "フレックス":
        with open(os.path.join(os.path.dirname(__file__), "flex.json"), "r") as j:
            messages = json.load(j)
    else:
        # get 
        messages = free_message(received_message, user_id)
        

    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": f"Bearer {CHANNEL_TOKEN}",
    }

    #サーバにPOSTするデータ（荷物，payload）にmessagesを乗せる
    payload = {
        "replyToken": reply_token,
        "messages": messages,
    }

    #サーバにPOST
    response = requests.post(REPLY_URL, headers=headers, json=payload)

    #接続状況返す　200は成功
    if response.status_code != 200:
        return jsonify({"status": "error", "detail": response.text}), 500

    return jsonify({"status": "success"}), 200

def free_message(sentence, line_id):
    url = f"https://mails.amano.mydns.jp/gmail/free_sentence?line_id={line_id}"
    data = {
        "sentence": sentence,
        "line_id": line_id
    }

    response = requests.post(url, json=data)
    print(response)
    response = response.json()
    if response.get("res") == "summary":
        messages = summary_message(response["message"])
    return messages
    
def summary_message(summaries):
    messages = [
        {
            "type": "text",
            "text": "\n--------\n".join(summaries),
        }
    ]
    return messages

def loading_spinner(user_id):
    url = "https://api.line.me/v2/bot/chat/loading/start"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer `{CHANNEL_TOKEN}`"
    }

    data = {
        "chatId": user_id,
        "loadingSeconds": 5
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
