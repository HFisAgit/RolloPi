#!/usr/bin/env python

import sys
import time
import smbus
import argparse
import TCA9548A

def setFloor(bus, floor):
    I2C_address = 0x70

    if(floor == 'EG'):
        subbus=5
    elif(floor=='OG'):
        subbus=3
    else:
        subbus=-1

    if(subbus > 0):
        print('set floor')
       # bus.write_byte(I2C_address,subbus)
        TCA9548A.I2C_setup(I2C_address,subbus)
        time.sleep(0.1)

    return

def SendSingleByte(bus, address, SendByte):

  print("Schreiben...")
  bus.write_byte(address, SendByte)

  print("Lesen...")
  bus.read_byte(address)

  return 


def SendTwoBytes(bus, address, Command, Argument):
  
  print("Schreiben...")
  bus.write_byte_data(address, Command, Argument) 

  print("Lesen...")
  bus.read_byte(address)



parser = argparse.ArgumentParser()
parser.add_argument("floor", help="Das stockwerk auf dem sich das Device befindet", choices=['EG', 'OG'])
parser.add_argument("address", help="Die Adresse des I2C device", type=lambda x: int(x,16))
parser.add_argument("command", help="Der Befehl, der ausgefuehrt werden soll. [CMD_Rolladen_Hoch ; CMD_Rolladen_Runter ; CMD_Rolladen_Stop ; CMD_Luefter ]")
parser.add_argument("--stufe", help="Die Stufe auf die der Luefter gesetzt werden soll", type=int, choices=[0,1,2,3])

args = parser.parse_args()

bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

if(args.command=="CMD_Rolladen_Hoch"):
    print("CMD_Rolladen_Hoch")
    setFloor(bus, args.floor)
    SendSingleByte(bus, args.address, 0x00)

elif(args.command=="CMD_Rolladen_Runter"):
    print("CMD_Rolladen_Runter")
    setFloor(bus, args.floor)
    SendSingleByte(bus, args.address, 0x06)

elif(args.command=="CMD_Rolladen_Stop"):
    print("CMD_Rolladen_Stop")
    setFloor(bus, args.floor)
    SendSingleByte(bus, args.address, 0x08)

elif(args.command=="CMD_Luefter"):
    print("CMD_Luefter")
    setFloor(bus, args.floor)
    SendTwoBytes(bus, args.address, 0x12, args.stufe)

else:
    print("ERROR: Unknown command.")
