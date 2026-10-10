#!/usr/bin/env python

# run with python3 -m drivers.Rolladoino ...
import sys
import time
import smbus
import argparse
import os
from . import TCA9548A


def log(message):
    print(f"[Rolladoino] {message}", flush=True)


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
        log(f"Multiplexer-Kanal {subbus} für Etage {floor} auswählen")
       # bus.write_byte(I2C_address,subbus)
        TCA9548A.I2C_setup(I2C_address,subbus) # reaktivate when seperate buses
        time.sleep(0.1)
        log(f"Multiplexer-Kanal {subbus} ausgewählt")

    return

def SendSingleByte(bus, address, SendByte):

  log(f"I2C write_byte: Adresse={hex(address)}, Wert={hex(SendByte)}")
  bus.write_byte(address, SendByte)

  log(f"I2C write_byte erfolgreich; Antwort von {hex(address)} lesen")
  ret = bus.read_byte(address)
  log(f"I2C-Leseantwort von {hex(address)}: {hex(ret)}")

  return ret


def SendTwoBytes(bus, address, Command, Argument):
  
  log(f"I2C write_byte_data: Adresse={hex(address)}, Befehl={hex(Command)}, Argument={hex(Argument)}")
  bus.write_byte_data(address, Command, Argument) 

  log(f"I2C write_byte_data erfolgreich; Antwort von {hex(address)} lesen")
  ret = bus.read_byte(address)
  log(f"I2C-Leseantwort von {hex(address)}: {hex(ret)}")

  return ret

def main(cmd, floor, addr, param=0):
    if isinstance(addr, str):
        addr = int(addr, 0)
    if not isinstance(addr, int) or isinstance(addr, bool) or not 0 <= addr <= 0x7f:
        raise ValueError(f"Ungültige I2C-Adresse: {addr!r}")

    log(f"Öffne SMBus 1; Befehl={cmd}, Etage={floor}, Adresse={hex(addr)}, Parameter={param}")
    bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    log("SMBus 1 geöffnet")

    if(cmd=="CMD_Rolladen_Hoch"):
        log("Führe CMD_Rolladen_Hoch aus")
        setFloor(bus, floor)
        SendSingleByte(bus, addr, 0x00)
        log("CMD_Rolladen_Hoch abgeschlossen")
        return None

    elif(cmd=="CMD_Rolladen_Runter"):
        log("Führe CMD_Rolladen_Runter aus")
        setFloor(bus, floor)
        SendSingleByte(bus, addr, 0x06)
        log("CMD_Rolladen_Runter abgeschlossen")
        return None

    elif(cmd=="CMD_Rolladen_Stop"):
        log("Führe CMD_Rolladen_Stop aus")
        setFloor(bus, floor)
        SendSingleByte(bus, addr, 0x08)
        log("CMD_Rolladen_Stop abgeschlossen")
        return None

    elif(cmd=="CMD_Luefter"):
        log("Führe CMD_Luefter aus")
        setFloor(bus, floor)
        SendTwoBytes(bus, addr, 0x12, param)
        log("CMD_Luefter abgeschlossen")
        return None

    elif(cmd=="CMD_Read_Pos"):
        log("Führe CMD_Read_Pos aus")
        setFloor(bus, floor)
        pos = SendSingleByte(bus, addr, 0x60)
        log(f"CMD_Read_Pos abgeschlossen: Position={pos}")
        return pos

    elif(cmd=="CMD_Summer"):
        log("Führe CMD_Summer aus")
        setFloor(bus, floor)
        SendTwoBytes(bus, addr, 0x13, param)
        log("CMD_Summer abgeschlossen")
        return None

    else:
        log(f"ERROR: Unbekannter Befehl: {cmd}")
        return None

if __name__ == "__main__":
    log(f"Prozess gestartet: executable={sys.executable}, cwd={os.getcwd()}, euid={os.geteuid()}, argv={sys.argv!r}")
    parser = argparse.ArgumentParser()
    parser.add_argument("floor", help="Das stockwerk auf dem sich das Device befindet", choices=['EGN', 'EGS', 'OGN', 'OGS'])
    parser.add_argument("address", help="Die Adresse des I2C device", type=lambda x: int(x,16))
    parser.add_argument("command", help="Der Befehl, der ausgefuehrt werden soll. [CMD_Rolladen_Hoch ; CMD_Rolladen_Runter ; CMD_Rolladen_Stop ; CMD_Luefter ; CMD_Read_Pos ; CMD_Summer ]")
    parser.add_argument("--stufe", help="Die Stufe auf die der Luefter gesetzt werden soll", type=int, choices=[0,1,2,3])
    parser.add_argument("--summer", help="Summer an (2) oder aus (0)", type=int, choices=[0,1,2])
    args = parser.parse_args()
    
    log("Öffne SMBus 1 für CLI-Start")
    bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    log("SMBus 1 für CLI-Start geöffnet")
    
    # Wähle den richtigen Parameter basierend auf dem Befehl
    if args.command == "CMD_Summer":
        param = args.summer if args.summer is not None else 0
    elif args.command == "CMD_Luefter":
        param = args.stufe if args.stufe is not None else 0
    else:
        param = args.stufe if args.stufe is not None else 0
    
    log(f"Argumente geparst: floor={args.floor}, address={hex(args.address)}, command={args.command}, parameter={param}")
    main(args.command, args.floor, args.address, param)
    #print(args.command)args.floor, args.address, args.stufe) # !! What if stufe is empty???
    log(f"CLI-Befehl {args.command} beendet")
