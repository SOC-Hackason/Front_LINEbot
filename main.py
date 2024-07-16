from flask import Flask, request, jsonify, render_template, redirect
import time, datetime
import requests, sys, json, os
from dotenv import load_dotenv

load_dotenv()
CHANNEL_TOKEN = os.getenv("CHANNEL_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
REPLY_URL = os.getenv("REPLY_URL")
PUSH_URL = os.getenv("PUSH_URL")
ADD_BP = os.getenv("ADD_BP")


app = Flask(__name__)

BACKEND_URL = "https://mails.amano.mydns.jp"

blacklist=[]

#タイマー関数のせいでうるさくなったログを非表示にするコード
"""
import logging
l = logging.getLogger()
l.addHandler( logging.FileHandler( "/nul" ))
"""


#タイマー機能のせいでログがめっちゃうるさいので開発時はコメントアウトしてもらっていいです
#スタート時刻と測る時間
timer_start = None
timer_duration = 0

s = '2024/7/16 16:52'
s_format = '%Y/%m/%d %H:%M'
GoOffTime= str(datetime.datetime.strptime(s, s_format))[11:-3]

@app.route('/')
def index():
    return render_template('timerupdater.html')

#タイマーがスタート状態になるjsonを返す
@app.route('/start/<int:seconds>')
def start_timer(seconds):
    global timer_start, timer_duration
    #現在時刻を取得
    timer_start = time.time()
    timer_duration = seconds
    #状態をstartedに変更
    return jsonify({"status": "started"})


#残り時間を返す
@app.route('/get_time')
def get_time():
    if timer_start is None:
        return jsonify({"time_left": 0})
    #経過時間の計算
    elapsed = time.time() - timer_start
    #残り時間の計算，秒に丸め　time()はデフォで秒数数え
    time_left = max(timer_duration - elapsed, 0)
    return jsonify({"time_left": round(time_left, 1)})


@app.route('/everyminute')
def everyminute():
    global GoOffTime
    global user_id

    CurrentTime = str(datetime.datetime.now().strftime(s_format))[11:]
    print("GoOffTime: ", GoOffTime)
    print("CurrentTime: ", CurrentTime)

    if(GoOffTime == CurrentTime):
        print("Timer went off")
        try:
            messages=message_reply(user_id, received_message = "要約")
        except KeyError:
            print("keyerror")

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Authorization": f"Bearer {CHANNEL_TOKEN}",
        }

        payload = {
            "to": user_id,
            "messages": messages,
        }

        response = requests.post(PUSH_URL, headers=headers, json=payload)

        if response.status_code != 200:
            print("LINE_ERROR")
            print(response.text)
            sys.stdout.flush()
            return jsonify({"status": "error", "detail": response.text}), 500

        return jsonify({"status": "success"}), 200
    
    return jsonify({"flask_timer": "updated"})
#タイマー機能ここまで


#LINEプラットフォームがwebhook URLのサーバにアクセスしたときにこのプログラムがサーバに返す関数
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    events = data.get("events", [])
    if not events:
        return jsonify({"status": "no events"}), 200

    event = events[0]
    global reply_token
    reply_token = event.get("replyToken")
    global user_id
    user_id = event["source"].get("userId")
    

    try:
        received_message = event["message"].get("text")
        messages = message_reply(user_id, received_message)
    except KeyError:
        postback_data = event["postback"].get("data")
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
        print("LINE_ERROR")
        print(response.text)
        sys.stdout.flush()
        return jsonify({"status": "error", "detail": response.text}), 500

    return jsonify({"status": "success"}), 200

#ユーザーの入力を読み取り，後述の関数を起動
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
        loading_spinner(user_id)
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
    elif received_message == "f":
        with open(os.path.join(os.path.dirname(__file__), "Addresslist.json"), "r") as j:
            flex_message = json.load(j)
            messages = [
                {
                    "type": "flex",
                    "altText": "メール詳細",
                    "contents": flex_message,
                }
            ]
    elif received_message == "以上":
        #一時ファイルに退避
        global blacklist
        blacklist_send=blacklist
        messages =[
            {
                "type": "text",
                "text": str(blacklist_send),
            }
        ]
        #blacklist初期化
        blacklist=[]
    elif received_message == "version":
        messages = [
            {
                "type": "text",
                "text": "welcome to KFch",
            }
        ]
    else:
        # get 
        messages = free_message(received_message, user_id)

    return messages

def postback_reply(user_id, postback_data:str):
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
    elif postback_data.startswith("address"):
        global blacklist
        data=postback_data.split("=")[1]
        blacklist.append(data)
        messages=1
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
            "layout": "horizontal",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "height": "sm",
                    "action": {
                        "type": "postback",
                        "label": "返信",
                        "data": f"action=reply%{msg_id}"
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
                        "data": f"action=read%{msg_id}"
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
            "msg_id": msg_id,
            "line_id": user_id
        }
        response = requests.get(url, params=params)
        data = response.json()
        return [{"type": "text", "text": "既読にしました"}]
    elif action == "Glink":
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
                        "data": f"msg_id={msg_id}"
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
                        "data": f"spaction=read_all%{','.join(msg_ids)}"
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
    app.run(debug=True, host="0.0.0.0", port=8000)
