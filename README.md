Das ist ein Webserver, der auf einem RaspberryPi läuft und im Haus die Rolläden und Lüfter seuert 


#Autotart
die datei automatisierung.service nach /lib/systemd/system/ kopieren
Berechtigung setzen: sudo chmod 644 /lib/systemd/system/automatisierung.service

Configure systemd
sudo systemctl daemon-reload
sudo systemctl enable myservice.service

