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

def readTempSensor(sensorName) :
    """Aus dem Systembus lese ich die Temperatur der DS18B20 aus."""
    f = open(sensorName, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def readTempLines(sensorName) :
    lines = readTempSensor(sensorName)
    # Solange nicht die Daten gelesen werden konnten, bin ich hier in einer Endlosschleife
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = readTempSensor(sensorName)
    temperaturStr = lines[1].find('t=')
    # Ich überprüfe ob die Temperatur gefunden wurde.
    if temperaturStr != -1 :
        tempData = lines[1][temperaturStr+2:]
        tempCelsius = float(tempData) / 1000.0
        return tempCelsius
 
# Funktion zum Steuern der Lüfter
def control_fans(stufe):
    for device in config['devices']:
        Rolladoino.main('CMD_Luefter', device['channel'], device['address'], stufe)
        time.sleep(1)


# global vars
clearReloadFile = False

# Pfad zur Konfigurationsdatei
config_path = 'luefterAddr.json'

# Konfiguration laden
with open(config_path, 'r') as f:
    config = json.load(f)

# initialisire Program
path_regeln = './regeln.json'
path_log = './automatisierung.log'
path_reloadRegeln = './reloadRegeln.txt'
path_rolladoino = './drivers/Rolladoino.py'
#path_rolladoino = '/home/harald/daten/BackupUSB/fries/Simulator.py'

heuteSchonZeitenAktualisiert = False


# Systempfad zum den Sensor, weitere Systempfade könnten über ein Array
# oder weiteren Variablen hier hinzugefügt werden.
# 28-0000039a30a1 müsst ihr durch die eures Sensors ersetzen!
sensor1 = '/sys/bus/w1/devices/28-0000039a30a1/w1_slave'
sensor2 = '/sys/bus/w1/devices/28-0000039a478d/w1_slave'
 
 
# https://www.latlong.net/
lon = 8.504561
lat = 49.809986

# lade regeln.json
with open(path_regeln, 'r') as regelnFile:
    data = json.load(regelnFile)


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
