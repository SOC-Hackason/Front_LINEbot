from flask import Flask, request, jsonify
import requests, sys, json, os, datetime
import linebot
from dotenv import load_dotenv
from jsons import *
import random
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
        if not postback_data.startswith("setting") and not postback_data.startswith("back"):
            loading_spinner(user_id)
            messages = postback_reply(user_id, postback_data, postback_params)
        else:
            return jsonify({"status": "success"}), 200
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
        # 1/5の確率で広告を表示
        if random.randint(1, 2) == 1:
            messages += ads_message()
        else:
            messages += ads_message()
    elif received_message == "広告":
        messages = ads_message()
    elif received_message == "一覧":
        loading_spinner(user_id)
        messages = list_message(user_id)
    elif received_message == "ラベリング":
        messages = label_message(user_id)
    elif received_message =="分類":
        messages = class_reply(user_id)
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
    elif received_message == "before_block":
        messages = before_block_reply(user_id)
    elif received_message == "list_block":
        messages = list_block_reply(user_id)
    elif received_message == "メールをブロック":
        messages = block_unblock_message()
    elif received_message == "言語を設定":
        messages = language_setting()
    elif received_message == "使い方":
        messages = usage_message()
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
    elif postback_data.startswith("datetime"):
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
        messages = change_label(user_id, label_type, msg_id, new_label)
    elif postback_data.startswith("category"):
        category_id = postback_data.split("=")[1]
        messages = category_reply(user_id, category_id)
    # show recent address
    elif postback_data.startswith("before_block"):
        messages = before_block_reply(user_id)
    # unblock={address}
    elif postback_data.startswith("unblock"):
        unblockaddress = postback_data.split("=")[1]
        unblockaddress, address =  unblockaddress.split("&")
        messages = unblock_reply(user_id, unblockaddress, address)
    # block={address}
    elif postback_data.startswith("block"):
        blockaddress = postback_data.split("=")[1]
        blockaddress, address = blockaddress.split("&")
        messages = block_reply(user_id, blockaddress, address)
    elif postback_data.startswith("list_block"):
        messages = list_block_reply(user_id)
    elif postback_data.startswith("lang"):
        lang = postback_data.split("=")[1]
        messages = set_language(user_id, lang)
    elif postback_data.startswith("importance"):
        importance = postback_data.split("=")[1]
        messages = get_importance_message(user_id, importance, None)
    elif postback_data.startswith("ccategory"):
        category = postback_data.split("=")[1]
        messages = get_importance_message(user_id, None, category=category)
    return messages

def get_importance_message(user_id, importance=None, category=None):
    if importance is not None:
        label = LABELS_IMPORTANCE[int(importance) - 1]
        url = BACKEND_URL + "/gmail/titles_importance"
        params = {
            "line_id": user_id,
            "max_results": 12,
            "importance": label
        }
        response = requests.get(url, params=params)
        data = response.json()
        titles = data["message"]
        msg_ids = data["msg_ids"]
    if category is not None:
        label = LABELS_CATEGORY[int(category)]
        url = BACKEND_URL + "/gmail/titles_content"
        params = {
            "line_id": user_id,
            "max_results": 12,
            "content": label
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
                    "text": title + " ",
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
                    "color": "#673B4D",
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
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{label}メール一覧",
                    "weight": "bold",
                    "size": "xl",
                    "align": "center",
                    "margin": "xs",
                }
            ],
            "backgroundColor": "#EEEEEE",
            "paddingAll": "md"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": flex_contents,
            "paddingTop": "5px"
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
                    "color": "#673B4D",
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

def before_block_reply(user_id):
    url = BACKEND_URL + "/gmail/recent_addresses"
    params = {
        "line_id": user_id
    }
    response = requests.get(url, params=params)
    data = response.json()
    addresses = data["message"]
    return recent_address(addresses)

