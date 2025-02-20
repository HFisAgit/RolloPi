# Abhänigkeiten
# pip install suncalc

import json
import time
import subprocess
import os
import drivers.ads1115 as ads1115
import drivers.Rolladoino as Rolladoino

from suncalc import get_position, get_times
from datetime import datetime, timedelta
from time import mktime
from dateutil import tz



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

def loadRegeln():
    f = open(path_regeln,)
    # parse json
    data = json.load(f)
    f.close()

def datetime2local(dto:datetime, s_tz: str='Europe/Berlin'):
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(s_tz)
    _local = dto.replace(tzinfo=from_zone)
    # and convert to local time
    return _local.astimezone(to_zone)

# Funktion zum Steuern der Lüfter
# time can be 'sunset' or 'dusk'
def control_shutter(time, pos):
    for device in config['devices'][time]:
        if pos == "hoch":
            Rolladoino.main('CMD_Rolladen_Hoch', device['channel'], device['address'])
        elif pos == "runter":
            Rolladoino.main('CMD_Rolladen_Runter', device['channel'], device['address'])
        time.sleep(1)


# global vars
clearReloadFile = False

# initialisire Program
path_regeln = './regeln.json'
config_path = 'rolladenAddr.json'
path_log = './automatisierung.log'
path_reloadRegeln = './reloadRegeln.txt'
path_rolladoino = './drivers/Rolladoino.py'
#path_rolladoino = '/home/harald/daten/BackupUSB/fries/Simulator.py'

heuteSchonZeitenAktualisiert = False
 
# https://www.latlong.net/
lon = 8.504561
lat = 49.809986

# lade regeln.json
#data = []
#loadRegeln()
with open(path_regeln, 'r') as regelnFile:
    data = json.load(regelnFile)


# Konfiguration laden
with open(config_path, 'r') as f:
    config = json.load(f)


delta_time = timedelta(seconds=10)
        
