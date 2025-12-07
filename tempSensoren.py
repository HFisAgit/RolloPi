#!/usr/bin/env python3
"""
DS18B20-Ausleser mit Konfigurationsdatei und Sonnenschein-Entprellung.

- Liest zwei DS18B20-Sensoren periodisch aus.
- Speichert Temperaturen, Differenz und das Bool 'sonnenschein' als JSON.
- Konfigurierbare Parameter via JSON-Config:
  - error_threshold: max. Änderung (°C) zur Erkennung von Messfehlern
  - read_interval: Abtastintervall in Sekunden
  - sun_diff_threshold: Differenz (°C) ab der 'sonnenschein' erkannt werden kann
  - sun_debounce_count: Anzahl aufeinanderfolgender Messungen >= threshold, um True zu setzen
  - sun_release_count: Anzahl aufeinanderfolgender Messungen < threshold, um False zu setzen
  - sensor1, sensor2: Pfade zu w1_slave
  - output_file: Pfad zur Ausgabe-Datei
"""

import json
import time
import os
import argparse
from pathlib import Path
from datetime import datetime

# Standard-Pfade (kann in der Config überschrieben werden)
DEFAULT_SENSOR1 = "/sys/bus/w1/devices/28-0000039a30a1/w1_slave"
DEFAULT_SENSOR2 = "/sys/bus/w1/devices/28-0000039a478d/w1_slave"
DEFAULT_OUTPUT = "/home/pi/RolloPi/ramdisk/temperatures.json"
DEFAULT_CONFIG = Path(__file__).parent / "temp_config.json"

# Default-Parameter
DEFAULTS = {
    "error_threshold": 2.0,
    "read_interval": 10,
    "sun_diff_threshold": 1.0,
    "sun_debounce_count": 3,
    "sun_release_count": 2,
    "sensor1": DEFAULT_SENSOR1,
    "sensor2": DEFAULT_SENSOR2,
    "output_file": DEFAULT_OUTPUT
}

def load_config(path: Path) -> dict:
    cfg = DEFAULTS.copy()
    try:
        if path.exists():
            with path.open() as f:
                user = json.load(f)
            if not isinstance(user, dict):
                print(f"Config {path} ungültig, benutze Defaults.")
                return cfg
            for k in user:
                if k in cfg:
                    cfg[k] = user[k]
        else:
            print(f"Config-Datei {path} nicht gefunden, benutze Defaults.")
    except Exception as e:
        print(f"Fehler beim Laden der Config {path}: {e}. Benutze Defaults.")
    return cfg

class TemperatureSensor:
    def __init__(self, sensor_path, error_threshold):
        self.sensor_path = sensor_path
        self.last_valid_value = None
        self.error_threshold = float(error_threshold)
    
    def read_raw(self):
        """Liest die rohe Temperatur vom Sensor aus (/sys/bus/w1/.../w1_slave)."""
        try:
            with open(self.sensor_path, 'r') as f:
                content = f.read()
            lines = content.splitlines()
            if not lines or len(lines) < 2:
                return None
            # Erste Zeile muss 'YES' enthalten (CRC-Prüfung)
            if 'YES' not in lines[0]:
                return None
            # Temperaturwert aus der zweiten Zeile extrahieren
            if 't=' in lines[1]:
                try:
                    temp_raw = int(lines[1].split('t=')[1])
                    return temp_raw / 1000.0  # In °C umwandeln
                except (ValueError, IndexError):
                    return None
            return None
        except FileNotFoundError:
            print(f"Sensordatei nicht vorhanden: {self.sensor_path}")
            return None
        except Exception as e:
            print(f"Fehler beim Lesen von {self.sensor_path}: {e}")
            return None
    
    def read_with_error_detection(self):
        """Liest Temperatur und filtert sprunghafte Messfehler heraus."""
        temp = self.read_raw()
        if temp is None:
            print(f"Sensor {self.sensor_path}: Lesefehler")
            return None
        # Erste Messung - akzeptieren
        if self.last_valid_value is None:
            self.last_valid_value = temp
            return temp
        # Prüfe auf unrealistischen Sprung
        if abs(temp - self.last_valid_value) > self.error_threshold:
            print(f"Sensor {self.sensor_path}: Verdächtiger Wert {temp}°C "
                  f"(Letzte gültige Messung: {self.last_valid_value}°C). Ignoriert.")
            return None
        # Wert akzeptieren
        self.last_valid_value = temp
        return temp

