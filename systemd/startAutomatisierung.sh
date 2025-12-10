#!/bin/bash
cd /home/pi/RolloPi
#RAM disk für dateien
mkdir -p /home/pi/RolloPi/ramdisk
sudo mount -t tmpfs -o size=100m tmpfs /home/pi/RolloPi/ramdisk
cp /home/pi/RolloPi/regeln.json /home/pi/RolloPi/ramdisk/regeln.json
cp /home/pi/RolloPi/suntimes.json /home/pi/RolloPi/ramdisk/suntimes.json
cp /home/pi/RolloPi/reloadRegeln.txt /home/pi/RolloPi/ramdisk/reloadRegeln.txt
#starte automatisierungs skripte
python3 luefterAutomatik.py &
python3 rolladenAutomatik.py &
#python3 telefonUeberwachung.py &
python3 fritzboxCallMonitor.py &
python3 klingelUeberwachung.py &
python2 tempsensoren.py &
#python3 hwtest.py &

