# Abhänigkeiten
# pip install suncalc

import json
import time
import subprocess
import os

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

# global vars
clearReloadFile = False

# define addresses
addrKueche = '0x0d'
addrWc = '0x0f'
addrWohnz = '0x0b'
addrTerrasse = '0x0c'

# initialisire Program
path_regeln = './regeln.json'
#path_rolladoino = '/home/pi/RolloPi/Rolladoino.py'
#path_log = '/home/pi/RolloPi/automatisierung.log'
#path_reloadRegeln = '/home/pi/RolloPi/reloadRegeln.txt'
path_rolladoino = './Rolladoino.py'
path_log = './automatisierung.log'
path_reloadRegeln = './reloadRegeln.txt'
#path_rolladoino = '/home/harald/daten/BackupUSB/fries/Simulator.py'

heuteSchonZeitenAktualisiert = False

# https://www.latlong.net/
lon = 8.502633
lat = 49.831873

# lade regeln.json
#data = []
#loadRegeln()

with open(path_regeln, 'r') as regelnFile:
    data = json.load(regelnFile)


#print(type(data))
#timestring = data["morgens"]["early"]
#print(timestring)
#zeit = stringToTime(timestring)
#print(zeit)
delta_time = timedelta(seconds=10)
        
#starte schleife
#while heuteSchonZeitenAktualisiert == False:
while True:
    # hole aktuelle Zeit
    startzeitutc = datetime.utcnow()
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
        #_times = get_times(startzeitutc, lon, lat, 0, [(-0.833, 'sunrise', 'sunset')])
        _times = get_times(startzeitutc, lon, lat)
        # times are in UTC but without timezoneinfo (native)
        # so: add UTC time zone info
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('Europe/Berlin')
        _times["dawn"] = _times["dawn"].replace(tzinfo=from_zone)
        _times["dusk"] = _times["dusk"].replace(tzinfo=from_zone)
        # and convert to local time
        sunrise = _times["dawn"].astimezone(to_zone)
        sunset = _times["dusk"].astimezone(to_zone)
        heuteSchonZeitenAktualisiert = True 
        # zeiten für Anzeige exportiere
        s_sunrise = (_times["dawn"].astimezone(to_zone)).time().isoformat();
        s_sunset  = (_times["dusk"].astimezone(to_zone)).time().isoformat();
        sunriseCropIndex = s_sunrise.rfind(".");
        sunsetCropIndex = s_sunset.rfind(".");

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
    
    sunriseBefore = is_time_between( startzeit.time(), (startzeit + delta_time).time(), morgensfrueh )   and sunrise.time() <= startzeit.time()
    surriseBetwen = is_time_between( startzeit.time(), (startzeit + delta_time).time(), sunrise.time() ) and morgensfrueh   < startzeit.time()
    sunriseAfter =  is_time_between( startzeit.time(), (startzeit + delta_time).time(), morgensspaet )

    if ( sunriseBefore or surriseBetwen or sunriseAfter ):
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + " Rolladen hoch" + '\n')
        os.system('python2 ' + path_rolladoino + ' ' + addrKueche +' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python2 ' + path_rolladoino + ' ' + addrWc + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python2 ' + path_rolladoino + ' ' + addrWohnz + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python2 ' + path_rolladoino + ' ' + addrTerrasse + ' CMD_Rolladen_Hoch')

    # prüfe regel 2 Rolladen runtr
    # 1. ist es früh- und nach sonnenuntergang -> ja
    # 2. ist es nach früh && sonnenuntergang -> ja
    # 3. ist es spättestens -> ja
    abendsfrueh = stringToTime(data['abends']['early'])
    abendsspaet = stringToTime(data['abends']['late'])
    
    sunsetBefore  = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsfrueh)    and sunset.time() <= startzeit.time()
    sunsetBetween = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sunset.time() ) and abendsfrueh < startzeit.time()
    sunsetAfter   = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsspaet)

    if ( sunsetBefore or sunsetBetween or sunsetAfter ):
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + " Rolladen runter" + '\n')
        os.system('python2 ' + path_rolladoino + ' ' + addrKueche +' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python2 ' + path_rolladoino + ' ' + addrWc + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python2 ' + path_rolladoino + ' ' + addrWohnz + ' CMD_Rolladen_Runter')
        
    # prüfe regel 3 sonne runter
    sonnenschutz = data['sonne']['ein']
    sonnerunter = stringToTime(data['sonne']['runter'])
    sonnehoch = stringToTime(data['sonne']['hoch'])

    isSonnenschutzActive = sonnenschutz == "true" or sonnenschutz == "True" or sonnenschutz == "TRUE"
    isSonneRunter = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sonnerunter)
    isSonneHoch = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sonnehoch)

    if (isSonnenschutzActive and isSonneRunter):
        os.system('python2 ' + path_rolladoino + ' ' + addrWohnz + ' CMD_Rolladen_Runter')
    
    # prüfe regel 3 Sonne hoch
    if (isSonnenschutzActive and isSonneHoch):
        os.system('python2 ' + path_rolladoino + ' ' + addrWohnz + ' CMD_Rolladen_Hoch')
    
    # prüfe regel 5 lüfter
    luefter = data['luftreduziert']

    isLuefterActive = luefter == "true" or luefter == "True" or luefter == "TRUE"
    isHourEven = startzeit.minute == 0 and startzeit.second < delta_time.seconds and (startzeit.hour % 2)-1
    isHourUneven = startzeit.minute == 0 and startzeit.second < delta_time.seconds and startzeit.hour % 2

    if (isLuefterActive and isHourEven == True):
        print('aus')
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + "Luefter aus" + '\n')
        os.system('python2 ' + path_rolladoino + ' ' + addrKueche +' CMD_Luefter 0')
        time.sleep(1)
        os.system('python2 ' + path_rolladoino + ' ' + addrWc + ' CMD_Luefter 0')

    if (isLuefterActive and isHourUneven == True):
        print('an')
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + "Luefter an" + '\n')
        os.system('python2 ' + path_rolladoino + ' ' + addrKueche +' CMD_Luefter 1')
        time.sleep(1)
        os.system('python2 ' + path_rolladoino + ' ' + addrWc + ' CMD_Luefter 1')

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
