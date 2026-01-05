#!/usr/bin/env python3
"""
Telefon-Überwachungsskript für GPIO5
Überwacht GPIO5 auf Toggling mit 0,5Hz - 2Hz und aktiviert GPIO13 sowie den Summer an allen Rolladoinos
"""

import RPi.GPIO as GPIO
import time
import json
import sys
import os

# Importiere Rolladoino-Modul
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'drivers'))
import drivers.Rolladoino as Rolladoino

# GPIO Konfiguration
GPIO_INPUT = 5      # Eingang zum Überwachen
GPIO_OUTPUT = 13    # Ausgang zum Setzen

# Frequenz-Parameter
MIN_FREQUENCY = 0.5  # Hz
MAX_FREQUENCY = 2.0  # Hz
MIN_PERIOD = 1.0 / MAX_FREQUENCY  # 0.5 Sekunden
MAX_PERIOD = 1.0 / MIN_FREQUENCY  # 2.0 Sekunden

# Anzahl der Flanken für Detektion
DETECTION_EDGES = 4  # Mindestens 2 komplette Zyklen

# Timeout für Toggling-Erkennung (in Sekunden)
TOGGLE_TIMEOUT = 3.0

# Pfad zur Rolladoino-Konfiguration
CONFIG_PATH = './rolladenAddr.json'


class AlarmMonitor:
    def __init__(self):
        self.toggling_active = False
        self.last_edge_time = None
        self.edge_times = []
        self.gpio_output_state = False
        self.config = self.load_config()
        
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_INPUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(GPIO_OUTPUT, GPIO.OUT)
        GPIO.output(GPIO_OUTPUT, GPIO.LOW)
        
        print("Alarm-Überwachung gestartet")
        print(f"Überwache GPIO{GPIO_INPUT}, Frequenzbereich: {MIN_FREQUENCY}-{MAX_FREQUENCY} Hz")
        print(f"Ausgang: GPIO{GPIO_OUTPUT}")
    
    def load_config(self):
        """Lade die Rolladoino-Konfiguration"""
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
            return {"devices": {"sunset": [], "dusk": []}}
    
    def send_summer_command(self, state):
        """Sende Summer-Befehl an alle Rolladoinos
        
        Args:
            state: 2 für Summer an, 0 für Summer aus
        """
        param = 2 if state else 0
        print(f"Sende CMD_Summer mit Parameter {param} an alle Rolladoinos...")
        
        # Durchlaufe alle Geräte in beiden Kategorien
        for category in ['sunset', 'dusk']:
            for device in self.config['devices'].get(category, []):
                try:
                    channel = device['channel']
                    address = int(device['address'], 16)
                    name = device.get('name', 'Unbekannt')
                    
                    print(f"  -> {name} ({channel}, {device['address']})")
                    Rolladoino.main('CMD_Summer', channel, address, param)
                    time.sleep(0.1)  # Kurze Pause zwischen den Befehlen
                    
                except Exception as e:
                    print(f"  Fehler bei {device.get('name', 'Unbekannt')}: {e}")
    
    def activate_alarm(self):
        """Aktiviere Alarm: GPIO13 auf HIGH, Summer an"""
        if not self.toggling_active:
            print(">>> ALARM AKTIVIERT <<<")
            self.toggling_active = True
            self.gpio_output_state = True
            GPIO.output(GPIO_OUTPUT, GPIO.HIGH)
            self.send_summer_command(True)
    
    def deactivate_alarm(self):
        """Deaktiviere Alarm: GPIO13 auf LOW, Summer aus"""
        if self.toggling_active:
            print(">>> ALARM DEAKTIVIERT <<<")
            self.toggling_active = False
            self.gpio_output_state = False
            GPIO.output(GPIO_OUTPUT, GPIO.LOW)
            self.send_summer_command(False)
    
    def check_frequency(self):
        """Prüfe ob die gesammelten Flanken im gültigen Frequenzbereich liegen"""
        if len(self.edge_times) < DETECTION_EDGES:
            return False
        
        # Berechne die Perioden zwischen den Flanken
        periods = []
        for i in range(1, len(self.edge_times)):
            period = self.edge_times[i] - self.edge_times[i-1]
            periods.append(period)
        
        # Prüfe ob alle Perioden im gültigen Bereich liegen
        # Eine volle Periode = 2 Flanken, also müssen wir die halbe Periode prüfen
        valid_periods = 0
        for period in periods:
            # Halbe Periode (Flanke zu Flanke)
            half_min = MIN_PERIOD / 2
            half_max = MAX_PERIOD / 2
            if half_min <= period <= half_max:
                valid_periods += 1
        
        # Wenn mindestens 75% der Perioden gültig sind
        return valid_periods >= len(periods) * 0.75
    
    def on_edge_detected(self, channel):
        """Callback für GPIO-Flankenänderung"""
        current_time = time.time()
        
        # Speichere Zeitpunkt
        self.edge_times.append(current_time)
        
        # Behalte nur die letzten DETECTION_EDGES Zeitpunkte
        if len(self.edge_times) > DETECTION_EDGES:
            self.edge_times.pop(0)
        
        # Prüfe ob Frequenz im gültigen Bereich liegt
        if self.check_frequency():
            self.activate_alarm()
            self.last_edge_time = current_time
    
    def run(self):
        """Hauptschleife"""
        try:
            # Setup Event-Detection für beide Flanken
            GPIO.add_event_detect(GPIO_INPUT, GPIO.BOTH, callback=self.on_edge_detected, bouncetime=50)
            
            print("Überwachung läuft... (Strg+C zum Beenden)")
            
            while True:
                # Prüfe ob Toggling gestoppt hat
                if self.toggling_active:
                    current_time = time.time()
                    if self.last_edge_time and (current_time - self.last_edge_time) > TOGGLE_TIMEOUT:
                        self.deactivate_alarm()
                        self.edge_times = []  # Reset edge buffer
                
                time.sleep(0.1)  # Kurze Pause um CPU zu schonen
                
        except KeyboardInterrupt:
            print("\nProgramm wird beendet...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Aufräumen beim Beenden"""
        print("Räume auf...")
        GPIO.cleanup()
        if self.toggling_active:
            # Stelle sicher, dass Summer ausgeschaltet wird
            self.send_summer_command(False)
        print("Programm beendet")


if __name__ == "__main__":
    monitor = AlarmMonitor()
    monitor.run()
