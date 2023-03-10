#!/usr/bin/python

import sys
import smbus

def writeToFile(Text):
  with open('readme.txt', 'a') as f:
    f.write(Text)
    f.write('\n')
    f.close()

if len(sys.argv) > 2:

  print(sys.argv[2])

  if str(sys.argv[2]) == "CMD_Rolladen_Hoch":
    writeToFile("Rolladen hoch")

  elif str(sys.argv[2]) == "CMD_Rolladen_Pos1":
    #  SendSingleByte(0x01)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Rolladen_Pos2":
    writeToFile("Rolladen Pos2")

  elif str(sys.argv[2]) == "CMD_Rolladen_Pos3":
    #SendSingleByte(0x03)
    print("Error Position not avalible")
  
  elif str(sys.argv[2]) == "CMD_Rolladen_Pos4":
    writeToFile("Rolladen Pos 4")

  elif str(sys.argv[2]) == "CMD_Rolladen_Pos5":
    #SendSingleByte(0x05)
    print("Error Position not avalible")
  
  elif str(sys.argv[2]) == "CMD_Rolladen_Runter":
    writeToFile("Rolladen Runter")

  elif str(sys.argv[2]) == "CMD_Rolladen_PosX":
    if len(sys.argv) > 3:
      writeToFile("Rolladen Pos X")

  elif str(sys.argv[2]) == "CMD_Rolladen_Stop":
    writeToFile("Rolladen STOP!")

  elif str(sys.argv[2]) == "CMD_Auto_Pos":
    writeToFile("Auto")

  elif str(sys.argv[2]) == "CMD_Auto":
    if len(sys.argv) > 3:
      writeToFile("anderes Auto")

  elif str(sys.argv[2]) == "CMD_Abendlicht":
    if len(sys.argv) > 3:
      writeToFile("Abendlicht")

  elif str(sys.argv[2]) == "CMD_Luefter":
    if len(sys.argv) > 3:
      writeToFile("Luefter auf ".int(sys.argv[3],16))

  elif str(sys.argv[2]) == "CMD_Summer":
    if len(sys.argv) > 3:
      writeToFile("SummSummSum, ...")

  elif str(sys.argv[2]) == "CMD_Set_Pos1":
    writeToFile("tbd")
  
  elif str(sys.argv[2]) == "CMD_Set_Pos2":
    writeToFile("tbd")
  
  elif str(sys.argv[2]) == "CMD_Set_Pos3":
    writeToFile("tbd")
  
  elif str(sys.argv[2]) == "CMD_Set_Pos4":
    writeToFile("tbd")
  
  elif str(sys.argv[2]) == "CMD_Set_Pos5":
    writeToFile("tbd")
  
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
    writeToFile("tbd")
  
  elif str(sys.argv[2]) == "CMD_Read_Licht":
    writeToFile("tbd")
  
  elif str(sys.argv[2]) == "CMD_Read_Temperatur":
    writeToFile("tbd")
  
  elif str(sys.argv[2]) == "CMD_Read_Feuchte":
    writeToFile("tbd")

  elif str(sys.argv[2]) == "CMD_Read_Auto":
    #print ReceiveTwoBytes(0x50)
    print("Error Position not avalible")

  elif str(sys.argv[2]) == "CMD_Read_Abendlicht":
    #print ReceiveTwoBytes(0x51)
    print("Error Position not avalible")
  
  elif str(sys.argv[2]) == "CMD_Read_Luefter":
    writeToFile("tbd")
  
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

