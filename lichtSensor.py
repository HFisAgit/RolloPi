#!/usr/bin/env python3
"""Einfacher Ausleser für TSL252 über ADS1115

- Liest periodisch den ADC-Wert vom ADS1115 (Treiber: drivers/ads1115.py)
- Schreibt JSON mit Timestamp, rohem Wert und berechneter Spannung in ramdisk
"""
import time
import json
from datetime import datetime
from pathlib import Path

try:
    from drivers import ads1115
except Exception as e:
    print("Fehler beim Import von drivers.ads1115:", e)
    raise

DEFAULT_OUTPUT = "/home/pi/RolloPi/ramdisk/light.json"
READ_INTERVAL = 10

def read_light_channel(channel=0):
    try:
        raw = ads1115.readSingle(channel)
        return int(raw)
    except Exception as e:
        print("Fehler beim Lesen des ADC:", e)
        return None

def raw_to_voltage(raw, vref=4.096):
    # ADS1115 liefert 16-bit Werte (±32768) bei gewählter Messspanne
    try:
        return (raw * float(vref)) / 32768.0
    except Exception:
        return None

def write_output(path: str, data: dict):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        with p.open('w') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
    except Exception as e:
        print(f"Fehler beim Schreiben der Datei {path}: {e}")

def main():
    print("Starte Licht-Sensor Ausleser")
    while True:
        raw = read_light_channel(0)
        voltage = None
        if raw is not None:
            try:
                voltage = round(raw_to_voltage(raw), 4)
            except Exception:
                voltage = None

        data = {
            "timestamp": datetime.now().isoformat(),
            "raw": raw,
            "voltage": voltage
        }

        write_output(DEFAULT_OUTPUT, data)
        print(f"[{data['timestamp']}] raw={raw} voltage={voltage}")
        time.sleep(READ_INTERVAL)

if __name__ == '__main__':
    main()
