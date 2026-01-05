#!/usr/bin/env python3
"""
Fritzbox CallMonitor-Überwachungsskript
Überwacht eingehende Anrufe via Fritzbox CallMonitor und aktiviert GPIO13 sowie den Summer an allen Rolladoinos
"""

import socket
import time
import json
import sys
import os
import re
from datetime import datetime

# Importiere GPIO und Rolladoino-Modul
import RPi.GPIO as GPIO
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'drivers'))
import drivers.Rolladoino as Rolladoino

# GPIO Konfiguration
GPIO_OUTPUT = 13    # Ausgang zum Setzen

# Pfade zu Konfigurationsdateien
FRITZBOX_CONFIG_PATH = './fritzbox_config.json'
ROLLADEN_CONFIG_PATH = './rolladenAddr.json'

# Alarm-Dauer in Sekunden (wie lange der Summer nach einem Anruf aktiv bleibt)
ALARM_DURATION = 10


class FritzboxCallMonitor:
    def __init__(self):
        self.socket = None
        self.alarm_active = False
        self.alarm_end_time = None
        
        # Lade Konfigurationen
        self.fritzbox_config = self.load_fritzbox_config()
        self.rolladen_config = self.load_rolladen_config()
        
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_OUTPUT, GPIO.OUT)
        GPIO.output(GPIO_OUTPUT, GPIO.LOW)
        
        print("Fritzbox CallMonitor-Überwachung gestartet")
        print(f"Fritzbox: {self.fritzbox_config['host']}:{self.fritzbox_config['port']}")
        print(f"Ausgang: GPIO{GPIO_OUTPUT}")
    
    def load_fritzbox_config(self):
        """Lade die Fritzbox-Konfiguration"""
        try:
            with open(FRITZBOX_CONFIG_PATH, 'r') as f:
                config = json.load(f)
                return config['fritzbox']
        except Exception as e:
            print(f"Fehler beim Laden der Fritzbox-Konfiguration: {e}")
            print("Verwende Standardwerte...")
            return {
                "host": "192.168.178.1",
                "port": 1012,
                "timeout": 30
            }
    
    def load_rolladen_config(self):
        """Lade die Rolladoino-Konfiguration"""
        try:
            with open(ROLLADEN_CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der Rolladen-Konfiguration: {e}")
            return {"devices": {"sunset": [], "dusk": []}}
    
    def send_summer_command(self, state):
        """Sende Summer-Befehl an alle Rolladoinos
        
        Args:
            state: True für Summer an, False für Summer aus
        """
        param = 2 if state else 0
        print(f"Sende CMD_Summer mit Parameter {param} an alle Rolladoinos...")
        
        # Durchlaufe alle Geräte in beiden Kategorien
        for category in ['sunset', 'dusk']:
            for device in self.rolladen_config['devices'].get(category, []):
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
        print(">>> ALARM AKTIVIERT - EINGEHENDER ANRUF <<<")
        self.alarm_active = True
        self.alarm_end_time = time.time() + ALARM_DURATION
        GPIO.output(GPIO_OUTPUT, GPIO.HIGH)
        self.send_summer_command(True)
    
    def deactivate_alarm(self):
        """Deaktiviere Alarm: GPIO13 auf LOW, Summer aus"""
        if self.alarm_active:
            print(">>> ALARM DEAKTIVIERT <<<")
            self.alarm_active = False
            self.alarm_end_time = None
            GPIO.output(GPIO_OUTPUT, GPIO.LOW)
            self.send_summer_command(False)
    
    def check_alarm_timeout(self):
        """Prüfe ob Alarm-Timeout erreicht wurde"""
        if self.alarm_active and self.alarm_end_time:
            if time.time() >= self.alarm_end_time:
                self.deactivate_alarm()
    
    def parse_call_monitor_line(self, line):
        """Parse eine Zeile vom CallMonitor
        
        Format: Datum;Typ;ConnectionID;Rufnummer;Angerufene Nummer;SIP
        Typ: RING = eingehender Anruf, CALL = ausgehender Anruf, CONNECT = Verbindung, DISCONNECT = Auflegen
        """
        try:
            parts = line.strip().split(';')
            if len(parts) < 2:
                return None
            
            timestamp = parts[0]
            event_type = parts[1]
            
            return {
                'timestamp': timestamp,
                'type': event_type,
                'raw': line.strip()
            }
        except Exception as e:
            print(f"Fehler beim Parsen der Zeile: {e}")
            return None
    
    def connect_to_fritzbox(self):
        """Verbinde mit dem Fritzbox CallMonitor"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                print(f"Verbinde mit Fritzbox ({self.fritzbox_config['host']}:{self.fritzbox_config['port']})...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(self.fritzbox_config['timeout'])
                self.socket.connect((self.fritzbox_config['host'], self.fritzbox_config['port']))
                print("Verbindung hergestellt!")
                return True
            except Exception as e:
                print(f"Verbindungsversuch {attempt + 1}/{max_retries} fehlgeschlagen: {e}")
                if self.socket:
                    self.socket.close()
                    self.socket = None
                if attempt < max_retries - 1:
                    print(f"Warte {retry_delay} Sekunden vor erneutem Versuch...")
                    time.sleep(retry_delay)
        
        return False
    
    def run(self):
        """Hauptschleife"""
        try:
            if not self.connect_to_fritzbox():
                print("Konnte keine Verbindung zur Fritzbox herstellen. Programm wird beendet.")
                return
            
            print("Überwachung läuft... (Strg+C zum Beenden)")
            print("Warte auf eingehende Anrufe...")
            
            buffer = ""
            
            while True:
                # Prüfe Alarm-Timeout
                self.check_alarm_timeout()
                
                try:
                    # Empfange Daten vom CallMonitor
                    data = self.socket.recv(1024)
                    if not data:
                        print("Verbindung zur Fritzbox verloren. Versuche Reconnect...")
                        if not self.connect_to_fritzbox():
                            break
                        continue
                    
                    # Dekodiere Daten
                    buffer += data.decode('utf-8', errors='ignore')
                    
                    # Verarbeite vollständige Zeilen
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            event = self.parse_call_monitor_line(line)
                            if event:
                                timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                print(f"[{timestamp_str}] Event: {event['type']}")
                                print(f"  Raw: {event['raw']}")
                                
                                # Bei eingehendem Anruf (RING) Alarm aktivieren
                                if event['type'] == 'RING':
                                    self.activate_alarm()
                
                except socket.timeout:
                    # Timeout ist normal, einfach weitermachen
                    continue
                except Exception as e:
                    print(f"Fehler beim Empfangen: {e}")
                    print("Versuche Reconnect...")
                    if not self.connect_to_fritzbox():
                        break
                
                time.sleep(0.1)  # Kurze Pause um CPU zu schonen
                
        except KeyboardInterrupt:
            print("\nProgramm wird beendet...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Aufräumen beim Beenden"""
        print("Räume auf...")
        
        # Schließe Socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        # Deaktiviere Alarm falls aktiv
        if self.alarm_active:
            self.send_summer_command(False)
        
        # GPIO cleanup
        GPIO.cleanup()
        print("Programm beendet")


if __name__ == "__main__":
    print('Starte Fritzbox CallMonitor Überwachung')
    monitor = FritzboxCallMonitor()
    monitor.run()
