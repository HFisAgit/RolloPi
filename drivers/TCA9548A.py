#!/usr/bin/python
# I2C Switch - 4 channels used
# channel 0 - Rolladoino 1
# channel 1 - Rolladoino 2
# channel 2 - Rolladoino 3
# channel 3 - Rolladoino 4
# channel 4 - Rolladoino 5
# channel 5 - X12
# channel 6 - X23
# channel 7 - ads1115 ADC
# intended for import to change channel of TCA9548A
# import then call I2C_setup(multiplexer_addr,multiplexer_channel)

import smbus
import time
import sys

channel_array=[0b00000001,0b00000010,0b00000100,0b00001000,0b00010000,0b00100000,0b01000000,0b10000000]

def I2C_setup(multiplexer,i2c_channel_setup):
    bus = smbus.SMBus(1)
    bus.write_byte(multiplexer,channel_array[i2c_channel_setup])
    time.sleep(0.01)
    #uncomment to debug #print("TCA9548A I2C channel status:", bin(bus.read_byte(multiplexer)))

