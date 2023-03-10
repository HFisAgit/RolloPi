# Abhänigkeiten
# pip install suncalc

import json
import time
import subprocess
import os

from suncalc import get_position, get_times
from datetime import datetime, timedelta
from time import mktime


def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
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

print('Hello World!')

# initialisire Program
#path_regeln = '/home/pi/gitRepos/RolloPi/regeln.json'
#path_regeln = '/var/www/html/RolloPi/regeln.json'
path_regeln = './regeln.json'
#path_sonne = '/home/harald/daten/BackupUSB/fries/suntimes'
#path_rolladoino = '/home/harald/daten/BackupUSB/fries/Rolladoino.py'
path_rolladoino = '/home/harald/daten/BackupUSB/fries/Simulator.py'
heuteSchonZeitenAktualisiert = False
# https://www.latlong.net/
lon = 8.502633
lat = 49.831873

#sunset
#sunrise


# lade regeln.json
f = open(path_regeln,)

# parse json
data = json.load(f)

f.close()
print(type(data))
timestring = data["morgens"]["early"]
print(timestring)
zeit = stringToTime(timestring)
print(zeit)
delta_time = timedelta(seconds=5)

# starte schleife
#while heuteSchonZeitenAktualisiert == False:
while True:
    # hole aktuelle Zeit
    #startzeit = datetime.now(datetime.timezone.utc)
    startzeit = datetime.now()

    # reset heuteSchonZeitenAktualisiert wenn ein neuer Tag anbricht.
    if( startzeit.hour == 0 & startzeit.minute == 0  & startzeit.second < 15 ):
        heuteSchonZeitenAktualisiert = False

    # prüfe, ob heute schon die Sonnen auf und Untergangszeiten geholt wprden
    if heuteSchonZeitenAktualisiert == False:
        # hole Zeiten, wenn nötig
        _times = get_times(startzeit, lon, lat, 0, [(-0.833, 'sunrise', 'sunset')])
        sunrise = _times["sunrise"]
        sunset = _times["sunset"]
        heuteSchonZeitenAktualisiert = True 

    # prüfe regel 1 Rolladen hoch
    # Was will ich Wissen? Muss ich den Rolladen jetzt hoch fahren?
    # 1. ist es nach frühestens && Sonnenaufgang -> ja
    # 2. ist es spätestens -> ja
    morgensfrueh = stringToTime(data['morgens']['early'])
    morgensspaet = stringToTime(data['morgens']['late'])
    
    if (startzeit.time() > morgensfrueh and is_time_between(startzeit, startzeit + delta_time, sunrise)) or \
        (is_time_between(startzeit.time(), (startzeit + delta_time).time(), morgensspaet)):
        os.system('./Rolladoino.py 0x0c CMD_Rolladen_Hoch')
        os.system('./Rolladoino.py 0x0d CMD_Rolladen_Hoch')
        os.system('./Rolladoino.py 0x0f CMD_Rolladen_Hoch')
        os.system('./Rolladoino.py 0x1f CMD_Rolladen_Hoch')

    # prüfe regel 2 Rolladen runte
    # 1. ist es nach früh && sonnenuntergang -> ja
    # 2. ist es spättestens -> ja
    abendsfrueh = stringToTime(data['abends']['early'])
    abendsspaet = stringToTime(data['abends']['late'])
    
    if (startzeit.time() > abendsfrueh and is_time_between(startzeit, startzeit + delta_time, sunset)) or \
        (is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsspaet)):
        os.system('./Rolladoino.py 0x0c CMD_Rolladen_Runter')
        os.system('./Rolladoino.py 0x0d CMD_Rolladen_Runter')
        os.system('./Rolladoino.py 0x0f CMD_Rolladen_Runter')
        os.system('./Rolladoino.py 0x1f CMD_Rolladen_Runter')
        
    # prüfe regel 3 sonne runter
    sonnenschutz = data['sonne']['ein']
    sonnerunter = data['sonne']['runter']
    sonnehoch = data['sonne']['hoch']

    if (sonnenschutz == "true" or sonnenschutz == "True" or sonnenschutz == "TRUE") and \
        (is_time_between(startzeit.time(), (startzeit + delta_time).time(), sonnerunter)):
        os.system('./Rolladoino.py 0x0c CMD_Rolladen_Runter')
    
    # prüfe regel 3 Sonne hoch
    if (sonnenschutz == "true" or sonnenschutz == "True" or sonnenschutz == "TRUE") and \
        (is_time_between(startzeit.time(), (startzeit + delta_time).time(), sonnehoch)):
        os.system('./Rolladoino.py 0x0c CMD_Rolladen_Hoch')
    
    # prüfe regel 5 lüfter
    luefter = data['luftreduziert']
    if (luefter == "true" or luefter == "True" or luefter == "TRUE") and \
        ( startzeit.minute == 0 and startzeit.second == delta_time.seconds and startzeit.hour % 2 == 0):
        os.system('./Rolladoino.py 0x0d CMD_Luefter 0')
        os.system('./Rolladoino.py 0x0f CMD_Luefter 0')

    if (luefter == "true" or luefter == "True" or luefter == "TRUE") and \
        ( startzeit.minute == 0 and startzeit.second == delta_time.seconds and startzeit.hour % 2 == 1):
        os.system('./Rolladoino.py 0x0d CMD_Luefter 1')
        os.system('./Rolladoino.py 0x0f CMD_Luefter 1')

    # hole neuen Zeitstempel
    endzeit = datetime.now()

    # berechne wartezeit bis zum nächsten schleifendurchlauf
    sleeptime = startzeit + delta_time - endzeit

    # sleep
    if (sleeptime.total_seconds() > 0):
        time.sleep(sleeptime.total_seconds())
        print(sleeptime.total_seconds())
    else:
        print("Error in sleeptime calculation")
        print(sleeptime.total_seconds())
        time.sleep(1)
# ende Schleife

print('end of program')
