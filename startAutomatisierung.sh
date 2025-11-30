#!/bin/bash
cd /home/pi/RolloPi
echo "start rolladen und lufter" >> startAutom.log
python3 LuefterAutomatik.py &
python3 rolladenAutomatik.py &
#python3 hwtest.py &

