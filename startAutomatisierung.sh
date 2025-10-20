#!/bin/bash
cd /home/pi/RolloPi
#RAM disk für dateien
sudo mount -t tmpfs -o size=100m tmpfs /home/pi/RolloPi/ramdisk
cp /home/pi/RolloPi/regeln.json /home/pi/RolloPi/ramdisk/regeln.json
cp /home/pi/RolloPi/suntimes.json /home/pi/RolloPi/ramdisk/suntimes.json
cp /home/pi/RolloPi/reloadRegeln.txt /home/pi/RolloPi/ramdisk/reloadRegeln.txt
#starte automatisierungs skripte
python3 LuefterAutomatik.py &
python3 rolladenAutomatik.py &
#python3 hwtest.py &

