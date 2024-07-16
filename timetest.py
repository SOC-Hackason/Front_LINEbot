import datetime

s = '2023/4/1 20:30'
s_format = '%Y/%m/%d %H:%M'
GoOffTime= str(datetime.datetime.strptime(s, s_format))[11:-3]
CurrentTime = str(datetime.datetime.now().strftime(s_format))[11:]
print(GoOffTime, CurrentTime)