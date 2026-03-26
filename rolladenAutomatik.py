
import json
import time
import subprocess
import os
import drivers.Rolladoino as Rolladoino
import logging
import sys

from datetime import datetime, timedelta
from time import mktime

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

def berechne_zeiten_neu():
    """Ruft rolladenZeiten.py auf, um neue Zeiten zu berechnen (Fallback)."""
    try:
        result = subprocess.run(
            [sys.executable, 'rolladenZeiten.py'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            logger.error(f"rolladenZeiten.py fehlgeschlagen: {result.stderr}")
            return False
        logger.info("Neue Zeiten berechnet (Fallback).")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Aufruf von rolladenZeiten.py: {e}")
        return False

def lade_zeiten(path):
    """Lade die berechneten Zeiten von der Ramdisk. Bei Fehler: Neuberechnung als Fallback."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        # Prüfe ob die Zeiten für heute sind
        if data.get('date') != datetime.now().date().isoformat():
            logger.warning("Zeiten-Datei ist veraltet, berechne neu...")
            if berechne_zeiten_neu():
                with open(path, 'r') as f:
                    return json.load(f)
            return data  # Veraltete Zeiten sind besser als keine
        return data
    except FileNotFoundError:
        logger.warning(f"Zeiten-Datei {path} nicht gefunden. Berechne neu...")
        if berechne_zeiten_neu():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                logger.error(f"Zeiten-Datei {path} auch nach Neuberechnung nicht gefunden!")
                return None
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Fehler beim Lesen der Zeiten-Datei: {e}")
        if berechne_zeiten_neu():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None


logger.info('Starte RolladenAutomatik')

# global vars
clearReloadFile = False

# initialisire Program
# note: log file removed; using systemd/journald via stdout/stderr
path_reloadRegeln = './ramdisk/reloadRegeln.txt'
path_zeiten = './ramdisk/rolladenZeiten.json'

delta_time = timedelta(seconds=10)

#starte schleife
while True:
    # hole aktuelle Zeit
    startzeit = datetime.now() # local time

    logger.info(str(startzeit) + " new Roll loop!")

    # check if reload of regeln is triggered
    try:
        with open(path_reloadRegeln, 'r') as fr:
            if("true" == fr.readline()):
                clearReloadFile = True
                # Zeiten neu berechnen, da Regeln geändert wurden
                berechne_zeiten_neu()
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

    # Zeiten von Ramdisk laden (bei Fehler/veraltet wird automatisch neu berechnet)
    zeiten = lade_zeiten(path_zeiten)
    if zeiten is None:
        logger.error("Keine Zeiten verfügbar, überspringe Durchlauf.")
        time.sleep(delta_time.total_seconds())
        continue

    now = startzeit.time()
    window_end = (startzeit + delta_time).time()

    # Pro Gerät prüfen — zeit_hoch/zeit_runter sind bereits auf early/late geclampt
    for device in zeiten['devices']:
        zeit_hoch = stringToTime(device['zeit_hoch'])
        zeit_runter = stringToTime(device['zeit_runter'])
        name = device['name']
        channel = device['channel']
        address = device['address']

        # Regel 1: Rolladen hoch (morgens)
        if is_time_between(now, window_end, zeit_hoch):
            logger.info(f"{name}: Rolladen hoch")
            Rolladoino.main('CMD_Rolladen_Hoch', channel, address)
            time.sleep(1)

        # Regel 2: Rolladen runter (abends)
        if is_time_between(now, window_end, zeit_runter):
            logger.info(f"{name}: Rolladen runter")
            Rolladoino.main('CMD_Rolladen_Runter', channel, address)
            time.sleep(1)

    # Regel 3: Sonnenschutz (nur für dusk-Geräte)
    sonnenschutz = zeiten['sonne']['ein']
    isSonnenschutzActive = sonnenschutz == "true" or sonnenschutz == "True" or sonnenschutz == "TRUE"

    if isSonnenschutzActive:
        sonnerunter = stringToTime(zeiten['sonne']['runter'])
        sonnehoch = stringToTime(zeiten['sonne']['hoch'])
        isSonneRunter = is_time_between(now, window_end, sonnerunter)
        isSonneHoch = is_time_between(now, window_end, sonnehoch)

        for device in zeiten['devices']:
            if device['gruppe'] == 'dusk':
                if isSonneRunter:
                    Rolladoino.main('CMD_Rolladen_Runter', device['channel'], device['address'])
                    time.sleep(1)
                if isSonneHoch:
                    Rolladoino.main('CMD_Rolladen_Hoch', device['channel'], device['address'])
                    time.sleep(1)

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
