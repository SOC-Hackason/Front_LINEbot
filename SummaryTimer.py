import datetime as dt
import time as t
import os
import requests
"""
from main import summary_message, summary_reply, loading_spinner
from dotenv import load_dotenv


load_dotenv()
CHANNEL_TOKEN = os.getenv("CHANNEL_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
REPLY_URL = os.getenv("REPLY_URL")
ADD_BP = os.getenv("ADD_BP")

"""



#test
GoOffTime=dt.datetime(2024, 7, 12, 22, 10)

          

#timer(GoOffTime)

def summary_timer(update_timestep):
    print("summary timer started")
    stopupdate=False
    while stopupdate == False:
          t.sleep(update_timestep)
          CurrentTime=dt.datetime.now()
          if CurrentTime > GoOffTime:
               stopupdate=True
               print("stopped update")
    
    print("exited loop")
    with open (os.path.join(os.path.dirname(__file__), "lineid.txt"), "w") as file:
                    file.write("Timer went off")         


"""
def timer(GoOffTime):
    CurrentTime=dt.datetime.now()
    if CurrentTime > GoOffTime:
        
        #loading_spinner(user_id)
        #summary_message(user_id)
        #messages = summary_reply(user_id)
        messages="a"
        headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "Authorization": f"Bearer {CHANNEL_TOKEN}",
            }

        payload = {
                #"replyToken": reply_token,
                "messages": messages,
            }

        response = requests.post(REPLY_URL, headers=headers, json=payload)
        """
