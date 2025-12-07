#!/usr/bin/env python

import sys
import time
import smbus
import argparse
import TCA9548A

def setFloor(bus, floor):
    I2C_address = 0x70

    if(floor == 'EGN'):
        subbus=0
    elif(floor == 'EGS'):
        subbus=1
    elif(floor=='OGN'):
        subbus=2
    elif(floor=='OGS'):
        subbus=3
    else:
        subbus=-1

    if(subbus >= 0):
        print('set floor')
       # bus.write_byte(I2C_address,subbus)
        TCA9548A.I2C_setup(I2C_address,subbus) # reaktivate when seperate buses
        time.sleep(0.1)

    return

def SendSingleByte(bus, address, SendByte):

  print("Schreiben...")
  bus.write_byte(address, SendByte)

  print("Lesen...")
  ret = bus.read_byte(address)

  return ret 


def SendTwoBytes(bus, address, Command, Argument):
  
  print("Schreiben...")
  bus.write_byte_data(address, Command, Argument) 

  print("Lesen...")
  ret = bus.read_byte(address)

  return ret

def main(cmd, floor, addr, param=0):
    bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

    if(cmd=="CMD_Rolladen_Hoch"):
        print("CMD_Rolladen_Hoch")
        setFloor(bus, floor)
        SendSingleByte(bus, addr, 0x00)
        return None

    elif(cmd=="CMD_Rolladen_Runter"):
        print("CMD_Rolladen_Runter")
        setFloor(bus, floor)
        SendSingleByte(bus, addr, 0x06)
        return None

    elif(cmd=="CMD_Rolladen_Stop"):
        print("CMD_Rolladen_Stop")
        setFloor(bus, floor)
        SendSingleByte(bus, addr, 0x08)
        return None

    elif(cmd=="CMD_Luefter"):
        print("CMD_Luefter")
        setFloor(bus, floor)
        SendTwoBytes(bus, addr, 0x12, param)
        return None

    elif(cmd=="CMD_Read_Pos"):
        print("CMD_Read_Pos")
        setFloor(bus, floor)
        pos = SendSingleByte(bus, addr, 0x60)
        return pos

    elif(cmd=="CMD_Summer"):
        print("CMD_Summer")
        setFloor(bus, floor)
        SendTwoBytes(bus, addr, 0x13, param)
        return None

    else:
        print("ERROR: Unknown command.")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("floor", help="Das stockwerk auf dem sich das Device befindet", choices=['EGN', 'EGS', 'OGN', 'OGS'])
    parser.add_argument("address", help="Die Adresse des I2C device", type=lambda x: int(x,16))
    parser.add_argument("command", help="Der Befehl, der ausgefuehrt werden soll. [CMD_Rolladen_Hoch ; CMD_Rolladen_Runter ; CMD_Rolladen_Stop ; CMD_Luefter ; CMD_Read_Pos ; CMD_Summer ]")
    parser.add_argument("--stufe", help="Die Stufe auf die der Luefter gesetzt werden soll", type=int, choices=[0,1,2,3])
    parser.add_argument("--summer", help="Summer an (2) oder aus (0)", type=int, choices=[0,1,2])
    args = parser.parse_args()
    
    bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    
    # Wähle den richtigen Parameter basierend auf dem Befehl
    if args.command == "CMD_Summer":
        param = args.summer if args.summer is not None else 0
    elif args.command == "CMD_Luefter":
        param = args.stufe if args.stufe is not None else 0
    else:
        param = args.stufe if args.stufe is not None else 0
    
    main(args.command, args.floor, args.address, param)
    #print(args.command)args.floor, args.address, args.stufe) # !! What if stufe is empty???
    print(args.command)

