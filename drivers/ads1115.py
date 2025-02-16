#!/usr/bin/env python3

import time
import smbus
import TCA9548A

# ADS1115 + hardware constants
I2C_BUS = 1
DEVICE_ADDRESS = 0x48
# ADS1115 Register adress
POINTER_CONVERSION = 0x0
POINTER_CONFIGURATION = 0x1
POINTER_LOW_THRESHOLD = 0x2
POINTER_HIGH_THRESHOLD = 0x3

RESET_ADDRESS = 0b0000000
RESET_COMMAND = 0b00000110
 
# Open I2C device
BUS = smbus.SMBus(I2C_BUS)
BUS.open(I2C_BUS)
 

# helper functions:
def swap2Bytes(c):
    '''Revert Byte order for Words (2 Bytes, 16 Bit).'''
    return (c>>8 |c<<8)&0xFFFF
 
def prepareLEconf(BEconf):
    '''Prepare LittleEndian Byte pattern from BigEndian configuration string, with separators.'''
    c = int(BEconf.replace('-',''), base=2)
    return swap2Bytes(c)
 
def LEtoBE(c):
    '''Little Endian to BigEndian conversion for signed 2Byte integers (2 complement).'''
    c = swap2Bytes(c)
    if(c >= 2**15):
        c= c-2**16
    return c
 
def BEtoLE(c):
    '''BigEndian to LittleEndian conversion for signed 2 Byte integers (2 complement).'''
    if(c < 0):
        c= 2**16 + c
    return swap2Bytes(c)
 
def resetChip():
    BUS.write_byte(RESET_ADDRESS, RESET_COMMAND)
    return


def setFloor():
    I2C_address = 0x70
    subbus=7

    TCA9548A.I2C_setup(I2C_address,subbus)
    time.sleep(0.1)

    return

def readSingle(input):
    setFloor()
    
    inbm = '100'
    if(input == 0):
        inbm = '100'
    elif(input == 1):
        inbm = '101'
    elif(input == 2):
        inbm = '110'
    elif(input == 3):
        inbm = '111'
    else:
        print("Input out of range")

    # Bitmask for config register (datasheet 9.6.3)
    # compare with configuration settings from ADS115 datasheet
    # start single conversion - AIN2/GND - 4.096V - single shot - 8SPS - X
    # - X - X - disable comparator
    conf = prepareLEconf('1-' + inbm + '-001-1-000-0-0-0-11')
 
    BUS.write_word_data(DEVICE_ADDRESS, POINTER_CONFIGURATION, conf)
    # long enough to be safe that data acquisition (conversion) has completed
    # may be calculated from data rate + some extra time for safety.
    # check accuracy in any case.
    time.sleep(0.2)
    value_raw = BUS.read_word_data(DEVICE_ADDRESS, POINTER_CONVERSION)
    value = LEtoBE(value_raw)
    
    return value

#test program
setFloor()
value = readSingle(1)
print("Value: " + str(value))
      