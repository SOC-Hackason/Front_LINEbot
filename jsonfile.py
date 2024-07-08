import json
import os
with open(os.path.join(os.path.dirname(__file__), "flex.json")) as j:
    jsonfile=json.load(j)
    print(jsonfile)