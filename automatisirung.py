# Abhänigkeiten
# pip install suncalc

import json
from datetime import datetime
import subprocess
import os

from suncalc import get_position, get_times
from datetime import datetime


def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time


print('Hello World!')

# initialisire Program
path_regeln = '/var/www/html/php-kontaktbuch/regeln.json'
path_sonne = '/home/harald/daten/BackupUSB/fries/suntimes'
path_rolladoino = '/home/harald/daten/BackupUSB/fries/Rolladoino.py'
heuteSchonSonnenaufgang = False
# https://www.latlong.net/
lon = 8.502633
lat = 49.831873

sunset
sunrise


# lade regeln.json
f = open(path_regeln,)

# parse json
data = json.load(f)

f.close()

# starte schleife
while heuteSchonSonnenaufgang == False:
    # hole aktuelle Zeit
    startzeit = datetime.now(datetime.timezone.utc)
    print(startzeit)

    # reset heuteschonSonnenaufgang wenn ein neuer Tag anbricht.
    if( startzeit.hour == 0 & startzeit.minute == 0  & startzeit.second < 15 ):
        heuteSchonSonnenaufgang = False

    # prüfe, ob heute schon die Sonnen auf und Untergangszeiten geholt wprden
    if heuteSchonSonnenaufgang == False:
        # hole Zeiten, wenn nötig
        times = get_times(startzeit, lon, lat, 0, [(-0.833, 'sunrise', 'sunset')])
        sunrise = times["sunrise"]
        sunset = times["sunset"]
        heuteSchonSonnenaufgang = True

    # prüfe regel 1 Rolladen hoch
    if is_time_between(startzeit, startzeit + 10, sunrise):
        os.system('./Rolladoino.py 0x0c CMD_Rolladen_Hoch')
        os.system('./Rolladoino.py 0x0d CMD_Rolladen_Hoch')
        os.system('./Rolladoino.py 0x0f CMD_Rolladen_Hoch')
        os.system('./Rolladoino.py 0x1f CMD_Rolladen_Hoch')

    # prüfe regel 2 Rolladen runter
    if is_time_between(startzeit, startzeit + 10, sunset):
        os.system('./Rolladoino.py 0x0c CMD_Rolladen_Runter')
        os.system('./Rolladoino.py 0x0d CMD_Rolladen_Runter')
        os.system('./Rolladoino.py 0x0f CMD_Rolladen_Runter')
        os.system('./Rolladoino.py 0x1f CMD_Rolladen_Runter')
        
    # prüfe regel 3 sonne runter
    if 
    # prüfe regel 3 Sonne hoch

    # prüfe regel 5 lüfter

    # hole neuen Zeitstempel
    endzeit = datetime.now()

    # berechne wartezeit bis zum nächsten schleifendurchlauf

    # sleep
# ende Schleife