def block_reply(user_id, blockaddress, address):
    url = BACKEND_URL + "/gmail/block_address"
    params = {
        "line_id": user_id,
        "address": blockaddress,
        "addressname": address
    }
    response = requests.get(url, params=params)
    data = response.json()
    return [{"type": "text", "text":f"{blockaddress}をブロックしました"}]

def unblock_reply(user_id, unblockaddress, address):
    url = BACKEND_URL + "/gmail/unblock_address"
    params = {
        "line_id": user_id,
        "address": unblockaddress
    }
    response = requests.get(url, params=params)
    data = response.json()
    return [{"type": "text", "text":f"{address}をブロック解除しました"}]

def list_block_reply(user_id):
    url = BACKEND_URL + "/gmail/block_address_list"
    params = {
        "line_id": user_id
    }
    response = requests.get(url, params=params)
    data = response.json()
    addresses = data["message"]
    if len(addresses) == 0:
        return [{"type": "text", "text": "ブロック中のメールアドレスはありません"}]
    return recent_address(addresses, unblock=True)

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

def get_(x:dict, y:str, z:str):
    item = x.get(y)
    if item is None:
        return z
    return item

def flex_one_mail(data, msg_id):
    _from = get_(data, "from", "Unknown")
    _from = _from.split("<")[0]
    _to = get_(data, "to", "Unknown")
    _subject = get_(data, "subject", "No Subject")
    _message = get_(data, "message", "No Message")
    _importance = data["importance"]
    _category = data["category"]
    _importance_index = 3 - LABELS_IMPORTANCE.index(_importance)
    _is_English = data.get("is_English", False)
    print(data)
    print(_to)
    bubble = {
        "type": "bubble",
        "styles": {
            "body": {
                "separator": True,
                "separatorColor": "#DDDDDD"
            }
        },
        "header": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": _subject,
                    "maxLines": 3,
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True,
                    "flex": 3,
                    "offsetTop": "3px",
                    "offsetStart": "5px",
                    "offsetBottom": "3px"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "alignItems": "center",
                    "contents": [
                        {
                            "type": "image",
                            "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png",
                            "size": "30px"
                        }
                        for _ in range(_importance_index)
                    ],
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
                    "margin": "md",
                    "offsetBottom": "sm"
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
                    "margin": "md",
                    "offsetBottom": "sm"
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
                            "label": "Reply" if _is_English else "返信",
                            "data": f"action=reply%{msg_id}",
                            "displayText": "返信を作成します"
                        },
                        "color": "#673B4D",
                        "margin": "none"
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "Read" if _is_English else "既読",
                            "data": f"action=read%{msg_id}",
                            "displayText": "既読にします"
                        },
                        "color": "#673B4D",
                        "margin": "sm"
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "Gmail",
                            "data": f"action=Glink%{msg_id}"
                        },
                        "color": "#673B4D",
                        "margin": "sm"
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
                            }
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
                            "margin": "sm"
                        }
                    ]
                }
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
        messages = create_gmail_open_link_message(msg_id)
    return messages
    
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
                        "uri": "https://mails.amano.mydns.jp/other/redirect_to_gmail?openExternalBrowser=1",
                    },
                    
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
                    "color": "#673B4D",
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
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "未読メール 一覧",
                    "weight": "bold",
                    "align": "center",
                    "size": "xl",
                    "wrap": True
                }
            ],
            "backgroundColor": "#EEEEEE",
            "paddingAll": "md"
        },
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
                    "color": "#673B4D",
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

