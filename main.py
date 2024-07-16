from flask import Flask, request, jsonify
import requests, sys, json, os, datetime
import linebot
from dotenv import load_dotenv

load_dotenv()
CHANNEL_TOKEN = os.getenv("CHANNEL_TOKEN")
REPLY_URL = os.getenv("REPLY_URL")
ADD_BP = os.getenv("ADD_BP")

app = Flask(__name__)

BACKEND_URL = "https://mails.amano.mydns.jp"
LABELS_CATEGORY = ["WORK", "SCHOOL", "APPOINTMENT", "PROMOTIONS", "OTHER"]
LABELS_IMPORTANCE = ["EMERGENCY", "NORMAL", "GARBAGE"]

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
    print(user_id)
    sys.stdout.flush()
    try:
        received_message = event["message"].get("text")
        messages = message_reply(user_id, received_message)
    except KeyError:
        postback_data = event["postback"].get("data")
        postback_params = event["postback"].get("params")
        loading_spinner(user_id)
        messages = postback_reply(user_id, postback_data, postback_params)
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
        print("LINE_ERROR")
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
    elif received_message == "ラベリング":
        messages = label_message(user_id)
    elif received_message == "分類":
        pass
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

def postback_reply(user_id, postback_data:str, postback_params=None):
    if postback_data.startswith("msg_id"):
        msg_id = postback_data.split("=")[1]
        url = BACKEND_URL + "/gmail/emails"
        params = {
            "msg_id": msg_id,
            "line_id": user_id
        }
        response = requests.get(url, params=params)
        data = response.json()
        messages = flex_one_mail(data, msg_id)
    elif postback_data.startswith("action"):
        #reply, read, Glink
        print(postback_data.split("=")[1].split("%"))
        action, msg_id = postback_data.split("=")[1].split("%")
        sys.stdout.flush()
        messages = postback_action_reply(user_id, action, msg_id)
    elif postback_data.startswith("spaction"):
        action, msg_ids = postback_data.split("=")[1].split("%")
        msg_ids = msg_ids.split(",")
        messages = postback_spaction(user_id, action, msg_ids)
    elif postback_data.startswith("dev") and postback_data.count("&") == 1:
        # split by "&" or "="
        action, message_id = postback_data.split("&")
        action = action.split("=")[1]
        message_id = message_id.split("=")[1]
        messages = postback_dev(user_id, action, message_id)
    elif postback_data.startswith("devl"):
        action, message_id, new_label = postback_data.split("&")
        action = action.split("=")[1]
        message_id = message_id.split("=")[1]
        new_label = new_label.split("=")[1]
        messages = postback_devl(user_id, action, message_id, new_label)
    elif postback_data.startswith("配信"):
        selected_datetime = postback_params['datetime']
        messages = change_datetime(user_id, selected_datetime)
    elif postback_data.startswith("label"):
        label_type, msg_id = postback_data.split("&")
        label_type = label_type.split("=")[1]
        msg_id = msg_id.split("=")[1]
        messages = create_quick_reply(msg_id, label_type, LABELS_IMPORTANCE, "chl") if label_type == "importance" else create_quick_reply(msg_id, label_type, LABELS_CATEGORY, "chl")
    elif postback_data.startswith("chl"):
        label_type, msg_id, new_label = postback_data.split("&")
        label_type = label_type.split("=")[1]
        msg_id = msg_id.split("=")[1]
        new_label = new_label.split("=")[1]
        # TODO: 
        pass
    return messages

def change_datetime(user_id, selected_datetime:str):
    # selected_datetime is like 2024-07-16T15:24
    date = datetime.datetime.strptime(selected_datetime, "%Y-%m-%dT%H:%M")
    sys.stdout.flush()
    hour = date.hour
    minute = date.minute
    URL = f"https://mails.amano.mydns.jp/gmail/change_time?line_id={user_id}&hour={hour}&minute={minute}"
    response = requests.get(URL)
    data = response.json()
    messages = [
        {
            "type": "text",
            "text": data["message"],
        }
    ]
    return messages

