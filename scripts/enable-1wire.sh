#!/bin/bash

# Enable 1-Wire interface on Raspberry Pi

# Add the necessary configuration to /boot/config.txt
if ! grep -q "^dtoverlay=w1-gpio" /boot/config.txt; then
    echo "dtoverlay=w1-gpio" | sudo tee -a /boot/config.txt
fi

# Load the 1-Wire kernel module
if ! grep -q "^w1-gpio" /etc/modules; then
    echo "w1-gpio" | sudo tee -a /etc/modules
fi

if ! grep -q "^w1-therm" /etc/modules; then
    echo "w1-therm" | sudo tee -a /etc/modules
fi

# Reboot the system to apply changes
echo "1-Wire interface enabled. Please reboot your Raspberry Pi for the changes to take effect."