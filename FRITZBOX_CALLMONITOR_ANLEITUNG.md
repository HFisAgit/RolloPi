# Fritzbox CallMonitor - Anleitung

## CallMonitor in der Fritzbox aktivieren

Der CallMonitor ist eine versteckte Funktion der Fritzbox, die über einen speziellen Code aktiviert werden muss.

### Aktivierung per Telefon:

1. Nehmen Sie ein an der Fritzbox angeschlossenes Telefon (DECT oder analog)
2. Wählen Sie folgende Tastenkombination:
   ```
   #96*5*
   ```
3. Sie sollten eine Bestätigung hören oder sehen
4. Der CallMonitor ist nun auf Port 1012 aktiv

### Deaktivierung (falls gewünscht):

Falls Sie den CallMonitor wieder deaktivieren möchten:
```
#96*4*
```

### Alternative Aktivierung per Browser (Fritz!OS ab 7.x):

1. Öffnen Sie Ihren Browser und geben Sie ein:
   ```
   http://fritz.box/fon_num/foncalls_list.lua
   ```
2. Der CallMonitor sollte automatisch aktiviert werden

### Verbindungstest

Sie können testen, ob der CallMonitor aktiv ist, indem Sie sich per Telnet verbinden:

```bash
telnet 192.168.178.1 1012
```

Wenn die Verbindung erfolgreich ist, sehen Sie bei jedem Anruf Meldungen im Format:
```
Datum;Typ;ConnectionID;Rufnummer;Angerufene Nummer;SIP
```

Beispiel für einen eingehenden Anruf:
```
08.12.24 14:23:45;RING;0;012345678;987654;SIP0;
```

## Konfiguration

Passen Sie die Datei `fritzbox_config.json` an Ihre Fritzbox an:

```json
{
    "fritzbox": {
        "host": "192.168.178.1",
        "port": 1012,
        "timeout": 30
    }
}
```

- **host**: IP-Adresse Ihrer Fritzbox (Standard: 192.168.178.1)
- **port**: CallMonitor Port (Standard: 1012, nicht ändern)
- **timeout**: Socket-Timeout in Sekunden

## Verwendung

### Das Skript ausführen:

```bash
sudo python3 fritzboxCallMonitor.py
```

(sudo wird für GPIO-Zugriff benötigt)


## Funktionsweise

1. Das Skript verbindet sich mit dem CallMonitor der Fritzbox (Port 1012)
2. Bei jedem eingehenden Anruf (Event-Typ "RING") wird:
   - GPIO 13 auf HIGH gesetzt
   - Der Befehl `CMD_Summer` mit Parameter 2 an alle Rolladoinos gesendet
3. Nach 10 Sekunden (konfigurierbar über `ALARM_DURATION` im Skript) wird:
   - GPIO 13 auf LOW gesetzt
   - Der Befehl `CMD_Summer` mit Parameter 0 an alle Rolladoinos gesendet

## Troubleshooting

### "Verbindung fehlgeschlagen"
- Prüfen Sie, ob der CallMonitor aktiviert ist (#96*5*)
- Prüfen Sie die IP-Adresse in `fritzbox_config.json`
- Prüfen Sie, ob Port 1012 erreichbar ist: `telnet 192.168.178.1 1012`

### "Permission denied" beim GPIO-Zugriff
- Führen Sie das Skript mit `sudo` aus

### Keine Rolladoino-Reaktion
- Prüfen Sie die `rolladenAddr.json` Konfiguration
- Prüfen Sie die I2C-Verbindungen zu den Rolladoinos

## CallMonitor Event-Typen

Der Fritzbox CallMonitor sendet verschiedene Event-Typen:

- **RING**: Eingehender Anruf (löst Alarm aus)
- **CALL**: Ausgehender Anruf
- **CONNECT**: Verbindung hergestellt
- **DISCONNECT**: Gespräch beendet

Aktuell reagiert das Skript nur auf **RING**-Events.
