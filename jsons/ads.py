import random

def ads_message():
    # video source from 

    if random.randint(0, 1) == 0:
        url = "https://mails.amano.mydns.jp/media/valorant2.mp4"
        preurl = "https://mails.amano.mydns.jp/media/valorant2.png"
        jump_url = "https://playvalorant.com/ja-jp/"
        ratio = "16:9"
        header = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "あなたもvalorantをプレイしませんか?",
                    "size": "sm",
                    "align": "center",
                    "color": "#FF4657"
                }
            ],
            "backgroundColor": "#000000",
        }
        footer = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "今すぐプレイ",
                        "uri": jump_url
                    },
                    "height": "sm",
                }
            ],
            "backgroundColor": "#ffffff",
            
        }
    else:
        url = "https://mails.amano.mydns.jp/media/cats2.mp4"
        preurl = "https://mails.amano.mydns.jp/media/cats.png"
        jump_url = "https://catmocha.jp/"
        ratio = "640:338"
        header = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "おつかれですね。猫カフェに行きませんか?",
                    "size": "sm",
                    "align": "center",
                    "color": "#000000"
                }
            ],
            "backgroundColor": "#ffffff",
        }
        footer = {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "猫カフェへ",
                        "uri": jump_url
                    },
                    "height": "sm",
                }
            ],
            "backgroundColor": "#C7BDB1",
        }
        
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "header": header,
        "hero": {
            "type": "video",
            "url": url,
            "previewUrl": preurl,
            "action": {
                "type": "uri",
                "uri": jump_url,
                "label": "jump"
            },
            "aspectRatio": ratio,
            "altContent": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "Click here to jump",
                        "align": "center",
                        "color": "#ffffff"
                    }
                ]
            }
        },
        "footer": footer
    }

    message = {
        "type": "flex",
        "altText": "This is ads message",
        "contents": bubble
    }

    return [message]
