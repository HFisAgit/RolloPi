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
echo "Füge www-data zur i2c-Gruppe hinzu und erstelle udev-Regel für i2c-Geräte"
if ! getent group i2c >/dev/null 2>&1; then
    echo "Gruppe 'i2c' existiert nicht, erstelle sie"
    sudo groupadd i2c || true
fi
sudo usermod -a -G i2c www-data

# Erstelle udev-Regel, die i2c-Geräte für Gruppe i2c lesbar/ Schreibbar macht
#UDEV_RULE="/etc/udev/rules.d/99-i2c.rules"
#echo "KERNEL==\"i2c-[0-9]*\", MODE=\"0660\", GROUP=\"i2c\"" | sudo tee "$UDEV_RULE" >/dev/null
#sudo udevadm control --reload-rules && sudo udevadm trigger
#echo "udev-Regel $UDEV_RULE gesetzt und Regeln neu geladen"

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
sudo cp ./systemd/rolladenAutomatk.service /etc/systemd/system/
sudo cp ./systemd/lueferAutomatk.service /etc/systemd/system/
sudo cp ./systemd/fritzboxCallMonitor.service /etc/systemd/system/
sudo cp ./systemd/klingelUeberwachung.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/rolladenAutomatk.service
sudo chmod 644 /etc/systemd/system/lueferAutomatk.service
sudo chmod 644 /etc/systemd/system/fritzboxCallMonitor.service
sudo chmod 644 /etc/systemd/system/klingelUeberwachung.service
sudo systemctl daemon-reload
sudo systemctl enable rolladenAutomatk.service
sudo systemctl enable lueferAutomatk.service
sudo systemctl enable fritzboxCallMonitor.service
sudo systemctl enable klingelUeberwachung.service
sudo systemctl start rolladenAutomatk.service
sudo systemctl start lueferAutomatk.service
sudo systemctl start fritzboxCallMonitor.service
sudo systemctl start klingelUeberwachung.service