def create_gmail_open_link_message(message_id):
    # Gmailメッセージのリンクを生成
    gmail_link = f"https://mails.amano.mydns.jp/other/redirect_to_gmail?openExternalBrowser=1"
    print(gmail_link)
    
    # LINEメッセージのフォーマット
    message = {
        "type": "flex",
        "altText": "Gmailメッセージを開く",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "Gmailメッセージを開きますか？",
                        "wrap": True,
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "Gmailで開く",
                            "uri": gmail_link,
                        },
                        "style": "primary",
                        "margin": "md",
                        "color": "#673B4D"
                    }
                ]
            }
        }
    }
    
    return [message]
           
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
    url = f"https://mails.amano.mydns.jp/gmail/summary?line_id={line_id}"
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
                    "maxLines": 6,
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
                    "color": "#673B4D",
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
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "要約",
                    "weight": "bold",
                    "align": "center",
                    "size": "xl",
                    "wrap": True
                }
            ],
            "backgroundColor": "#EEEEEE",
            "paddingAll": "md"
        },
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
                    "color": "#673B4D",
                    "height": "sm"
                }
            ],
            "margin": "sm"
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
                        "data": f"dev=correct_importance&message_id={msg.get('id', '')}",
                        "displayText": "Importance Labelを修正します",
                    }
                },
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "Contents Label修正",
                        "data": f"dev=correct_contents&message_id={msg.get('id', '')}",
                        "displayText": "Contents Labelを修正します",
                    }
                },
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "次のメールへ",
                        "data": f"dev=next_mail&message_id={msg.get('id', '')}",
                        "displayText": "次のメールへ"
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

def change_label(user_id, label_type, message_id, new_label):
    url = f"https://mails.amano.mydns.jp/gmail/change_label/"
    index = LABELS_IMPORTANCE.index(new_label) if label_type == "importance" else LABELS_CATEGORY.index(new_label)
    params = {
        "msg_id": message_id,
        "label": index,
        "label_type": label_type,
        "line_id": user_id
    }
    response = requests.get(url, params=params)
    response = response.json()

    message = {
        "type": "text",
        "text": response["message"]
    }
    return [message]


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
                        "data": f"dev=next_mail&message_id={message_id}",
                        "displayText": "次のメールへ"
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
    
    
def class_reply(line_id):
    flex_contents = [
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": "重要度",
                    "wrap": True,
                    "weight": "bold",
                    "size": "md",
                    "flex": 3,
                    "gravity": "center"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "選択",
                        "data": "category=1",
                        "displayText":"重要度を選択"
                    },
                    "style": "primary",
                    "color": "#673B4D",
                    "height": "sm",
                    "flex": 1,
                }
            ],
            "margin": "sm"
        },
        {
            "type": "separator",
            "margin": "md"
        },
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": "カテゴリ",
                    "wrap": True,
                    "weight": "bold",
                    "size": "md",
                    "flex": 3,
                    "gravity": "center"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "選択",
                        "data": "category=2",
                        "displayText":"カテゴリを選択"
                    },
                    "style": "primary",
                    "color": "#673B4D",
                    "height": "sm",
                    "flex": 1,
                }
            ],
            "margin": "md"
        }
    ]

    bubble = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "分類の選択",
                    "weight": "bold",
                    "align": "center",
                    "size": "xl",
                    "wrap": True
                }
            ],
            "backgroundColor": "#EEEEEE",
            "paddingAll": "md"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": flex_contents
        }
    }

    messages = [
        {
            "type": "flex",
            "altText": "分類カテゴリの選択",
            "contents": bubble
        }
    ]

    return messages

