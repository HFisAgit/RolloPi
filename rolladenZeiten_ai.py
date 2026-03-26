# Abhängigkeiten
# pip install suncalc requests
# Ollama muss lokal laufen: https://ollama.ai

import json
import math
import logging
import sys
import subprocess
import urllib.request
import urllib.error

from suncalc import get_position, get_times
from datetime import datetime, timedelta
from dateutil import tz

# Logging to stdout so systemd/journald captures logs
logger = logging.getLogger('rolladenZeiten_ai')
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Pfade
path_regeln = './regeln.json'
path_config = './rolladenAddr.json'
path_ai_config = './ai_prompt_config.json'
path_output = './ramdisk/rolladenZeiten.json'
path_suntimes = './ramdisk/suntimes.json'
path_fallback = './rolladenZeiten.py'

# https://www.latlong.net/
lon = 8.504561
lat = 49.809986


def datetime2local(dto: datetime, s_tz: str = 'Europe/Berlin'):
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz(s_tz)
    _local = dto.replace(tzinfo=from_zone)
    return _local.astimezone(to_zone)


def get_sun_time_for_angle(date_utc, lng, lat, target_angle_deg, rising=True):
    """Berechne den UTC-Zeitpunkt für einen bestimmten Sonnen-Höhenwinkel."""
    target_rad = target_angle_deg * math.pi / 180.0
    noon_utc = date_utc.replace(hour=12, minute=0, second=0, microsecond=0)

    if rising:
        low = noon_utc - timedelta(hours=14)
        high = noon_utc
    else:
        low = noon_utc
        high = noon_utc + timedelta(hours=14)

    for _ in range(50):
        mid = low + (high - low) / 2
        pos = get_position(mid, lng, lat)
        altitude = pos['altitude']

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
    """Beschränke eine berechnete Zeit auf den Bereich [early, late]."""
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


