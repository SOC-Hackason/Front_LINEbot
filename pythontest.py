from flask import Flask
import asyncio


from flask import Flask, render_template, jsonify
import time

app = Flask(__name__)

timer_start = None
timer_duration = 0

@app.route('/')
def index():
    return render_template('timerupdater.html')

@app.route('/start/<int:seconds>')
def start_timer(seconds):
    global timer_start, timer_duration
    timer_start = time.time()
    timer_duration = seconds
    return jsonify({"status": "started"})

@app.route('/get_time')
def get_time():
    if timer_start is None:
        return jsonify({"time_left": 0})
    
    elapsed = time.time() - timer_start
    time_left = max(timer_duration - elapsed, 0)
    return jsonify({"time_left": round(time_left, 1)})

if __name__ == '__main__':
    app.run(debug=True)

"""
async def start_timer():
    print("starting timer")
    task = asyncio.create_task(main())
    await asyncio.sleep(10)
    print("a")

async def main():
        print("starting flask")
        app = Flask(__name__)

        @app.route("/")
        def hello():
                return("Hello")

        if __name__ == "__main__":
                app.run(debug=True)

# イベントループを開始
asyncio.run(start_timer())
"""