def category_reply(user_id, category_id):
    if category_id == "1":
        flex_contents = [
            {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "icon",
                                        "size": "md",
                                        "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
                                    },
                                    {
                                        "type": "icon",
                                        "size": "md",
                                        "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
                                    },
                                    {
                                        "type": "icon",
                                        "size": "md",
                                        "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
                                    },
                                    {
                                        "type": "text",
                                        "text": "EMERGENCY",
                                        "size": "md",
                                        "color": "#8c8c8c",
                                        "weight": "bold",
                                        "margin": "md",
                                        "flex": 1,
                                        "gravity": "center"
                                    }
                                ],
                                "flex": 4,
                                "offsetTop": "9px"
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "一覧",
                                    "label": "選択",
                                    "data": "importance=1",
                                    "displayText": "重要度を選択",
                                },
                                "style": "primary",
                                "color": "#673B4D",
                                "height": "sm",
                                "flex": 2,
                                "gravity": "center"
                            }
                        ]
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "icon",
                                        "size": "md",
                                        "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
                                    },
                                    {
                                        "type": "icon",
                                        "size": "md",
                                        "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
                                    },
                                    {
                                        "type": "icon",
                                        "size": "md",
                                        "url": "https://via.placeholder.com/28x28/FFFFFF/FFFFFF"
                                    },
                                    {
                                        "type": "text",
                                        "text": "NORMAL",
                                        "size": "md",
                                        "color": "#8c8c8c",
                                        "weight": "bold",
                                        "margin": "md",
                                        "flex": 1
                                    }
                                ],
                                "flex": 4
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "一覧",
                                    "label": "選択",
                                    "data": "importance=2"
                                },
                                "style": "primary",
                                "color": "#673B4D",
                                "height": "sm",
                                "flex": 2
                            }
                        ],
                        "alignItems": "center"
                    },
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "icon",
                                        "size": "md",
                                        "url": "https://developers-resource.landpress.line.me/fx/img/review_gold_star_28.png"
                                    },
                                    {
                                        "type": "icon",
                                        "size": "md",
                                        "url": "https://via.placeholder.com/28x28/FFFFFF/FFFFFF"
                                    },
                                    {
                                        "type": "icon",
                                        "size": "md",
                                        "url": "https://via.placeholder.com/28x28/FFFFFF/FFFFFF"
                                    },
                                    {
                                        "type": "text",
                                        "text": "GARBAGE",
                                        "size": "md",
                                        "color": "#8c8c8c",
                                        "weight": "bold",
                                        "margin": "md",
                                        "flex": 1
                                    }
                                ],
                                "flex": 4
                            },
                            {
                                "type": "button",
                                "action": {
                                    "type": "postback",
                                    "label": "一覧",
                                    "label": "選択",
                                    "data": "importance=3"
                                },
                                "style": "primary",
                                "color": "#673B4D",
                                "height": "sm",
                                "flex": 2
                            }
                        ],
                        "alignItems": "center"
                    }
                ],
                "spacing": "md",
                "paddingAll": "9px"
            }
        ]

        bubble = {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                     {
                        "type": "text",
                        "text": "重要度",
                        "weight": "bold",
                        "align": "center",
                        "size": "xl",
                        "wrap": True
                }
            ],
            "backgroundColor": "#EEEEEE",
            "paddingAll": "md"
            },

            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": flex_contents
            }
        }

        messages = [
            {
                "type": "flex",
                "altText": "重要度の選択",
                "contents": bubble
            }
        ]

        return messages

    elif category_id == "2":
        flex_contents = [
            {
                "type": "box",
                "layout": "horizontal",
                "margin": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": f"{category}のアイテム",
                        "weight": "bold",
                        "size": "sm",
                        "wrap": True,
                        "margin": "md",
                        "flex": 3,
                        "gravity": "center"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "一覧",
                            "data": f"ccategory={i}",
                            "displayText":f"{category}を選択"
                        },
                        "style": "primary",
                        "color": "#673B4D",
                        "height": "sm",
                        "flex": 1,
                        "gravity": "center",
                        "margin": "sm"
                    },
                ],
            } 
            for i, category in enumerate(LABELS_CATEGORY)
        ]

        bubble = {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "カテゴリ",
                        "weight": "bold",
                        "align": "center",
                        "size": "xl",
                        "wrap": True
                    }
                ],
                "backgroundColor": "#EEEEEE",
                "paddingAll": "md"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": flex_contents
            }
        }

        messages = [
            {
                "type": "flex",
                "altText": "カテゴリの選択",
                "contents": bubble
            }
        ]

        return messages

