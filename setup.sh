#!/bin/bash
# This script sets up the development environment
#!/bin/bash

if [ "$PWD" = "/home/pi/RolloPi" ]; then
    echo "Du befindest dich im richtigen Verzeichnis!"
else
    echo "Du bist NICHT im /home/pi/RolloPi Verzeichnis."
    echo "clone dieses Reop nach /home/pi/RolloPi und starte das script erneut"
    exit 1
fi

echo "Setting up the development environment..."
echo "Bitte aktivirer I2C und 1-wire mit dem tool 'raspi-config'"
echo "sudo raspi-config"
#bash ./scripts/enable-i2c.sh
#bash ./scripts/enable-1wire.sh

echo "update apt und installiere pakete"
sudo apt update
sudo apt install -y git vim python3 
sudo apt install -y python3-smbus python3-dev i2c-tools
sudo apt install -y python3-pip
sudo apt install -y php

pip3 install python-dateutil
pip3 install suncalc

echo "bearbeite user www-data"
usermod -s /bin/bash www-data

echo "kopiere webseite"
sudo cp ./webseite/index.php /var/www/html/
sudo cp ./webseite/style.css /var/www/html/
sudo mkdir -p /var/www/html/img/
sudo cp ./webseite/img/* /var/www/html/img/

echo "configuriere systemd"
sudo cp ./systemd/automatisierung.service /lib/systemd/system/
sudo chmod 644 /lib/systemd/system/automatisierung.service
sudo systemctl daemon-reload
sudo systemctl enable automatisierung.service
sudo systemctl start automatisierung.service