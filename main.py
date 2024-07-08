from flask import Flask, request, jsonify
import requests, sys, json, os
import linebot
from dotenv import load_dotenv

load_dotenv()
CHANNEL_TOKEN = os.getenv("CHANNEL_TOKEN")
REPLY_URL = os.getenv("REPLY_URL")
ADD_BP = os.getenv("ADD_BP")

app = Flask(__name__)

BACKEND_URL = "https://mails.amano.mydns.jp"

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
    user_id = event["source"].get("userId")
    try:
        received_message = event["message"].get("text")
        messages = message_reply(user_id, received_message)
    except:
        postback_data = event["postback"].get("data")
        loading_spinner(user_id)
        messages = postback_reply(user_id, postback_data)
    if not reply_token:
        return jsonify({"status": "no reply token"}), 200

    
        

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
        print(response.text)
        sys.stdout.flush()
        return jsonify({"status": "error", "detail": response.text}), 500

    return jsonify({"status": "success"}), 200

def message_reply(user_id, received_message):
    if received_message == "認証":
        messages = [
            {
                "type": "text",
                "text": f"https://mails.amano.mydns.jp/gmail/auth?openExternalBrowser=1&clientid={user_id}",
            }
        ]
    elif received_message == "要約":
        loading_spinner(user_id)
        messages = summary_reply(user_id)
    elif received_message == "一覧":
        loading_spinner(user_id)
        messages = list_message(user_id)
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
                "text": "sakenomitai",
            }
        ]
    else:
        # get 
        messages = free_message(received_message, user_id)

    return messages

def postback_reply(user_id, postback_data):
    if postback_data.startswith("msg_id"):
        msg_id = postback_data.split("=")[1]
        url = BACKEND_URL + "/gmail/emails"
        params = {
            "msg_id": msg_id,
            "line_id": user_id
        }
        response = requests.get(url, params=params)
        data = response.json()
        messages = flex_one_mail(data)
    return messages

def flex_one_mail(data):
    _from = data["from"]
    _to = data["to"]
    _subject = data["subject"]
    _message = data["message"]

    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": _from,
                    "weight": "bold",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": _to,
                    "weight": "bold",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": _subject,
                    "weight": "bold",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": _message,
                    "wrap": True
                }
            ]
        }
    }

    messages = [
        {
            "type": "flex",
            "altText": "メール詳細",
            "contents": bubble
        }
    ]

    return messages

def list_message(line_id):
    url = BACKEND_URL + "/gmail/unread_titles"
    params = {
        "line_id": line_id,
        "max_results": 12
    }
    response = requests.get(url, params=params)
    data = response.json()
    titles = data["message"]
    msg_ids = data["msg_ids"]

    flex_contents = []
    for title, msg_id in zip(titles, msg_ids):
        flex_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": title,
                    "wrap": True,
                    "weight": "bold",
                    "size": "xs",
                    "maxLines": 2,
                    "flex": 3,
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "詳細",
                        "data": f"msg_id={msg_id}"
                    },
                    "style": "primary",
                    "color": "#905c44",
                    "height": "sm",
                    "margin": "sm",
                    "flex": 1,
                }
            ],
            "alignItems": "center",
            "paddingAll": "sm",
            "margin": "xs",
        })

    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": flex_contents
        }
    }

    messages = [
        {
            "type": "flex",
            "altText": "メール一覧",
            "contents": bubble
        }
    ]

    return messages
           
def free_message(sentence, line_id):
    url = f"https://mails.amano.mydns.jp/gmail/free_sentence?line_id={line_id}"
    data = {
        "sentence": sentence,
        "line_id": line_id
    }

    response = requests.post(url, json=data)
    response = response.json()
    if response.get("res") == "summary":
        messages = summary_message(response["message"])
    elif response.get("res") == "read":
        messages = read_message(response["message"])
    elif response.get("res") == "greating":
        messages = [
            {
                "type": "text",
                "text": response["message"],
            }
        ]
    else:
        messages = [
            {
                "type": "text",
                "text": response["message"],
            }
        ]
    return messages

def summary_reply(line_id):
    url = f"https://mails.amano.mydns.jp/gmail/emails/summary?line_id={line_id}"
    response = requests.get(url)
    data = response.json()
    summaries = data["message"]
    msg_ids = data["msg_ids"]
    messages = summary_message(summaries)
    return messages

def read_message(message):
    messages = [
        {
            "type": "text",
            "text": message,
        }
    ]
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
        "loadingSeconds": 10
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=49515)