#starte schleife
#while heuteSchonZeitenAktualisiert == False:
while True:
    # hole aktuelle Zeit
    startzeitutc = datetime.utcnow() # deprecated ...
    #startzeitutc = time.time().now(datetime.timezone.utc) # new variant
    startzeit = datetime.now() # local time

    # check if reload of regeln is triggered
    with open(path_reloadRegeln, 'r') as fr:
        if("true" == fr.readline()):
            with open(path_regeln, 'r') as regelnFile:
                data = json.load(regelnFile)
            clearReloadFile = True
    
    # clear 
    if(clearReloadFile):
        with open(path_reloadRegeln, 'w') as fw:
            fw.write(" ")
            clearReloadFile = False


    # reset heuteSchonZeitenAktualisiert wenn ein neuer Tag anbricht.
    # Nachts um vier, für den Fall, dass Sommerzeit anfängt oder endet. 
    if( startzeit.hour == 4 & startzeit.minute == 0  & startzeit.second < 15 ):
        heuteSchonZeitenAktualisiert = False

    # prüfe, ob heute schon die Sonnen auf und Untergangszeiten geholt wprden
    if heuteSchonZeitenAktualisiert == False:
        # hole Zeiten, wenn nötig
        print("Neue Sonnen auf/unterganz Zeiten.")
        _times = get_times(startzeitutc, lon, lat)
        # and convert to local time
        for x in _times:
            _times[x] = datetime2local(_times[x])

        dawn_time = _times["dawn"]
        dusk_time = _times["dusk"]
        sunset_time = _times['sunset']
        heuteSchonZeitenAktualisiert = True 

        # zeiten für Anzeige exportiere
        s_sunrise = _times["sunrise"].isoformat()
        s_sunset  = _times["sunset"].isoformat()
        sunriseCropIndex = s_sunrise.rfind(".")
        sunsetCropIndex = s_sunset.rfind(".")
        suntimes = {
            "date": startzeit.date().isoformat(),
            "sunrise": s_sunrise[:sunriseCropIndex],
            "sunset": s_sunset[:sunsetCropIndex]
        }
        with open('suntimes.json', 'w') as f:
            json.dump(suntimes, f)
    
    # prüfe regel 1 Rolladen hoch
    # Was will ich Wissen? Muss ich den Rolladen jetzt hoch fahren?
    # 1. ist es frühestens und nach sonnenaufgang -> ja
    # 2. ist es nach frühestens && Sonnenaufgang -> ja
    # 3. ist es spätestens -> ja
    morgensfrueh = stringToTime(data['morgens']['early']) #time
    morgensspaet = stringToTime(data['morgens']['late']) #time
    
    sunriseBefore = is_time_between( startzeit.time(), (startzeit + delta_time).time(), morgensfrueh )   and dawn_time.time() <= startzeit.time()
    surriseBetwen = is_time_between( startzeit.time(), (startzeit + delta_time).time(), dawn_time.time() ) and morgensfrueh   < startzeit.time()
    sunriseAfter =  is_time_between( startzeit.time(), (startzeit + delta_time).time(), morgensspaet )

    if ( sunriseBefore or surriseBetwen or sunriseAfter ):
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + " Rolladen hoch" + '\n')
        # wir fahren alle Rolläden. die Zeitinformation ist nur bein Runterfahren relevant.
        control_shutter('dusk', 'hoch')
        control_shutter('sunset', 'hoch')

    # prüfe regel 2 Rolladen runter Straße - dusk ist die spätere Zeit
    # 1. ist es früh- und nach sonnenuntergang -> ja
    # 2. ist es nach früh && sonnenuntergang -> ja
    # 3. ist es spättestens -> ja
    abendsfrueh = stringToTime(data['abends']['early'])
    abendsspaet = stringToTime(data['abends']['late'])
    
    duskBefore  = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsfrueh)    and dusk_time.time() <= startzeit.time()
    duskBetween = is_time_between(startzeit.time(), (startzeit + delta_time).time(), dusk_time.time() ) and abendsfrueh < startzeit.time()
    duskAfter   = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsspaet)

    if ( duskBefore or duskBetween or duskAfter ):
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + " Rolladen runter Straße" + '\n')
        control_shutter('dusk', 'runter')
    
    # prüfe regel 2 Rolladen runter Garten - sunset ist die frühere Zeit
    # 1. ist es früh- und nach sonnenuntergang -> ja
    # 2. ist es nach früh && sonnenuntergang -> ja
    # 3. ist es spättestens -> ja
    sunsetBefore  = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsfrueh)    and sunset_time.time() <= startzeit.time()
    sunsetBetween = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sunset_time.time() ) and abendsfrueh < startzeit.time()
    sunsetAfter   = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsspaet)

    if ( sunsetBefore or sunsetBetween or sunsetAfter ):
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + " Rolladen runter Garten" + '\n')
        control_shutter('sunset', 'runter')
        

    # prüfe regel 3 sonne runter
    sonnenschutz = data['sonne']['ein']
    sonnerunter = stringToTime(data['sonne']['runter'])
    sonnehoch = stringToTime(data['sonne']['hoch'])

    isSonnenschutzActive = sonnenschutz == "true" or sonnenschutz == "True" or sonnenschutz == "TRUE"
    isSonneRunter = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sonnerunter)
    isSonneHoch = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sonnehoch)

    if (isSonnenschutzActive and isSonneRunter):
        control_shutter('dusk', 'runter')
    
    # prüfe regel 3 Sonne hoch
    if (isSonnenschutzActive and isSonneHoch):
        control_shutter('dusk', 'hoch')
    
    #########################################################################################
    # hole neuen Zeitstempel
    endzeit = datetime.now()

    # berechne wartezeit bis zum nächsten schleifendurchlauf
    sleeptime = startzeit + delta_time - endzeit

    # sleep
    if (sleeptime.total_seconds() > 0):
        time.sleep(sleeptime.total_seconds())
    else:
        print("Warning: loop takes longer then time_delta!")
        print(sleeptime.total_seconds())
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + "Warning: loop takes longer then time_delta!" + '\n')
        time.sleep(1)
# ende Schleife

print('end of program')
