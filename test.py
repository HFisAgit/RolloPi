#!/usr/bin/env python

import sys
import time
import argparse

def setFloor(floor):
    I2C_address = 0x70

    return

def SendSingleByte(address, SendByte):

  print("Schreiben...")

  print("Lesen...")
  ret = 1

  return ret 


def SendTwoBytes(address, Command, Argument):
  
  print("Lesen...")
  ret = 2

  return ret


def main(cmd, floor, addr, ):
    pos = 0
    if(cmd=="CMD_Rolladen_Hoch"):
        print("CMD_Rolladen_Hoch")
        setFloor(floor)
        SendSingleByte(addr, 0x00)

    elif(cmd=="CMD_Rolladen_Runter"):
        print("CMD_Rolladen_Runter")
        setFloor(floor)
        SendSingleByte(addr, 0x06)

    elif(cmd=="CMD_Rolladen_Stop"):
        print("CMD_Rolladen_Stop")
        setFloor(floor)
        SendSingleByte(addr, 0x08)

    elif(cmd=="CMD_Luefter"):
        print("CMD_Luefter")
        setFloor(floor)
        SendTwoBytes(addr, 0x12, args.stufe)

    elif(cmd=="CMD_Read_Pos"):
        print("CMD_Read_Pos")
        setFloor(floor)
        pos = SendSingleByte(addr, 0x60)

    else:
        print("ERROR: Unknown command.")

    return pos


parser = argparse.ArgumentParser()
parser.add_argument("floor", help="Das stockwerk auf dem sich das Device befindet", choices=['ch1', 'ch2', 'ch3', 'ch4', 'ch5'])
parser.add_argument("address", help="Die Adresse des I2C device", type=lambda x: int(x,16))
parser.add_argument("command", help="Der Befehl, der ausgefuehrt werden soll. [CMD_Rolladen_Hoch ; CMD_Rolladen_Runter ; CMD_Rolladen_Stop ; CMD_Luefter ]")
parser.add_argument("--stufe", help="Die Stufe auf die der Luefter gesetzt werden soll", type=int, choices=[0,1,2,3])

args = parser.parse_args()

anwer = main(args.command, args.floor, args.address)
print(args.command)
print(anwer)