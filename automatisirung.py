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
    print('fkt_stringToTime')
    print(timestring)
    st_time = time.strptime(timestring, '%H:%M:%S')
    dt = datetime.fromtimestamp(mktime(st_time))
    return dt.time()

print('Hello World!')

struct_time = time.strptime("7:03:45", '%H:%M:%S')
print(struct_time)

# initialisire Program
path_regeln = '/home/pi/gitRepos/RolloPi/regeln.json'
#path_regeln = '/var/www/html/RolloPi/regeln.json'
#path_sonne = '/home/harald/daten/BackupUSB/fries/suntimes'
path_rolladoino = '/home/harald/daten/BackupUSB/fries/Rolladoino.py'
heuteSchonSonnenaufgang = False
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
print(type(data["morgens"]["late"]))
zeit = stringToTime(data["morgens"]["early"])
print(zeit)
delta_time = timedelta(seconds=1)

# starte schleife
while heuteSchonSonnenaufgang == False:
    # hole aktuelle Zeit
    #startzeit = datetime.now(datetime.timezone.utc)
    startzeit = datetime.now()
    print(startzeit)

    # reset heuteschonSonnenaufgang wenn ein neuer Tag anbricht.
    if( startzeit.hour == 0 & startzeit.minute == 0  & startzeit.second < 15 ):
        heuteSchonSonnenaufgang = False

    # prüfe, ob heute schon die Sonnen auf und Untergangszeiten geholt wprden
    if heuteSchonSonnenaufgang == False:
        # hole Zeiten, wenn nötig
        _times = get_times(startzeit, lon, lat, 0, [(-0.833, 'sunrise', 'sunset')])
        sunrise = _times["sunrise"]
        sunset = _times["sunset"]
        heuteSchonSonnenaufgang = True

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
    time.sleep(sleeptime.total_seconds())
    
# ende Schleife