def hole_wetterdaten():
    """Hole aktuelle Wetterdaten von Open-Meteo API (kostenlos, kein Key nötig)."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=sunrise,sunset,weathercode,temperature_2m_max,uv_index_max"
        f"&hourly=cloudcover,temperature_2m"
        f"&timezone=Europe/Berlin"
        f"&forecast_days=1"
    )
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'RolloPi/1.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
        logger.info("Wetterdaten erfolgreich geholt.")
        return data
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        logger.warning(f"Wetterdaten konnten nicht geholt werden: {e}")
        return None


def formatiere_wetter(wetter_data):
    """Wetterdaten in lesbaren Text für den Prompt umwandeln."""
    if wetter_data is None:
        return "Keine Wetterdaten verfügbar."

    try:
        daily = wetter_data.get('daily', {})
        hourly = wetter_data.get('hourly', {})

        temp_max = daily.get('temperature_2m_max', [None])[0]
        uv_max = daily.get('uv_index_max', [None])[0]
        wetter_code = daily.get('weathercode', [None])[0]

        # Bewölkung: Durchschnitt der Stunden 6-21 (Tagesstunden)
        cloud_values = hourly.get('cloudcover', [])
        temp_values = hourly.get('temperature_2m', [])
        hours = hourly.get('time', [])

        tag_wolken = []
        for i, h in enumerate(hours):
            hour = int(h.split('T')[1].split(':')[0]) if 'T' in h else 0
            if 6 <= hour <= 21 and i < len(cloud_values):
                tag_wolken.append(cloud_values[i])

        avg_cloud = sum(tag_wolken) / len(tag_wolken) if tag_wolken else None

        # WMO Wettercode in Text
        wetter_codes = {
            0: "Klar", 1: "Überwiegend klar", 2: "Teilweise bewölkt",
            3: "Bedeckt", 45: "Nebel", 48: "Nebel mit Reif",
            51: "Leichter Nieselregen", 53: "Mäßiger Nieselregen",
            55: "Starker Nieselregen", 61: "Leichter Regen",
            63: "Mäßiger Regen", 65: "Starker Regen",
            71: "Leichter Schneefall", 73: "Mäßiger Schneefall",
            75: "Starker Schneefall", 80: "Leichte Regenschauer",
            81: "Mäßige Regenschauer", 82: "Starke Regenschauer",
            95: "Gewitter", 96: "Gewitter mit Hagel"
        }
        wetter_text = wetter_codes.get(wetter_code, f"Unbekannt (Code {wetter_code})")

        lines = [f"Wetterlage: {wetter_text}"]
        if temp_max is not None:
            lines.append(f"Höchsttemperatur: {temp_max}°C")
        if avg_cloud is not None:
            lines.append(f"Durchschnittliche Bewölkung tagsüber: {avg_cloud:.0f}%")
        if uv_max is not None:
            lines.append(f"UV-Index max: {uv_max}")

        # Bewölkungsverlauf morgens und abends
        morgens_wolken = []
        abends_wolken = []
        for i, h in enumerate(hours):
            hour = int(h.split('T')[1].split(':')[0]) if 'T' in h else 0
            if 5 <= hour <= 9 and i < len(cloud_values):
                morgens_wolken.append(cloud_values[i])
            if 17 <= hour <= 21 and i < len(cloud_values):
                abends_wolken.append(cloud_values[i])

        if morgens_wolken:
            lines.append(f"Bewölkung morgens (5-9 Uhr): {sum(morgens_wolken)/len(morgens_wolken):.0f}%")
        if abends_wolken:
            lines.append(f"Bewölkung abends (17-21 Uhr): {sum(abends_wolken)/len(abends_wolken):.0f}%")

        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"Fehler beim Formatieren der Wetterdaten: {e}")
        return "Keine Wetterdaten verfügbar (Formatierungsfehler)."


def frage_ollama(prompt_config, system_prompt, user_prompt):
    """Sende Prompt an lokales Ollama und gib die Antwort zurück."""
    url = prompt_config['ollama_url'] + '/api/generate'
    timeout = prompt_config.get('timeout_seconds', 120)

    payload = json.dumps({
        "model": prompt_config['model'],
        "prompt": user_prompt,
        "system": system_prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048
        }
    }).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        result = json.loads(response.read().decode('utf-8'))

    return result.get('response', '')


def validiere_antwort(antwort_json, erwartete_devices):
    """Prüfe ob die LLM-Antwort das richtige Format hat."""
    if 'devices' not in antwort_json:
        raise ValueError("Feld 'devices' fehlt")
    if 'date' not in antwort_json:
        raise ValueError("Feld 'date' fehlt")
    if 'sonne' not in antwort_json:
        raise ValueError("Feld 'sonne' fehlt")

    devices = antwort_json['devices']
    if len(devices) != len(erwartete_devices):
        raise ValueError(f"Erwarte {len(erwartete_devices)} Geräte, bekam {len(devices)}")

    erwartete_namen = {d['name'] for d in erwartete_devices}

    for device in devices:
        for feld in ['name', 'channel', 'address', 'gruppe', 'zeit_hoch', 'zeit_runter']:
            if feld not in device:
                raise ValueError(f"Feld '{feld}' fehlt in Gerät {device.get('name', '?')}")

        if device['name'] not in erwartete_namen:
            raise ValueError(f"Unbekanntes Gerät: {device['name']}")

        # Zeitformat prüfen (H:MM:SS oder HH:MM:SS)
        for zeit_feld in ['zeit_hoch', 'zeit_runter']:
            parts = device[zeit_feld].split(':')
            if len(parts) != 3:
                raise ValueError(f"Ungültiges Zeitformat für {device['name']}.{zeit_feld}: {device[zeit_feld]}")
            try:
                h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
                    raise ValueError(f"Zeit außerhalb gültiger Bereiche: {device[zeit_feld]}")
            except (ValueError, IndexError):
                raise ValueError(f"Ungültiges Zeitformat: {device[zeit_feld]}")

    return True


def fallback_deterministisch():
    """Fallback: rufe die deterministische Berechnung auf."""
    logger.warning("Starte Fallback: deterministische Berechnung mit rolladenZeiten.py")
    try:
        result = subprocess.run(
            [sys.executable, path_fallback],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            logger.info("Fallback erfolgreich.")
            return True
        else:
            logger.error(f"Fallback fehlgeschlagen: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Fallback-Fehler: {e}")
        return False


def berechne_zeiten_ai():
    """Berechne Rolladen-Zeiten mit lokalem LLM und Wetterdaten."""
    now_utc = datetime.utcnow()
    now_local = datetime.now()

    # Konfigurationen laden
    with open(path_regeln, 'r') as f:
        regeln = json.load(f)
    with open(path_config, 'r') as f:
        config = json.load(f)
    with open(path_ai_config, 'r') as f:
        ai_config = json.load(f)

    # Sonnenwinkel aus Regeln
    morgen_winkel = regeln['morgens'].get('sonnenwinkel', -6)
    strasse_winkel = regeln['abends'].get('sonnenwinkel_strasse', -6)
    garten_winkel = regeln['abends'].get('sonnenwinkel_garten', -0.833)

    # Astronomische Referenzzeiten berechnen
    _times = get_times(now_utc, lon, lat)
    for x in _times:
        _times[x] = datetime2local(_times[x])

    dawn_time = datetime2local(get_sun_time_for_angle(now_utc, lon, lat, morgen_winkel, rising=True))
    dusk_time = datetime2local(get_sun_time_for_angle(now_utc, lon, lat, strasse_winkel, rising=False))
    sunset_time = datetime2local(get_sun_time_for_angle(now_utc, lon, lat, garten_winkel, rising=False))

    logger.info(f"Astronomische Zeiten: dawn={dawn_time.strftime('%H:%M:%S')}, "
                f"dusk={dusk_time.strftime('%H:%M:%S')}, sunset={sunset_time.strftime('%H:%M:%S')}")

    # Wetterdaten holen
    wetter_data = hole_wetterdaten()
    wetter_text = formatiere_wetter(wetter_data)
    logger.info(f"Wetter:\n{wetter_text}")

    # Grenzen aus Regeln
    morgens_early = regeln['morgens']['early']
    morgens_late = regeln['morgens']['late']
    abends_early = regeln['abends']['early']
    abends_late = regeln['abends']['late']

    # Geräte-Liste für Prompt formatieren
    devices_text = json.dumps(config['devices'], indent=2, ensure_ascii=False)

    # Format-Beispiel bauen
    format_example = json.dumps({
        "date": now_local.date().isoformat(),
        "sonne": regeln['sonne'],
        "devices": [
            {
                "name": "GERÄTENAME",
                "channel": "CHANNEL",
                "address": "ADDRESS",
                "gruppe": "GRUPPE",
                "zeit_hoch": "HH:MM:SS",
                "zeit_runter": "HH:MM:SS"
            }
        ]
    }, indent=2, ensure_ascii=False)

    # Prompt zusammenbauen
    user_prompt = ai_config['user_prompt_template'].format(
        date=now_local.date().isoformat(),
        lat=lat,
        lon=lon,
        sunrise=_times['sunrise'].strftime('%H:%M:%S'),
        sunset=_times['sunset'].strftime('%H:%M:%S'),
        dawn=dawn_time.strftime('%H:%M:%S'),
        dusk=dusk_time.strftime('%H:%M:%S'),
        sunset_custom=sunset_time.strftime('%H:%M:%S'),
        morgen_winkel=morgen_winkel,
        strasse_winkel=strasse_winkel,
        garten_winkel=garten_winkel,
        morgens_early=morgens_early,
        morgens_late=morgens_late,
        abends_early=abends_early,
        abends_late=abends_late,
        wetter=wetter_text,
        sonne_ein=regeln['sonne']['ein'],
        sonne_runter=regeln['sonne']['runter'],
        sonne_hoch=regeln['sonne']['hoch'],
        devices=devices_text,
        format_example=format_example
    )

    system_prompt = ai_config['system_prompt']
    max_retries = ai_config.get('max_retries', 3)

    # LLM aufrufen mit Retry
    for attempt in range(1, max_retries + 1):
        logger.info(f"LLM-Versuch {attempt}/{max_retries}...")
        try:
            antwort_raw = frage_ollama(ai_config, system_prompt, user_prompt)
            logger.info(f"LLM-Antwort ({len(antwort_raw)} Zeichen) erhalten.")

            antwort = json.loads(antwort_raw)
            validiere_antwort(antwort, config['devices'])

            # Sicherheits-Clamping: LLM-Zeiten auf early/late beschränken
            for device in antwort['devices']:
                device['zeit_hoch'] = _clamp_time(device['zeit_hoch'], morgens_early, morgens_late)
                device['zeit_runter'] = _clamp_time(device['zeit_runter'], abends_early, abends_late)
                logger.info(f"  {device['name']}: hoch={device['zeit_hoch']}, runter={device['zeit_runter']}")

            # Ergebnis schreiben
            with open(path_output, 'w') as f:
                json.dump(antwort, f, indent=2)
            logger.info(f"AI-Zeiten geschrieben nach {path_output}")

            # Suntimes für Webseite exportieren
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
                "winkel_garten": garten_winkel,
                "quelle": "ai",
                "wetter": wetter_text
            }

            with open(path_suntimes, 'w') as f:
                json.dump(suntimes, f)
            logger.info(f"Suntimes geschrieben nach {path_suntimes}")
            return True

        except json.JSONDecodeError as e:
            logger.warning(f"Versuch {attempt}: Ungültiges JSON vom LLM: {e}")
            logger.warning(f"Rohe Antwort: {antwort_raw[:500]}")
        except ValueError as e:
            logger.warning(f"Versuch {attempt}: Validierungsfehler: {e}")
        except (urllib.error.URLError, OSError) as e:
            logger.warning(f"Versuch {attempt}: Ollama nicht erreichbar: {e}")
        except Exception as e:
            logger.warning(f"Versuch {attempt}: Unerwarteter Fehler: {e}")

    # Alle Versuche fehlgeschlagen → Fallback
    logger.error(f"Alle {max_retries} LLM-Versuche fehlgeschlagen.")
    fallback_deterministisch()


if __name__ == '__main__':
    berechne_zeiten_ai()
