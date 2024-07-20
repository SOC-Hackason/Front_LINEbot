import random

def ads_message():
    # video source from 

    if random.randint(0, 1) == 0:
        url = "https://mails.amano.mydns.jp/static/valorant.mp4"
        preurl = "https://mails.amano.mydns.jp/static/valorant.jpg"
        jump_url = "https://playvalorant.com/ja-jp/"
    else:
        url = "https://mails.amano.mydns.jp/static/cats.mp4"
        preurl = "https://mails.amano.mydns.jp/static/cats.png"
        jump_url = "https://catmocha.jp/"
        
    bubble = {
        "type": "bubble",
        "size": "kilo",
        "hero": {
            "type": "video",
            "url": url,
            "previewUrl": preurl,
            "action": {
                "type": "uri",
                "uri": jump_url,
                "label": "jump"
            },
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
    }

    message = {
        "type": "flex",
        "altText": "This is a Flex Message",
        "contents": bubble
    }

    return [message]

