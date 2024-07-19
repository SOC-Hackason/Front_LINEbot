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
                "backgroundColor": "#f0f8ff",
                "separator": True,
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
                },
            ]
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
                            "style": "secondary",
                            "height": "sm",
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