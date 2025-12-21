#!/bin/bash
# This script sets up the development environment
#!/bin/bash

# ist RolloPi vorhanden?
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

# Default: execute apt commands. Use -n/--no-apt to skip all apt calls.
DO_APT=1

usage() {
    echo "Usage: $0 [-n] [--no-apt] [-h] [--help]"
    echo "  -n, --no-apt   skip all apt update/install calls"
    echo "  -h, --help     show this help message"
}

# Parse short options with getopts; accept -n and -h
while getopts ":nh" opt; do
    case "$opt" in
        n)
            DO_APT=0
            ;;
        h)
            usage
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG"
            usage
            exit 1
            ;;
    esac
done
shift $((OPTIND -1))

# Support long options (--no-apt, --help) if provided
for arg in "$@"; do
    case "$arg" in
        --no-apt)
            DO_APT=0
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            usage
            exit 1
            ;;
    esac
done

# installiere benötigte pakete
echo "update apt und installiere pakete"
if [ "$DO_APT" -eq 1 ]; then
    sudo apt update
    sudo apt install -y git vim python3 
    sudo apt install -y python3-smbus python3-dev i2c-tools
    sudo apt install -y python3-pip
    sudo apt install -y php
    sudo apt install -y composer
else
    echo "--no-apt gesetzt: apt update/install wird übersprungen"
fi

# installiere benötigte logging fuer php module
cd /home/pi/RolloPi/webseite
composer require monolog/monolog
cd /home/pi/RolloPi

# installiere benötigte python module
pip3 install python-dateutil
pip3 install suncalc

# konfiguriere user www-data für den webserver zugriff auf I2C
echo "bearbeite user www-data"
usermod -s /bin/bash www-data

# kopiere webseite
echo "kopiere webseite"
sudo cp ./webseite/index.php /var/www/html/
sudo cp ./webseite/style.css /var/www/html/
sudo mkdir -p /var/www/html/img/
sudo cp ./webseite/img/* /var/www/html/img/
sudo cp ./webseite/hardware_config_Brentanoweg.json /var/www/html/hardware_config_Brentanoweg.json
sudo cp ./webseite/hardware_config_AmLohrein.json /var/www/html/hardware_config_AmLohrein.json
sudo cp -r ./webseite/vendor/ /var/www/html/vendor/

# konfiguriere systemd für autostart
echo "configuriere systemd"
sudo cp ./systemd/automatisierung.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/automatisierung.service
sudo systemctl daemon-reload
sudo systemctl enable automatisierung.service
sudo systemctl start automatisierung.service