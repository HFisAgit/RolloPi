#!/bin/bash

# Enable I2C on Raspberry Pi

# Load I2C kernel module
echo "Loading I2C kernel module..."
sudo modprobe i2c-dev

# Update config.txt to enable I2C
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "Enabling I2C in /boot/config.txt..."
    echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
else
    echo "I2C is already enabled in /boot/config.txt."
fi

# Update modules to load I2C modules on boot
if ! grep -q "^i2c-dev" /etc/modules; then
    echo "Adding i2c-dev to /etc/modules..."
    echo "i2c-dev" | sudo tee -a /etc/modules
else
    echo "i2c-dev is already present in /etc/modules."
fi

echo "I2C bus has been enabled."