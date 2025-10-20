# Abhänigkeiten

import json
import time
import subprocess
import os
import drivers.ads1115 as ads1115
import drivers.Rolladoino as Rolladoino

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
def control_fans(stufe):
    for device in config['devices']:
        Rolladoino.main('CMD_Luefter', device['channel'], device['address'], stufe)
        time.sleep(1)


# global vars
clearReloadFile = False

# initialisire Program
path_regeln = './regeln.json'
path_log = './luft_automatisierung.log'
path_reloadRegeln = './ramdisk/reloadRegeln.txt'
path_rolladoino = './drivers/Rolladoino.py'
config_path = 'luefterAddr.json'
#path_rolladoino = '/home/harald/daten/BackupUSB/fries/Simulator.py'

# lade regeln.json
with open(path_regeln, 'r') as regelnFile:
    data = json.load(regelnFile)

# Konfiguration laden
with open(config_path, 'r') as f:
    config = json.load(f)

delta_time = timedelta(seconds=10)
        
# --- starte schleife ---
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


    # prüfe regel lüfter
    luefter = data['luftreduziert']

    isLuefterActive = luefter == "true" or luefter == "True" or luefter == "TRUE"
    isHourEven = startzeit.minute == 0 and startzeit.second < delta_time.seconds and (startzeit.hour % 2)-1
    isHourUneven = startzeit.minute == 0 and startzeit.second < delta_time.seconds and startzeit.hour % 2

    if (isLuefterActive and isHourEven == True):
        print('aus')
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + "Luefter aus" + '\n')
        control_fans(0) 

    if (isLuefterActive and isHourUneven == True):
        print('an')
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + "Luefter an" + '\n')
        control_fans(1) 

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
