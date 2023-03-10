Das ist ein Webserver, der auf einem RaspberryPi läuft und im Haus die Rolläden und Lüfter steuert 


#Autotart
die datei automatisierung.service nach /lib/systemd/system/ kopieren
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

#Automatik
automatik.py wird über systemd automatisch gestartet.
Es liest die regeln.json ein und läuft dann in einer endlosschleife. alle 2 Sekunden wird überprüft, ob zu dieser Zeit eine aktion nötig ist.