def postback_spaction(user_id, action, msg_ids):
    if action == "read_all":
        url = BACKEND_URL + "/gmail/read"
        params = {
            "msg_ids": msg_ids,
            "line_id": user_id
        }
        response = requests.get(url, params=params)
        data = response.json()
        return [{"type": "text", "text": "すべて既読にしました"}]

def flex_one_mail(data, msg_id):
    _from = data["from"]
    _to = data["to"]
    _subject = data["subject"]
    _message = data["message"]
    _importance = data["importance"]
    _category = data["category"]

    bubble = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": _subject,
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True
                }
            ],
            "backgroundColor": "#EEEEEE",
            "paddingAll": "md"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "From:",
                            "size": "sm",
                            "color": "#888888",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": _from,
                            "size": "sm",
                            "wrap": True,
                            "flex": 4
                        }
                    ],
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "To:",
                            "size": "sm",
                            "color": "#888888",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": _to,
                            "size": "sm",
                            "wrap": True,
                            "flex": 4
                        }
                    ],
                    "margin": "md"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": _message,
                            "wrap": True,
                            "size": "sm",
                            "maxLines": 10,
                        }
                    ],
                    "backgroundColor": "#F7F7F7",
                    "paddingAll": "md",
                    "cornerRadius": "md",
                    "margin": "md",
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                { 
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "返信",
                            "data": f"action=reply%{msg_id}",
                            "displayText": "返信を作成します"
                        },
                        "color": "#00B900"
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "既読",
                            "data": f"action=read%{msg_id}",
                            "displayText": "既読にします"
                        },
                        "color": "#00B900"
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "GLinK(Not yet)",
                            "data": f"action=Glink%{msg_id}"
                        },
                        "color": "#00B900"
                    },
                    ],
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "style": "secondary",
                            "height": "sm",
                            "action": {
                                "type": "postback",
                                "label": f"{_importance}",
                                "data": f"label=importance&msg_id={msg_id}",
                                "displayText": f"Importanceを変更します"
                            },
                            "color": "#AAAAAA"
                        },
                        {
                            "type": "button",
                            "style": "secondary",
                            "height": "sm",
                            "action": {
                                "type": "postback",
                                "label": f"{_category}",
                                "data": f"label=category&msg_id={msg_id}",
                                "displayText": f"Categoryを変更します"
                            },
                            "color": "#AAAAAA"
                        }
                    ]
                },
            ],
            "flex": 0
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

def postback_action_reply(user_id, action, msg_id):
    if action == "reply":
        url = BACKEND_URL + "/gmail/reply"
        params = {
            "msg_id": msg_id,
            "line_id": user_id
        }
        response = requests.get(url, params=params)
        data = response.json()
        draft = data["message"]
        return create_draft_preview_message(draft)
    elif action== "read":
        url = BACKEND_URL + "/gmail/read"
        params = {
            "msg_ids": [msg_id],
            "line_id": user_id
        }
        response = requests.get(url, params=params)
        data = response.json()
        return [{"type": "text", "text": "既読にしました"}]
    elif action == "Glink":
        url = "https://mail.google.com/mail/u/0/#inbox/msg_id"
        params = {
            "msg_ids": [msg_id],
            "line_id": user_id
        }
        response = requests.get(url, params=params)
        data = response.json()
        return [{"type": "text", "text": "Gmailアプリの起動"}]
        pass

def create_draft_preview_message(draft_content):
    bubble = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "自動下書きが作成されました",
                    "weight": "bold",
                    "size": "md",
                    "wrap": True,
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": draft_content,
                    "size": "sm",
                    "wrap": True,
                    "margin": "md"
                }
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "下書きを編集(Not yet)",
                        "uri": "https://test.com"
                    }
                }
            ],
            "flex": 0
        }
    }
    
    return [{
        "type": "flex",
        "altText": "自動下書きが作成されました",
        "contents": bubble
    }]

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
                        "data": f"msg_id={msg_id}",
                        "displayText": "詳細を表示します"
                    },
                    "style": "primary",
                    "color": "#00B900",
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
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "すべて既読にする",
                        "data": f"spaction=read_all%{','.join(msg_ids)}",
                        "displayText": "すべてのメールを既読にします"
                    },
                    "style": "primary",
                    "color": "#00B900",
                    "height": "sm"
                }
            ],
            "margin": "sm"
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

    flex_contents = []
    for summary,msg_id in zip(summaries, msg_ids):
        flex_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": summary,
                    "wrap": True,
                    "weight": "bold",
                    "size": "xs",
                    "maxLines": 4,
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
                    "color": "#004aad",
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
            "altText": "要約一覧",
            "contents": bubble
        }
    ]

    return messages

