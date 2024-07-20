def ads_message():
    # video source from https://i.ytimg.com/an_webp/esYojk39qgQ/mqdefault_6s.webp?du=3000&sqp=COCt7bQG&rs=AOn4CLAti_qXNC2TFeW0SF7x-1VBt7_eGA
    bubble = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": "https://i.ytimg.com/an_webp/esYojk39qgQ/mqdefault_6s.webp?du=3000&sqp=COCt7bQG&rs=AOn4CLAti_qXNC2TFeW0SF7x-1VBt7_eGA",
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
            "action": {
                "type": "uri",
                "uri": "https://www.agaskin.net/clinic/"
            }
        },
    }

    message = {
        "type": "flex",
        "altText": "This is a Flex Message",
        "contents": bubble
    }

    return [message]

