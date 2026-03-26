# Abhänigkeiten
# pip install suncalc

import json
import math
import logging
import sys

from suncalc import get_position, get_times
from datetime import datetime, timedelta
from dateutil import tz

# Logging to stdout so systemd/journald captures logs
logger = logging.getLogger('rolladenZeiten')
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Pfade
path_regeln = './regeln.json'
path_config = './rolladenAddr.json'
path_output = './ramdisk/rolladenZeiten.json'
path_suntimes = './ramdisk/suntimes.json'

# https://www.latlong.net/
lon = 8.504561
lat = 49.809986


def datetime2local(dto: datetime, s_tz: str = 'Europe/Berlin'):
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(s_tz)
    _local = dto.replace(tzinfo=from_zone)
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


def _crop_iso(iso_str):
    idx = iso_str.rfind(".")
    return iso_str[:idx] if idx > 0 else iso_str


def _clamp_time(calculated_time_str, early_str, late_str):
    """Beschränke eine berechnete Zeit auf den Bereich [early, late].
    Wenn die berechnete Zeit vor 'early' liegt, wird 'early' zurückgegeben.
    Wenn sie nach 'late' liegt, wird 'late' zurückgegeben.
    """
    # Alle Zeiten als Tupel (H, M, S) vergleichbar machen
    def _parse(t_str):
        parts = t_str.split(':')
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    calc = _parse(calculated_time_str)
    early = _parse(early_str)
    late = _parse(late_str)

    if calc < early:
        return early_str
    elif calc > late:
        return late_str
    else:
        return calculated_time_str


def berechne_zeiten():
    """Berechne Rolladen-Zeiten für alle Geräte und schreibe Ergebnisse auf die Ramdisk."""
    now_utc = datetime.utcnow()
    now_local = datetime.now()

    # Regeln laden
    with open(path_regeln, 'r') as f:
        regeln = json.load(f)

    # Hardware-Konfiguration laden
    with open(path_config, 'r') as f:
        config = json.load(f)

    # Sonnenwinkel aus Regeln lesen (Defaultwerte = bisheriges Verhalten)
    morgen_winkel = regeln['morgens'].get('sonnenwinkel', -6)          # Default: -6° (bürgerliche Dämmerung)
    strasse_winkel = regeln['abends'].get('sonnenwinkel_strasse', -6)  # Default: -6° (bürgerliche Dämmerung)
    garten_winkel = regeln['abends'].get('sonnenwinkel_garten', -0.833)  # Default: -0.833° (Sonnenuntergang)

    logger.info(f"Sonnenwinkel: morgens={morgen_winkel}°, strasse={strasse_winkel}°, garten={garten_winkel}°")

    # Standard-Sonnenzeiten für Anzeige (Webseite)
    _times = get_times(now_utc, lon, lat)
    for x in _times:
        _times[x] = datetime2local(_times[x])

    # Morgens-Zeit berechnen (gleich für alle Geräte)
    dawn_time = datetime2local(get_sun_time_for_angle(now_utc, lon, lat, morgen_winkel, rising=True))

    # Abends-Zeiten je nach Gruppe
    dusk_time = datetime2local(get_sun_time_for_angle(now_utc, lon, lat, strasse_winkel, rising=False))
    sunset_time = datetime2local(get_sun_time_for_angle(now_utc, lon, lat, garten_winkel, rising=False))

    logger.info(f"Berechnete Zeiten: morgens={dawn_time.strftime('%H:%M:%S')}, "
                f"strasse={dusk_time.strftime('%H:%M:%S')}, garten={sunset_time.strftime('%H:%M:%S')}")

    # Grenzen aus Regeln
    morgens_early = regeln['morgens']['early']
    morgens_late = regeln['morgens']['late']
    abends_early = regeln['abends']['early']
    abends_late = regeln['abends']['late']

    # Per-device Zeiten berechnen und auf early/late clampen
    devices_output = []
    for device in config['devices']:
        gruppe = device['gruppe']

        if gruppe == 'dusk':
            zeit_runter_raw = dusk_time.strftime('%H:%M:%S')
        elif gruppe == 'sunset':
            zeit_runter_raw = sunset_time.strftime('%H:%M:%S')
        else:
            logger.warning(f"Unbekannte Gruppe '{gruppe}' für {device['name']}, verwende dusk-Zeit")
            zeit_runter_raw = dusk_time.strftime('%H:%M:%S')

        zeit_hoch_raw = dawn_time.strftime('%H:%M:%S')

        # Clamping: berechnete Zeit auf [early, late] beschränken
        zeit_hoch = _clamp_time(zeit_hoch_raw, morgens_early, morgens_late)
        zeit_runter = _clamp_time(zeit_runter_raw, abends_early, abends_late)

        logger.info(f"  {device['name']}: hoch={zeit_hoch} (raw={zeit_hoch_raw}), "
                    f"runter={zeit_runter} (raw={zeit_runter_raw})")

        devices_output.append({
            "name": device['name'],
            "channel": device['channel'],
            "address": device['address'],
            "gruppe": gruppe,
            "zeit_hoch": zeit_hoch,
            "zeit_runter": zeit_runter
        })

    # Ergebnis-JSON zusammenbauen
    output = {
        "date": now_local.date().isoformat(),
        "sonne": regeln['sonne'],
        "devices": devices_output
    }

    with open(path_output, 'w') as f:
        json.dump(output, f, indent=2)
    logger.info(f"Zeiten geschrieben nach {path_output}")

    # Suntimes für Anzeige (Webseite) exportieren
    s_sunrise = _times["sunrise"].isoformat()
    s_sunset = _times["sunset"].isoformat()

    suntimes = {
        "date": now_local.date().isoformat(),
        "sunrise": _crop_iso(s_sunrise),
        "sunset": _crop_iso(s_sunset),
        "custom_morgen": _crop_iso(dawn_time.isoformat()),
        "custom_strasse": _crop_iso(dusk_time.isoformat()),
        "custom_garten": _crop_iso(sunset_time.isoformat()),
        "winkel_morgen": morgen_winkel,
        "winkel_strasse": strasse_winkel,
        "winkel_garten": garten_winkel
    }

    with open(path_suntimes, 'w') as f:
        json.dump(suntimes, f)
    logger.info(f"Suntimes geschrieben nach {path_suntimes}")


if __name__ == '__main__':
    berechne_zeiten()
