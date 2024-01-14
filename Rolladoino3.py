#!/usr/bin/env python

import sys
import smbus
#from smbus2 import SMBus


def SendSingleByte(SendByte):

  bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

  DEVICE_ADDRESS = int(sys.argv[1],16)   
  print(DEVICE_ADDRESS)

  print("Schreiben...")
  bus.write_byte(DEVICE_ADDRESS, SendByte)

  print("Lesen...")
  bus.read_byte(DEVICE_ADDRESS)

  return 

def SendTwoBytes(Command, Argument):
  
  bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

  DEVICE_ADDRESS = int(sys.argv[1],16)   
  print(DEVICE_ADDRESS)

  print("Schreiben...")
  bus.write_byte_data(DEVICE_ADDRESS, Command, Argument) 

  print("Lesen...")
  bus.read_byte(DEVICE_ADDRESS)

def ReceiveTwoBytes(Command):

  bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

  DEVICE_ADDRESS = int(sys.argv[1],16)   

  print("Schreiben...")
  bus.write_byte(DEVICE_ADDRESS, Command)

  print("Lesen...")
  byte1 = bus.read_byte(DEVICE_ADDRESS)
  print (byte1)

  print("Lesen...")
  byte2 = bus.read_byte(DEVICE_ADDRESS)
  print (byte2)
  
  return byte1*255+byte2

if len(sys.argv) > 2:

  print(sys.argv[2])

  if str(sys.argv[2]) == "CMD_Rolladen_Hoch":
    SendSingleByte(0x00)

  elif str(sys.argv[2]) == "CMD_Rolladen_Pos1":
    #  SendSingleByte(0x01)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Rolladen_Pos2":
    SendSingleByte(0x02)

  elif str(sys.argv[2]) == "CMD_Rolladen_Pos3":
    #SendSingleByte(0x03)
    print("Error Position not avalible")
  
  elif str(sys.argv[2]) == "CMD_Rolladen_Pos4":
    SendSingleByte(0x04)
  
  elif str(sys.argv[2]) == "CMD_Rolladen_Pos5":
    #SendSingleByte(0x05)
    print("Error Position not avalible")
  
  elif str(sys.argv[2]) == "CMD_Rolladen_Runter":
    SendSingleByte(0x06)

  elif str(sys.argv[2]) == "CMD_Rolladen_PosX":
    if len(sys.argv) > 3:
      SendTwoBytes(0x07,int(sys.argv[3],16))

  elif str(sys.argv[2]) == "CMD_Rolladen_Stop":
    SendSingleByte(0x08)

  elif str(sys.argv[2]) == "CMD_Auto_Pos":
    SendSingleByte(0x09)

  elif str(sys.argv[2]) == "CMD_Auto":
    if len(sys.argv) > 3:
      SendTwoBytes(0x10,int(sys.argv[3],16))

  elif str(sys.argv[2]) == "CMD_Abendlicht":
    if len(sys.argv) > 3:
      SendTwoBytes(0x11,int(sys.argv[3],16))

  elif str(sys.argv[2]) == "CMD_Luefter":
    if len(sys.argv) > 3:
      SendTwoBytes(0x12,int(sys.argv[3],16))

  elif str(sys.argv[2]) == "CMD_Summer":
    if len(sys.argv) > 3:
      SendTwoBytes(0x13,int(sys.argv[3],16))

  elif str(sys.argv[2]) == "CMD_Set_Pos1":
    SendSingleByte(0x21)
  
  elif str(sys.argv[2]) == "CMD_Set_Pos2":
    SendSingleByte(0x22)
  
  elif str(sys.argv[2]) == "CMD_Set_Pos3":
    SendSingleByte(0x23)
  
  elif str(sys.argv[2]) == "CMD_Set_Pos4":
    SendSingelByte(0x24)
  
  elif str(sys.argv[2]) == "CMD_Set_Pos5":
    SendSingleByte(0x25)
  
  elif str(sys.argv[2]) == "CMD_Set_PosMax":
    if len(sys.argv) > 3:
      #SendTwoBytes(0x26,int(sys.argv[3],16))
      print("Error Position not avalible")
  
  elif str(sys.argv[2]) == "CMD_Set_Luefter_Zeit":
    if len(sys.argv) > 3:
      #SendTwoBytes(0x27,int(sys.argv[3],16))
      print("Error Position not avalible")
  
  elif str(sys.argv[2]) == "CMD_Rolladen_Enable":
    if len(sys.argv) > 3:
      #SendTwoBytes(0x30,int(sys.argv[3],16))
      print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_Strom_Rolladen":
    print( ReceiveTwoBytes(0x40)) 
  
  elif str(sys.argv[2]) == "CMD_Read_Licht":
    print( ReceiveTwoBytes(0x41) )
  
  elif str(sys.argv[2]) == "CMD_Read_Temperatur":
    print( ReceiveTwoBytes(0x42)) 
  
  elif str(sys.argv[2]) == "CMD_Read_Feuchte":
    print( ReceiveTwoBytes(0x43) )

  elif str(sys.argv[2]) == "CMD_Read_Auto":
    #print ReceiveTwoBytes(0x50)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_Abendlicht":
    #print ReceiveTwoBytes(0x51)
    print("Error Position not avalible")
  
  elif str(sys.argv[2]) == "CMD_Read_Luefter":
    print( ReceiveTwoBytes(0x52))
  
  elif str(sys.argv[2]) == "CMD_Read_Summer":
    #print ReceiveTwoBytes(0x53)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_Pos":
    #print ReceiveTwoBytes(0x60)
    print("Error Position not avalible")
  
  elif str(sys.argv[2]) == "CMD_Read_Pos1":
    #print ReceiveTwoBytes(0x61)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_Pos2":
    #print ReceiveTwoBytes(0x62)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_Pos3":
    #print ReceiveTwoBytes(0x63)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_Pos4":
    #print ReceiveTwoBytes(0x64)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_Pos5":
    #print ReceiveTwoBytes(0x65)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_PosMax":
    #print ReceiveTwoBytes(0x66)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_LuefterZeit":
    #print ReceiveTwoBytes(0x67)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_Version":
    #print ReceiveTwoBytes(0x70)
    print("Error Position not avalible")

  else:
    print("ERROR: unknown command")

