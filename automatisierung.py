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
from gpiozero import LED



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

def updateLauflicht(lauflicht):
    with open(path_log, 'a') as f:
            f.write(str(startzeit) + " Lauflicht: " + str(lauflicht) + '\n')
    bit0 = lauflicht % 2
    bit1 = (lauflicht >> 1) % 2
    bit2 = (lauflicht >> 2) % 2
    bit3 = (lauflicht >> 3) % 2
    bit4 = (lauflicht >> 4) % 2
    bit5 = (lauflicht >> 5) % 2
    bit6 = (lauflicht >> 6) % 2
    bit7 = (lauflicht >> 7) % 2

    led0.off() if bit0 == 0 else led0.on()
    led1.off() if bit1 == 0 else led1.on()
    led2.off() if bit2 == 0 else led2.on()
    led3.off() if bit3 == 0 else led3.on()
    led4.off() if bit4 == 0 else led4.on()
    led5.off() if bit5 == 0 else led5.on()
    led6.off() if bit6 == 0 else led6.on()
    led7.off() if bit7 == 0 else led7.on()

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
 


# global vars
clearReloadFile = False

# define addresses
# todo: echte Adressen eintragen
addrKueche = '0x0a'
addrHwr = '0x0b'
addrWc = '0x0c'
addrGaderobe = '0x0d'
addrBuroP = '0x0e'
addrWohnz = '0x0f'
addrTerrasse = '0x0g'

addrSchlafz = '0x1a'
addrBad = '0x1b'
addrBuroR = '0x1c'
addrGaste = '0x1d'

# initialisire Program
path_regeln = './regeln.json'
#path_rolladoino = '/home/pi/RolloPi/Rolladoino.py'
#path_log = '/home/pi/RolloPi/automatisierung.log'
#path_reloadRegeln = '/home/pi/RolloPi/reloadRegeln.txt'
#path_rolladoino = './Rolladoino3.py'
path_rolladoino = './RolladoinoNew.py'
path_log = './automatisierung.log'
path_reloadRegeln = './ramdisk/reloadRegeln.txt'
path_suntimes = './ramdisk/suntimes.json'
#path_rolladoino = '/home/harald/daten/BackupUSB/fries/Simulator.py'

#GPIO
led0 = LED(26)
led1 = LED(16)
led2 = LED(19)
led3 = LED(13)
led4 = LED(12)
led5 = LED(6)
led6 = LED(5)
led7 = LED(4)

led0.on()
led1.on()
led2.on()
led3.on()
led4.on()
led5.on()
led6.on()
led7.on()

lauflicht = 0

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
        with open(path_suntimes, 'w') as f:
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
        os.system('python3 ' + path_rolladoino + ' ' + addrKueche +' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrHwr + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrWc + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrGaderobe + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrBuroP + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrWohnz + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrTerrasse + ' CMD_Rolladen_Hoch')

        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrSchlafz + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrBad + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrBuroR + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrGaste + ' CMD_Rolladen_Hoch')

    # prüfe regel 2 Rolladen runter Straße
    # 1. ist es früh- und nach sonnenuntergang -> ja
    # 2. ist es nach früh && sonnenuntergang -> ja
    # 3. ist es spättestens -> ja
    abendsfrueh = stringToTime(data['abends']['early'])
    abendsspaet = stringToTime(data['abends']['late'])
    
    duskBefore  = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsfrueh)    and sunset_time.time() <= startzeit.time()
    duskBetween = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sunset_time.time() ) and abendsfrueh < startzeit.time()
    duskAfter   = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsspaet)

    if ( duskBefore or duskBetween or duskAfter ):
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + " Rolladen runter Straße" + '\n')
        os.system('python3 ' + path_rolladoino + ' ' + addrKueche +' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrWc + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrGaderobe + ' CMD_Rolladen_Runter')

        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrSchlafz + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrBad + ' CMD_Rolladen_Runter')
    
    # prüfe regel 2 Rolladen runter Garten
    # 1. ist es früh- und nach sonnenuntergang -> ja
    # 2. ist es nach früh && sonnenuntergang -> ja
    # 3. ist es spättestens -> ja
    sunsetBefore  = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsfrueh)    and dusk_time.time() <= startzeit.time()
    sunsetBetween = is_time_between(startzeit.time(), (startzeit + delta_time).time(), dusk_time.time() ) and abendsfrueh < startzeit.time()
    sunsetAfter   = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsspaet)

    if ( sunsetBefore or sunsetBetween or sunsetAfter ):
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + " Rolladen runter Garten" + '\n')
        os.system('python3 ' + path_rolladoino + ' ' + addrBuroP + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrWohnz + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrTerrasse + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrBuroR + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrGaste + ' CMD_Rolladen_Runter')
        

    # prüfe regel 3 sonne runter
    sonnenschutz = data['sonne']['ein']
    sonnerunter = stringToTime(data['sonne']['runter'])
    sonnehoch = stringToTime(data['sonne']['hoch'])

    isSonnenschutzActive = sonnenschutz == "true" or sonnenschutz == "True" or sonnenschutz == "TRUE"
    isSonneRunter = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sonnerunter)
    isSonneHoch = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sonnehoch)

    if (isSonnenschutzActive and isSonneRunter):
        os.system('python3 ' + path_rolladoino + ' ' + addrWohnz + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrTerrasse + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrBuroR + ' CMD_Rolladen_Runter')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrGaste + ' CMD_Rolladen_Runter')
    
    # prüfe regel 3 Sonne hoch
    if (isSonnenschutzActive and isSonneHoch):
        os.system('python3 ' + path_rolladoino + ' ' + addrWohnz + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrTerrasse + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrBuroR + ' CMD_Rolladen_Hoch')
        time.sleep(1)
        os.system('python3 ' + path_rolladoino + ' ' + addrGaste + ' CMD_Rolladen_Hoch')
    
    #######################################################################################

    # Hardware Tests:
    # lauflicht
    if (lauflicht < 7):
        lauflicht += 1
    else:
        lauflicht = 0
    updateLauflicht(lauflicht)
    
    # ADC
    adc1 = ads1115.readSingle(0)
    adc2 = ads1115.readSingle(1)
    adc3 = ads1115.readSingle(2)
    adc4 = ads1115.readSingle(3)

    analogVals = {
            "adc1": str(adc1),
            "adc2": str(adc2),
            "adc3": str(adc3),
            "adc4": str(adc4)
        }
    with open('analogValues.json', 'w') as f:
            json.dump(analogVals, f)

    
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
