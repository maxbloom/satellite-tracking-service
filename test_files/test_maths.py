from datetime import datetime
from time import time
import calendar

t = "11-5-2018 00:00:00"
dtDate = datetime.strptime(t, "%m-%d-%Y %H:%M:%S")
# print(dtDate)

# print(time())

now_time_sec = datetime.now()
print(now_time_sec)

zz = datetime(2014, 1, 18, 1, 35, 37, 500000)
# print(zz)


dtDate1 = datetime.strftime(dtDate, "%Y-%m-%d %H:%M:%S")
# print(dtDate1)

timestamp1 = calendar.timegm(dtDate.timetuple())
rr = datetime.utcfromtimestamp(timestamp1)
# print(dtDate.timetuple())
# print(timestamp1)


datetime_object = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
# print(datetime_object)