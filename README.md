Das ist ein Webserver, der auf einem RaspberryPi läuft und im Haus die Rolläden und Lüfter steuert 


#Autotart
Den Pfand in der Datei automatisierung.service anpassen.
Die Datei automatisierung.service nach /lib/systemd/system/ kopieren
Berechtigung setzen: sudo chmod 644 /lib/systemd/system/automatisierung.service

Configure systemd
sudo systemctl daemon-reload
sudo systemctl enable myservice.service

#Webseite
Die webseite ist mit PHP geschrieben.
Die Geräte werden hardcoded angelegt. Ist zwar nicht flexiebel aber einfach....
Die Seiten werden über die URL ausgewählt. 
Es gibt je eine Seite für die Lüfter und die Rolläden. Auf diesen können die Geräte manuel gesteuert werden.
Auf der Seite Regeln wird die aktuelle Konfiguration der automatik angezeigt und kann angepasst werden.
Es gibt noch weitere Seiten, die Aktionen ausführen (Rolläden fahren, Lüfter schalten) aber nichts anzeigen und automatisch auf die Rolladen- bzw Lüfter- Seite umleiten.
Die PHP, css Dateien und der ing Ordner müsssen nach /var/www/html kopiert werden. (Wahlweise Link) 
#Automatik
automatik.py wird über systemd automatisch gestartet.
Es liest die regeln.json ein und läuft dann in einer endlosschleife. alle 2 Sekunden wird überprüft, ob zu dieser Zeit eine aktion nötig ist.


#Rasbian OS

https://www.abelectronics.co.uk/kb/article/1/i2c--smbus-and-raspbian-linux

-activiere i2c:
sudo raspi-config

-install: 
sudo apt-get update
sudo apt install git vim 
sudo apt install python2 #Rolladoino.py is still python2.....
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
