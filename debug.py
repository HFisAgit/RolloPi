
import json
import time
import subprocess
import os

from suncalc import get_position, get_times
from datetime import datetime, timedelta
from time import mktime


def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
  #  check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

def stringToTime(timestring):
    # raspberry pi can not work with date 1900! so we need to set the year....
    inputstr = "2000 "
    inputstr += timestring
    st_time = time.strptime(inputstr, '%Y %H:%M:%S')
    dt = datetime.fromtimestamp(mktime(st_time))
    return dt.time()

path_regeln = './regeln.json'
path_rolladoino = '/home/pi/RolloPi/Rolladoino.py'

# https://www.latlong.net/
lon = 8.502633
lat = 49.831873

startzeit = datetime(2022, 3, 21, 17, 59, 58, 0)

_times = get_times(startzeit, lon, lat, 0, [(-0.833, 'sunrise', 'sunset')])
sunrise = _times["sunrise"]
sunset = _times["sunset"]

delta_time = timedelta(seconds=10)

# lade regeln.json
f = open(path_regeln,)

# parse json
data = json.load(f)

f.close()

morgensfrueh = stringToTime(data['morgens']['early']) #time
morgensspaet = stringToTime(data['morgens']['late']) #time

sunriseBefore = is_time_between( startzeit.time(), (startzeit + delta_time).time(), morgensfrueh )   and sunrise.time() <= startzeit.time()
surriseBetwen = is_time_between( startzeit.time(), (startzeit + delta_time).time(), sunrise.time() ) and morgensfrueh   < startzeit.time()
sunriseAfter =  is_time_between( startzeit.time(), (startzeit + delta_time).time(), morgensspaet )


print(startzeit.time())
print((startzeit + delta_time).time())
print(morgensfrueh)
print(is_time_between( startzeit.time(), (startzeit + delta_time).time(), morgensfrueh ))

print(sunriseBefore)
print(surriseBetwen)
print(sunriseAfter)

print("-----------------")

abendsfrueh = stringToTime(data['abends']['early'])
abendsspaet = stringToTime(data['abends']['late'])
    
sunsetBefore  = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsfrueh)    and sunset.time() <= startzeit.time()
sunsetBetween = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sunset.time() ) and abendsfrueh < startzeit.time()
sunsetAfter   = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsspaet)

print(sunsetBefore)
print(sunsetBetween)
print(sunsetAfter)

print(path_rolladoino  + ' 0x0c CMD_Rolladen_Runter')
