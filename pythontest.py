from flask import Flask, render_template, jsonify
import time, datetime
import logging
 
#標準出力に出てくるFlaskのログを出さないようにする
l = logging.getLogger()
l.addHandler( logging.FileHandler( "/nul" ))

app = Flask(__name__)

#スタート時刻と測る時間
timer_start = None
timer_duration = 0

s = '2024/7/16 15:00'
s_format = '%Y/%m/%d %H:%M'
GoOffTime= str(datetime.datetime.strptime(s, s_format))[11:-3]

@app.route('/')
def index():
    return render_template('timerupdater.html')

#タイマーがスタート状態になるjsonを返す
@app.route('/start/<int:seconds>')
def start_timer(seconds):
    global timer_start, timer_duration
    #現在時刻を取得
    timer_start = time.time()
    timer_duration = seconds
    #状態をstartedに変更
    return jsonify({"status": "started"})


#残り時間を返す
@app.route('/get_time')
def get_time():
    if timer_start is None:
        return jsonify({"time_left": 0})
    #経過時間の計算
    elapsed = time.time() - timer_start
    #残り時間の計算，秒に丸め　time()はデフォで秒数数え
    time_left = max(timer_duration - elapsed, 0)
    return jsonify({"time_left": round(time_left, 1)})


@app.route('/everyminute')
def everyminute():
    global GoOffTime
    CurrentTime = str(datetime.datetime.now().strftime(s_format))[11:]
    print("GoOffTime: ", GoOffTime)
    print("CurrentTime: ", CurrentTime)
    if(GoOffTime == CurrentTime):
        print("Timer went off") 
    return jsonify({"timer_update": "done"})




if __name__ == '__main__':
    app.run(debug=True)