def label_message(line_id, msg_id = None):
    if msg_id is not None:
        URL = f"https://mails.amano.mydns.jp/gmail/emails_dev/?line_id={line_id}&msg_id={msg_id}"
    else:
        URL = f"https://mails.amano.mydns.jp/gmail/emails_dev/?line_id={line_id}"
    print(URL)
    sys.stdout.flush()
    response = requests.get(URL)
    msg = response.json()
    print(msg)
    sys.stdout.flush()
    content = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"From: {msg.get('from', 'Unknown')}",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"To: {msg.get('to', 'Unknown')}"
                },
                {
                    "type": "text",
                    "text": f"Subject: {msg.get('subject', 'No Subject')}",
                    "wrap": True
                },
                {
                    "type": "text",
                    "text": f"Message: {msg.get('message', 'No Message')}",
                    "wrap": True
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Importance:",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": msg.get('importance', 'Unknown'),
                            "flex": 2,
                            "color": "#1DB446",
                            "weight": "bold"
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "text",
                            "text": "Contents:",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": msg.get('category', 'Unknown'),
                            "flex": 2,
                            "color": "#1DB446",
                            "weight": "bold"
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "Importance Label修正",
                        "data": f"dev=correct_importance&message_id={msg.get('id', '')}"
                    }
                },
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "Contents Label修正",
                        "data": f"dev=correct_contents&message_id={msg.get('id', '')}"
                    }
                },
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "次のメールへ",
                        "data": f"dev=next_mail&message_id={msg.get('id', '')}"
                    }
                }
            ],
            "flex": 0
        }
    }
    
    
    messages =[ {
        "type": "flex",
        "altText": "ラベリング",
        "contents": content
    }]
    
    return messages
    
def postback_dev(user_id, action, message_id):
    if action == "correct_importance":
        messages = create_quick_reply(message_id, "importance", LABELS_IMPORTANCE)
    elif action == "correct_contents":
        messages = create_quick_reply(message_id, "contents", LABELS_CATEGORY)
    elif action == "next_mail":
        messages = label_message(user_id, message_id)
        
    return messages
    
def create_quick_reply(message_id, label_type, options, tag="devl"):
    items = [
        {
            "type": "action",
            "action": {
                "type": "postback",
                "label": option,
                "data": f"{tag}={label_type}&message_id={message_id}&new_label={option}",
                "displayText": f"{label_type.capitalize()} Labelを「{option}」に更新します"
            }
        } for option in options
    ]
    
    return [{
        "type": "text",
        "text": f"新しいLabelを選択してください：",
        "quickReply": {
            "items": items
        }
    }]

def postback_devl(user_id, action, message_id, new_label):
    # send new label to backend
    url = f"https://mails.amano.mydns.jp/gmail/emails_devl/"
    index = LABELS_IMPORTANCE.index(new_label) if action == "importance" else LABELS_CATEGORY.index(new_label)
    data = {
        "message_id": message_id,
        "label": index,
        "label_type": action,
        "line_id": user_id
    }
    response = requests.get(url, params=data)
    message = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "ラベルを更新しました。つづいて更新する場合は上のメッセージからお願いします。",
                    "wrap": True
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "次のメールへ",
                        "data": f"dev=next_mail&message_id={message_id}"
                    }
                }
            ],
        }
    }
    
    return [{
        "type": "flex",
        "altText": "ラベルを更新しました",
        "contents": message
    }]
    
    
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
    app.run(debug=True, host="localhost", port=8000)
