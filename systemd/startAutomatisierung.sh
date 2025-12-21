#!/bin/bash
echo "Starte RolloPi Automatisierungsskripte"
cd /home/pi/RolloPi
#RAM disk für dateien
mkdir -p /home/pi/RolloPi/ramdisk
sudo mount -t tmpfs -o size=100m tmpfs /home/pi/RolloPi/ramdisk
cp /home/pi/RolloPi/regeln.json /home/pi/RolloPi/ramdisk/regeln.json
cp /home/pi/RolloPi/suntimes.json /home/pi/RolloPi/ramdisk/suntimes.json
cp /home/pi/RolloPi/reloadRegeln.txt /home/pi/RolloPi/ramdisk/reloadRegeln.txt
#starte automatisierungs skripte
python3 luefterAutomatik.py 2>&1 | /bin/systemd-cat -t luefterAutomatik &
python3 rolladenAutomatik.py 2>&1 | /bin/systemd-cat -t rolladenAutomatik &
#python3 telefonUeberwachung.py &
python3 fritzboxCallMonitor.py 2>&1 | /bin/systemd-cat -t fritzboxCallMonitor &
python3 klingelUeberwachung.py 2>&1 | /bin/systemd-cat -t klingelUeberwachung &
python3 tempSensoren.py 2>&1 | /bin/systemd-cat -t tempSensoren &
#python3 hwtest.py &

echo "RolloPi Automatisierungsskripte gestartet"

