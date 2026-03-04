# Abhänigkeiten
# pip install suncalc

import json
import time
import subprocess
import os
import math
import drivers.ads1115 as ads1115
import drivers.Rolladoino as Rolladoino
import logging
import sys

from suncalc import get_position, get_times
from datetime import datetime, timedelta
from time import mktime
from dateutil import tz

# Logging to stdout so systemd/journald captures logs
logger = logging.getLogger('rolladenAutomatik')
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


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

def get_sun_time_for_angle(date_utc, lng, lat, target_angle_deg, rising=True):
    """
    Berechne den UTC-Zeitpunkt, an dem die Sonne einen bestimmten Höhenwinkel erreicht.
    Verwendet Binärsuche mit suncalc.get_position().
    rising=True für morgens (Sonne steigt), rising=False für abends (Sonne sinkt).
    Gibt einen datetime in UTC zurück.
    """
    target_rad = target_angle_deg * math.pi / 180.0

    noon_utc = date_utc.replace(hour=12, minute=0, second=0, microsecond=0)

    if rising:
        low = noon_utc - timedelta(hours=14)
        high = noon_utc
    else:
        low = noon_utc
        high = noon_utc + timedelta(hours=14)

    # 50 Iterationen → Sub-Sekunden-Genauigkeit
    for _ in range(50):
        mid = low + (high - low) / 2
        pos = get_position(mid, lng, lat)
        altitude = pos['altitude']  # Radiant

        if rising:
            if altitude < target_rad:
                low = mid
            else:
                high = mid
        else:
            if altitude > target_rad:
                low = mid
            else:
                high = mid

    return low + (high - low) / 2

# Funktion zum Steuern der Lüfter
# time can be 'sunset' or 'dusk'
def control_shutter(time, pos):
    for device in config['devices'][time]:
        if pos == "hoch":
            Rolladoino.main('CMD_Rolladen_Hoch', device['channel'], device['address'])
        elif pos == "runter":
            Rolladoino.main('CMD_Rolladen_Runter', device['channel'], device['address'])
        time.sleep(1)


logger.info('Starte RolladenAutomatik')

# global vars
clearReloadFile = False

# initialisire Program
path_regeln = './regeln.json'
config_path = 'rolladenAddr.json'
# note: log file removed; using systemd/journald via stdout/stderr
path_reloadRegeln = './ramdisk/reloadRegeln.txt'
path_rolladoino = './drivers/Rolladoino.py'
path_suntimes = './ramdisk/suntimes.json' 
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

    logger.info(str(startzeit) + " new Roll loop!")

    # check if reload of regeln is triggered
    try:
        with open(path_reloadRegeln, 'r') as fr:
            if("true" == fr.readline()):
                with open(path_regeln, 'r') as regelnFile:
                    data = json.load(regelnFile)
                clearReloadFile = True
                heuteSchonZeitenAktualisiert = False  # Sonnenzeiten mit neuen Winkeln neu berechnen
    except FileNotFoundError:
        # Datei anlegen, falls sie fehlt
        with open(path_reloadRegeln, 'w') as fw:
            fw.write(" ")
        clearReloadFile = False

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
        logger.info("Neue Sonnen auf/unterganz Zeiten.")

        # Lese benutzerdefinierte Sonnenwinkel aus Regeln (Defaultwerte = bisheriges Verhalten)
        morgen_winkel = data['morgens'].get('sonnenwinkel', -6)        # Default: -6° (bürgerliche Dämmerung / dawn)
        strasse_winkel = data['abends'].get('sonnenwinkel_strasse', -6)  # Default: -6° (bürgerliche Dämmerung / dusk)
        garten_winkel = data['abends'].get('sonnenwinkel_garten', -0.833)  # Default: -0.833° (Sonnenuntergang / sunset)

        logger.info(f"Sonnenwinkel: morgens={morgen_winkel}°, strasse={strasse_winkel}°, garten={garten_winkel}°")

        # Standard-Sonnenzeiten für Anzeige
        _times = get_times(startzeitutc, lon, lat)
        for x in _times:
            _times[x] = datetime2local(_times[x])

        # Berechne benutzerdefinierte Sonnenzeiten basierend auf konfigurierten Winkeln
        dawn_time = datetime2local(get_sun_time_for_angle(startzeitutc, lon, lat, morgen_winkel, rising=True))
        dusk_time = datetime2local(get_sun_time_for_angle(startzeitutc, lon, lat, strasse_winkel, rising=False))
        sunset_time = datetime2local(get_sun_time_for_angle(startzeitutc, lon, lat, garten_winkel, rising=False))

        logger.info(f"Berechnete Zeiten: morgens={dawn_time.strftime('%H:%M:%S')}, strasse={dusk_time.strftime('%H:%M:%S')}, garten={sunset_time.strftime('%H:%M:%S')}")

        heuteSchonZeitenAktualisiert = True 

        # Zeiten für Anzeige exportieren
        s_sunrise = _times["sunrise"].isoformat()
        s_sunset  = _times["sunset"].isoformat()
        sunriseCropIndex = s_sunrise.rfind(".")
        sunsetCropIndex = s_sunset.rfind(".")

        def _crop_iso(iso_str):
            idx = iso_str.rfind(".")
            return iso_str[:idx] if idx > 0 else iso_str

        suntimes = {
            "date": startzeit.date().isoformat(),
            "sunrise": s_sunrise[:sunriseCropIndex],
            "sunset": s_sunset[:sunsetCropIndex],
            "custom_morgen": _crop_iso(dawn_time.isoformat()),
            "custom_strasse": _crop_iso(dusk_time.isoformat()),
            "custom_garten": _crop_iso(sunset_time.isoformat()),
            "winkel_morgen": morgen_winkel,
            "winkel_strasse": strasse_winkel,
            "winkel_garten": garten_winkel
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
        logger.info(str(startzeit) + " Rolladen hoch")
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
        logger.info(str(startzeit) + " Rolladen runter Straße")
        control_shutter('dusk', 'runter')
    
    # prüfe regel 2 Rolladen runter Garten - sunset ist die frühere Zeit
    # 1. ist es früh- und nach sonnenuntergang -> ja
    # 2. ist es nach früh && sonnenuntergang -> ja
    # 3. ist es spättestens -> ja
    sunsetBefore  = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsfrueh)    and sunset_time.time() <= startzeit.time()
    sunsetBetween = is_time_between(startzeit.time(), (startzeit + delta_time).time(), sunset_time.time() ) and abendsfrueh < startzeit.time()
    sunsetAfter   = is_time_between(startzeit.time(), (startzeit + delta_time).time(), abendsspaet)

    if ( sunsetBefore or sunsetBetween or sunsetAfter ):
        logger.info(str(startzeit) + " Rolladen runter Garten")
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
        logger.warning("Warning: loop takes longer then time_delta!")
        logger.warning(sleeptime.total_seconds())
        logger.warning(str(startzeit) + " Warning: loop takes longer then time_delta!")
        time.sleep(1)
# ende Schleife

print('end of program')
