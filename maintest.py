from app.env_KF import *
import json, os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, FlexSendMessage, TextSendMessage

app = Flask(__name__)

# LINE Developersで取得したチャンネルアクセストークンとチャンネルシークレット
LINE_CHANNEL_ACCESS_TOKEN = CHANNEL_TOKEN
LINE_CHANNEL_SECRET = CHANNEL_SECRET

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

blocklist=[]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "f":
        #jsonファイルではtrueは小文字
        with open(os.path.join(os.path.dirname(__file__), "Addresslist.json"), "r") as j:
            flex_message = json.load(j)

        flex_message = FlexSendMessage(
            alt_text='Flex Message',
            contents=flex_message
        )

        line_bot_api.reply_message(
            event.reply_token,
            flex_message
        )
    elif event.message.text == "以上":
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=str(blocklist))
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="「f」と入力してください。")
        )

@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    data = event.postback.data
    blocklist.append(data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
