Das ist ein Webserver, der auf einem RaspberryPi läuft und im Haus die Rolläden und Lüfter steuert 


#Autotart
Den Pfand in der Datei automatisierung.service anpassen.
Die Datei automatisierung.service nach /lib/systemd/system/ kopieren
Berechtigung setzen: sudo chmod 644 /lib/systemd/system/automatisierung.service

Configure systemd
sudo systemctl daemon-reload
sudo systemctl enable automatisierung.service

#Webseite
Die webseite ist mit PHP geschrieben.
Die Geräte werden hardcoded angelegt. Ist zwar nicht flexiebel aber einfach....
Die Seiten werden über die URL ausgewählt. 
Es gibt je eine Seite für die Lüfter und die Rolläden. Auf diesen können die Geräte manuel gesteuert werden.
Auf der Seite Regeln wird die aktuelle Konfiguration der automatik angezeigt und kann angepasst werden.
Es gibt noch weitere Seiten, die Aktionen ausführen (Rolläden fahren, Lüfter schalten) aber nichts anzeigen und automatisch auf die Rolladen- bzw Lüfter- Seite umleiten.
Die PHP, css Dateien und der img Ordner müsssen nach /var/www/html kopiert werden. (Wahlweise Link) 
#Automatik
automatik.py wird über systemd automatisch gestartet.
Es liest die regeln.json ein und läuft dann in einer endlosschleife. Alle 2 Sekunden wird überprüft, ob zu dieser Zeit eine aktion nötig ist.


#Rasbian OS

https://www.abelectronics.co.uk/kb/article/1/i2c--smbus-and-raspbian-linux

-activiere i2c:
sudo raspi-config

-activiere onewire:
sudo raspi-config

-install: 
sudo apt-get update
sudo apt install git vim 
sudo apt install python3 
sudo apt-get install python3-smbus python3-dev i2c-tools

-test i2c:
sudo i2cdetect -y 1

-python
wir brauchen python3 und python-is-python3
sudo apt-get install python3-pip

pip3 install suncalc
pip3 install python-dateutil

sudo apt install php

in /etc/passwd dem user www-data die /bin/bash als shell geben.

index.php, styles.css und img/ nach /var/www/html/ kopieren.


- logging:
Loginformationen finden sich im journald
journalctl -n 30 -u rolladenAutomatik.service 
journalctl -n 30 -u luefterAutomatik.service 
journalctl -n 30 -u fritzboxCallMonitor.service 
journalctl -n 30 -u klingelUeberwachung.service 
journalctl -n 30 -u tempSensoren.service 

journalctl -n 30 -t webseite

journal beenden mit "q" 

TODO:
# Alles was sich zwischen Golle und Crumscht unterscheidet in separate Dateien auslagern, um branches so nah wie möglich zusammen zu halten
    - Webseite in mehrere *.php files aufteilen und mit include('header.php'); einbinden
    - I2C Addressen in json auslagern - OK
    - Dateinamen eideutiger machen
    - Ordnerstruktur verbessern
    - Kommunikation auf WebSocket umstellen 
    - Für jeden Raum eine Seite anlegen, mit Hintergrundbild
    - API Dokumentieren
    
# Sonnensensor in betrieb nehmen
# Telefon Signal überwachen und Ton ausgeben
# Klingel Signal überwachen und Ton ausgeben - ok