def make_output_dir_if_needed(path: str):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception as e:
        print(f"Fehler beim Anlegen des Output-Verzeichnisses für {path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="DS18B20 Ausleser mit Config und Sonnenschein-Entprellung")
    parser.add_argument("--config", "-c", type=str, default=str(DEFAULT_CONFIG),
                        help="Pfad zur JSON-Config (default: temp_config.json neben dem Script)")
    args = parser.parse_args()

    cfg_path = Path(args.config)
    cfg = load_config(cfg_path)

    ERROR_THRESHOLD = float(cfg["error_threshold"])
    READ_INTERVAL = int(cfg["read_interval"])
    SUN_DIFF_THRESHOLD = float(cfg["sun_diff_threshold"])
    SUN_DEBOUNCE = int(cfg["sun_debounce_count"])
    SUN_RELEASE = int(cfg["sun_release_count"])
    SENSOR1 = cfg["sensor1"]
    SENSOR2 = cfg["sensor2"]
    OUTPUT_FILE = cfg["output_file"]

    sensor1 = TemperatureSensor(SENSOR1, ERROR_THRESHOLD)
    sensor2 = TemperatureSensor(SENSOR2, ERROR_THRESHOLD)

    make_output_dir_if_needed(OUTPUT_FILE)

    # Entprell-Statusvariablen
    sonnenschein = False
    true_count = 0
    false_count = 0

    print("Temperaturüberwachung gestartet...")
    print(f"Config: {cfg_path}")
    print(f"Output-Datei: {OUTPUT_FILE}")
    print(f"Intervall: {READ_INTERVAL}s, Error-Threshold: {ERROR_THRESHOLD}°C, "
          f"Sonnenschein ab: {SUN_DIFF_THRESHOLD}°C (debounce {SUN_DEBOUNCE}, release {SUN_RELEASE})")

    try:
        while True:
            temp1 = sensor1.read_with_error_detection()
            temp2 = sensor2.read_with_error_detection()

            # Differenz berechnen (None falls unvollständig)
            difference = None
            if temp1 is not None and temp2 is not None:
                difference = abs(temp1 - temp2)

            # Entprell-Logik: Zähle aufeinanderfolgende Messungen
            if difference is not None and difference >= SUN_DIFF_THRESHOLD:
                true_count += 1
                false_count = 0
            else:
                false_count += 1
                true_count = 0

            # Setze oder löse Sonnenschein je nach Zählern
            if not sonnenschein and true_count >= SUN_DEBOUNCE:
                sonnenschein = True
                print(f"Sonnenschein aktiviert (diff={difference}, true_count={true_count})")
            if sonnenschein and false_count >= SUN_RELEASE:
                sonnenschein = False
                print(f"Sonnenschein deaktiviert (diff={difference}, false_count={false_count})")

            data = {
                "timestamp": datetime.now().isoformat(),
                "sensor1": {
                    "path": SENSOR1,
                    "temperature": round(temp1, 2) if temp1 is not None else None
                },
                "sensor2": {
                    "path": SENSOR2,
                    "temperature": round(temp2, 2) if temp2 is not None else None
                },
                "difference": round(difference, 2) if difference is not None else None,
                "sonnenschein": sonnenschein
            }

            try:
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(data, f, indent=2)
                    f.write("\n")
                print(f"[{data['timestamp']}] T1: {data['sensor1']['temperature']}°C, "
                      f"T2: {data['sensor2']['temperature']}°C, "
                      f"Diff: {data['difference']}°C, Sonnenschein: {data['sonnenschein']}")
            except Exception as e:
                print(f"Fehler beim Schreiben der Datei {OUTPUT_FILE}: {e}")

            time.sleep(READ_INTERVAL)

    except KeyboardInterrupt:
        print("\nTemperaturüberwachung beendet.")
    except Exception as e:
        print(f"Kritischer Fehler: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())