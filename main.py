from flask import Flask
from app.env import *
from app import deploy

app = Flask(__name__)
app.register_blueprint(deploy.bp)

@app.route("/")
def hello():
    return "hello world"


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    events = data.get('events', [])
    if not events:
        return jsonify({'status': 'no events'}), 400

    event = events[0]
    reply_token = event.get('replyToken')
    received_message = event['message'].get('text')
    user_id = event['source'].get('userId')

    if not reply_token:
        return jsonify({'status': 'no reply token'}), 400

    if received_message == '認証':
        messages = [{
            'type': 'text',
            'text': f"https://mails.amano.mydns.jp/gmail/auth?openExternalBrowser=1&clientid={user_id}",
        }]
    elif received_message == '要約':
        res = requests.get(f"https://mails.amano.mydns.jp/gmail/emails/summary?line_id={user_id}")
        response_text = res.text
        messages = [{
            'type': 'text',
            'text': response_text,
        }]
    elif received_message == "version":
        messages = [{
            'type': 'text',
            'text': "2:32",
        }]
    else:
        messages = [{
            'type': 'text',
            'text': f"{received_message}{received_message}ama",
        }]

    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'Authorization': f'Bearer {CHANNEL_TOKEN}',
    }

    payload = {
        'replyToken': reply_token,
        'messages': messages,
    }

    response = requests.post(REPLY_URL, headers=headers, json=payload)

    if response.status_code != 200:
        return jsonify({'status': 'error', 'detail': response.text}), 500

    return jsonify({'status': 'success'}), 200


if __name__ == "__main__":
    app.run(debug = True, host='0.0.0.0', port=49515)