def usage_message():
    bubble = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "使い方",
                    "size": "xl",
                    "margin": "xs",
                    "align": "center",
                    "decoration": "none",
                    "style": "normal",
                    "weight": "bold"
                }
            ],
            "position": "relative",
            "backgroundColor": "#EEEEEE",
            "alignItems": "center",
            "margin": "none",
            "spacing": "none",
            "height": "50px",
            "offsetTop": "none",
            "offsetBottom": "none",
            "paddingAll": "10px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "<機能＞",
                    "margin": "none",
                    "size": "sm",
                    "weight": "regular",
                    "offsetBottom": "5px"
                },
                {
                    "type": "text",
                    "text": "・一覧",
                    "size": "sm",
                    "weight": "bold",
                    "margin": "xs",
                    "action": {
                        "type": "message",
                        "label": "list",
                        "text": "一覧"
                    }
                },
                {
                    "type": "text",
                    "text": "未読メールのタイトルを表示します",
                    "weight": "regular",
                    "size": "sm",
                    "margin": "xs"
                },
                {
                    "type": "text",
                    "text": "・要約",
                    "margin": "md",
                    "size": "sm",
                    "weight": "bold",
                    "action": {
                        "type": "message",
                        "label": "summary",
                        "text": "要約"
                    }
                },
                {
                    "type": "text",
                    "text": "最新のAIが未読メールを要約します",
                    "size": "sm",
                    "margin": "xs"
                },
                {
                    "type": "text",
                    "text": "・分類",
                    "margin": "md",
                    "size": "sm",
                    "weight": "bold",
                    "action": {
                        "type": "message",
                        "label": "classification",
                        "text": "分類"
                    }
                },
                {
                    "type": "text",
                    "text": "メールを重要度とカテゴリで分類します",
                    "size": "sm",
                    "wrap": True,
                    "margin": "xs"
                },
                {
                    "type": "separator",
                    "margin": "md"
                },
                {
                    "type": "text",
                    "text": "<設定＞",
                    "margin": "md",
                    "size": "sm",
                    "weight": "regular",
                    "offsetTop": "2px",
                    "offsetBottom": "5px"
                },
                {
                    "type": "text",
                    "text": "・定期配信",
                    "margin": "md",
                    "size": "sm",
                    "weight": "bold",
                    "action": {
                        "type": "datetimepicker",
                        "label": "配信時刻の設定",
                        "data": "datetime",
                        "mode": "datetime"
                    }
                },
                {
                    "type": "text",
                    "text": "決まった時刻に、未読メール一覧を取得します",
                    "size": "sm",
                    "wrap": True,
                    "margin": "xs"
                },
                {
                    "type": "text",
                    "text": "・ブロック",
                    "margin": "md",
                    "size": "sm",
                    "weight": "bold",
                    "action": {
                        "type": "message",
                        "label": "block",
                        "text": "メールをブロック"
                    }
                },
                {
                    "type": "text",
                    "text": "メールをブロックできます",
                    "size": "sm",
                    "margin": "xs"
                },
                {
                    "type": "text",
                    "text": "・言語",
                    "margin": "md",
                    "size": "sm",
                    "weight": "bold",
                    "action": {
                        "type": "message",
                        "label": "language",
                        "text": "言語を設定"
                    }
                },
                {
                    "type": "text",
                    "text": "使用言語を設定できます",
                    "margin": "xs",
                    "size": "sm"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "↑太字をタップ↑",
                    "size": "sm",
                    "margin": "xs",
                    "align": "center",
                    "weight": "regular",
                    "color": "#808080"
                }
            ]
        },
        "styles": {
            "header": {
                "separator": False
            },
            "footer": {
                "separator": True
            }
        }
    }

    message = {
        "type": "flex",
        "altText": "使い方ガイド",
        "contents": bubble
    }

    return [message]

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
