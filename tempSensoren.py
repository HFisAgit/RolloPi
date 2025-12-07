#!/usr/bin/env python3
"""
Programm zum Auslesen von zwei DS18B20 Temperatursensoren auf dem Raspberry Pi.
Speichert die Temperaturen und die Differenz in einem RamFS als JSON.
Erkennt Messfehler durch Abweichung von mehr als 2° vom letzten Messwert.
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime

# Sensor-Adressen
SENSOR1 = "/sys/bus/w1/devices/28-0000039a30a1/w1_slave"
SENSOR2 = "/sys/bus/w1/devices/28-0000039a478d/w1_slave"

# Output-Datei im RamFS
OUTPUT_FILE = "/home/pi/RolloPi/ramdisk/temperatures.json"

# Messfehler-Schwellwert (°C)
ERROR_THRESHOLD = 2.0

# Ausleseverzeichnis in Sekunden
READ_INTERVAL = 10

class TemperatureSensor:
    def __init__(self, sensor_path):
        self.sensor_path = sensor_path
        self.last_valid_value = None
    
    def read_raw(self):
        """Liest die rohe Temperatur vom Sensor aus."""
        try:
            with open(self.sensor_path, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Erste Zeile muss YES enthalten
            if lines[0].strip() != 'YES':
                return None
            
            # Temperaturwert aus der zweiten Zeile extrahieren
            for line in lines[1:]:
                if 't=' in line:
                    temp_raw = int(line.split('t=')[1])
                    return temp_raw / 1000.0  # In °C umwandeln
            
            return None
        
        except Exception as e:
            print(f"Fehler beim Lesen von {self.sensor_path}: {e}")
            return None
    
    def read_with_error_detection(self):
        """Liest Temperatur mit Fehlerdetektierung basierend auf Änderungsrate."""
        temp = self.read_raw()
        
        if temp is None:
            print(f"Sensor {self.sensor_path}: Lesefehler")
            return None
        
        # Erste Messung - einfach akzeptieren
        if self.last_valid_value is None:
            self.last_valid_value = temp
            return temp
        
        # Prüfe auf unrealistische Sprünge
        if abs(temp - self.last_valid_value) > ERROR_THRESHOLD:
            print(f"Sensor {self.sensor_path}: Verdächtiger Wert {temp}°C "
                  f"(Letzte Messung: {self.last_valid_value}°C). Ignoriert.")
            return None
        
        # Wert akzeptieren
        self.last_valid_value = temp
        return temp


def main():
    sensor1 = TemperatureSensor(SENSOR1)
    sensor2 = TemperatureSensor(SENSOR2)
    
    print("Temperaturüberwachung gestartet...")
    print(f"Output-Datei: {OUTPUT_FILE}")
    print(f"Ausleseinverval: {READ_INTERVAL} Sekunden")
    
    try:
        while True:
            # Sensoren auslesen
            temp1 = sensor1.read_with_error_detection()
            temp2 = sensor2.read_with_error_detection()
            
            # Daten vorbereiten
            data = {
                "timestamp": datetime.now().isoformat(),
                "sensor1": {
                    "address": "28-0000039a30a1",
                    "temperature": round(temp1, 2) if temp1 is not None else None
                },
                "sensor2": {
                    "address": "28-0000039a478d",
                    "temperature": round(temp2, 2) if temp2 is not None else None
                }
            }
            
            # Differenz berechnen, wenn beide Werte vorhanden
            if temp1 is not None and temp2 is not None:
                data["difference"] = round(abs(temp1 - temp2), 2)
            else:
                data["difference"] = None
            
            # In JSON-Datei schreiben
            try:
                os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
                with open(OUTPUT_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                    f.write('\n')
                
                print(f"[{data['timestamp']}] T1: {data['sensor1']['temperature']}°C, "
                      f"T2: {data['sensor2']['temperature']}°C, "
                      f"Diff: {data['difference']}°C")
            
            except Exception as e:
                print(f"Fehler beim Schreiben der Ausgabedatei: {e}")
            
            # Warten bis zur nächsten Messung
            time.sleep(READ_INTERVAL)
    
    except KeyboardInterrupt:
        print("\nTemperaturüberwachung beendet.")
    
    except Exception as e:
        print(f"Kritischer Fehler: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())