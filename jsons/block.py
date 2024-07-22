import requests

def recent_address(addresses, unblock=False):

    """
    最近届いたメールアドレスのリストの表示
    """
    _addresses = list(map(lambda x: x.split("<")[1], addresses))
    _addresses = list(map(lambda x: x.split(">")[0], _addresses))
    addresses = list(map(lambda x: x.split("<")[0], addresses))
    if unblock:
        blk = "unblock"
        txt = "Block List"
    else:
        blk = "block"
        txt = "最近届いたメールアドレス"

    bubble = {
        "type": "bubble",
        "styles": {
            "body": {
                "separator": False,
                "separatorColor": "#000000",
            }
        },
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": f"{txt}",
                    "weight": "bold",
                    "size": "xl",
                    "margin": "xs",
                    "align": "center"
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
                            "text": f"{address}",
                            "size": "sm",
                            "align": "start",
                            "wrap": False,
                            "flex": 5,
                            "gravity": "center"
                        },
                        {
                            "type": "button",
                            "action": {
                                "type": "postback",
                                "label": f"{blk}",
                                "data": f"{blk}={_addresses[i]}&{address}",
                                "displayText": f"{blk} {address}"
                            },
                            "style": "primary",
                            "height": "sm",
                            "color": "#673B4D",
                            "flex": 3,
                        }
                    ]
                } if j == 0 else {
                    "type": "separator",
                    "margin": "md",
                    "color": "#ffffff"
                }
                for i, address in enumerate(addresses)
                for j in range(2)
            ]
        }
    }
    message = {
        "type": "flex",
        "altText": "最近届いたメールアドレス",
        "contents": bubble
    }

    return [message]

def block_unblock_message():
    bubble = {
        "type": "bubble",
        "styles": {
            "body": {
                "separator": False,
                "separatorColor": "#000000",
            }
        },
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "Block or Unblock",
                    "weight": "bold",
                    "size": "xl",
                    "margin": "xs",
                    "align": "center"
                },
            ],
            "backgroundColor": "#EEEEEE",
            "paddingAll": "md",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "Block",
                        "data": "before_block",
                        "displayText": "最近のアドレスを表示します"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "margin": "none",
                },
                {
                    "type": "button",
                    "action": {
                        "type": "postback",
                        "label": "Unblock",
                        "data": "list_block",
                        "displayText": "ブロックリストを表示します"
                    },
                    "style": "secondary",
                    "height": "sm",
                    "margin": "lg",
                }
            ]
        }
    }

    message = {
        "type": "flex",
        "altText": "Block or Unblock",
        "contents": bubble
    }

    return [message]

def language_setting():
    # quick message japanese, english, chinese, korean, french, spanish, german, italian, portuguese
    languages = ["日本語", "English", "中文", "한국어", "Français", "Español", "Deutsch", "Italiano", "Português"]
    languages_in_english = ["Japanese", "English", "Chinese", "Korean", "French", "Spanish", "German", "Italian", "Portuguese"]
    items = [
        {
            "type": "action",
            "action": {
                "type": "postback",
                "label": lang,
                "data": f"lang={lang_}"
            }
        } for lang, lang_ in zip(languages, languages_in_english)
    ]

    message = {
        "type": "text",
        "text": "言語設定",
        "quickReply": {
            "items": items
        }
    }

    return [message]

def set_language(line_id, lang):

    url = "https://mails.amano.mydns.jp/gmail/change_language"
    params = {
        "line_id": line_id,
        "language": lang
    }

    res = requests.get(url, params=params)
    data = res.json()
    message  = {
        "type": "text",
        "text": f"言語設定を{lang}に変更しました"
    }
    return [message]