#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Klingel-Überwachungsskript
Überwacht GPIO6 (HIGH = klingeln) und setzt GPIO19 sowie den Summer über Rolladoino.
"""

import RPi.GPIO as GPIO
import time
import json
import sys
import os

# Rolladoino-Modul aus dem drivers-Verzeichnis importieren
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'drivers'))
import Rolladoino

# GPIO-Konfiguration
GPIO_INPUT = 6    # Klingel-Eingang
GPIO_OUTPUT = 19  # Ausgang zur Anzeige

# Pfad zur Rolladoino-Konfiguration (wie im Repo)
#CONFIG_PATH = './rolladenAddr.json'
CONFIG_PATH = './luefterAddr.json'

# Entprellzeit für Event-Detection (ms)
BOUNCE_MS = 50

class KlingelMonitor:
    def __init__(self):
        self.active = False
        self.config = self.load_config()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_INPUT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(GPIO_OUTPUT, GPIO.OUT)
        GPIO.output(GPIO_OUTPUT, GPIO.LOW)

        # Setze initialen Zustand entsprechend dem Eingangspegel
        initial = GPIO.input(GPIO_INPUT)
        if initial:
            self.activate()

        print("Klingel-Überwachung gestartet")
        print(f"Eingang: GPIO{GPIO_INPUT}, Ausgang: GPIO{GPIO_OUTPUT}")

    def load_config(self):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                print(data)
                return data
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration '{CONFIG_PATH}': {e}")
            return {"devices": [] }

    def send_summer_command(self, state):
        """
        Sende CMD_Summer an alle konfigurierten Rolladoinos.
        state: True -> param 1 (summen), False -> param 0 (aus)
        """
        param = 1 if state else 0
        print(f"Sende CMD_Summer, param={param}")
        for device in self.config.get('devices', {}):
            try:
                channel = device['channel']
                address = int(device['address'], 16)
                name = device.get('name', 'Unbekannt')
                print(f"  -> {name} ({channel}, {device['address']})")
                Rolladoino.main('CMD_Summer', channel, address, param)
                time.sleep(0.05)
            except Exception as e:
                print(f"  Fehler bei {device.get('name', 'Unbekannt')}: {e}")

    def activate(self):
        if not self.active:
            print("Klingel: AN")
            self.active = True
            GPIO.output(GPIO_OUTPUT, GPIO.HIGH)
            self.send_summer_command(True)

    def deactivate(self):
        if self.active:
            print("Klingel: AUS")
            self.active = False
            GPIO.output(GPIO_OUTPUT, GPIO.LOW)
            #self.send_summer_command(True)

    def on_edge(self, channel):
        # Lese aktuellen Pegel und schalte entsprechend
        try:
            val = GPIO.input(GPIO_INPUT)
            if val:
                self.deactivate()
            else:
                self.activate()
        except Exception as e:
            print(f"Fehler im Edge-Callback: {e}")

    def run(self):
        try:
            GPIO.add_event_detect(GPIO_INPUT, GPIO.BOTH, callback=self.on_edge, bouncetime=BOUNCE_MS)
            print("Überwachung läuft... (Strg+C zum Beenden)")
            while True:
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\nBeende Überwachung...")
        finally:
            self.cleanup()

    def cleanup(self):
        print("Räume auf...")
        # Stelle sicher, dass Summer ausgeschaltet wird
        if self.active:
            self.send_summer_command(False)
        GPIO.cleanup()
        print("Fertig.")

if __name__ == "__main__":
    monitor = KlingelMonitor()
    monitor.run()