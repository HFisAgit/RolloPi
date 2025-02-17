# Abhänigkeiten

import json
import time
import subprocess
import os
import os.path
import drivers.ads1115 as ads1115
import drivers.Rolladoino as Rolladoino

from datetime import datetime, timedelta
from time import mktime
from dateutil import tz
from gpiozero import LED, Button

def klingeln():
     led0.on()
     time.sleep(0.2)
     led0.off()

def telefon():
     led0.on()
     time.sleep(0.4)
     led0.off()

def readTempSensor(sensorName) :
    f = open(sensorName, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
 
def readTempLines(sensorName) :
    lines = readTempSensor(sensorName)
    # Solange nicht die Daten gelesen werden konnten, bin ich hier in einer Endlosschleife
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = readTempSensor(sensorName)
    temperaturStr = lines[1].find('t=')
    # Ich überprüfe ob die Temperatur gefunden wurde.
    if temperaturStr != -1 :
        tempData = lines[1][temperaturStr+2:]
        tempCelsius = float(tempData) / 1000.0
        return tempCelsius
 

# initialisire Program
path_log = './automatisierung.log'

#GPIO LED = output
led0 = LED(13)
led1 = LED(19)
led2 = LED(16)
led3 = LED(26)
led4 = LED(20)
led5 = LED(21)
led6 = LED(14)
led7 = LED(15)

# Button = Input
button0 = Button(17)
button1 = Button(18)
button2 = Button(27)
button3 = Button(22)
button4 = Button(23)
button5 = Button(24)
button6 = Button(25)
button7 = Button(4)

telefon0 = Button(5)
klingel0 = Button(6)

# Tempsensor via onewire
# Systempfad zum den Sensor, weitere Systempfade könnten über ein Array
# oder weiteren Variablen hier hinzugefügt werden.
# 28-0000039a30a1 müsst ihr durch die eures Sensors ersetzen!
sensor1 = '/sys/bus/w1/devices/28-0000039a30a1/w1_slave'
sensor2 = '/sys/bus/w1/devices/28-0000039a478d/w1_slave'
 

#outputs
telefon0.when_pressed = telefon
klingel0.when_pressed = klingeln
led0.source = button0
led1.source = button1
led2.source = button2
led3.source = button3
led4.source = button4
led5.source = button5
led6.source = button6
led7.source = button7
                            

     
#starte schleife
while True:
    # hole aktuelle Zeit
    startzeit = datetime.now() # local time

    #######################################################################################

    # Hardware Tests:
    # INPUTS
    #Taster / Schalter
    buttonVals = {
         "in1": button0.is_pressed,
         "in2": button1.is_pressed,
         "in3": button2.is_pressed,
         "in4": button3.is_pressed,
         "in5": button4.is_pressed,
         "in6": button5.is_pressed,
         "in7": button6.is_pressed,
         "in8": button7.is_pressed
         }
    with open('buttonValues.json', 'w') as f:
            json.dump(buttonVals, f)

    # ADC
    adc1 = ads1115.readSingle(0)
    adc2 = ads1115.readSingle(1)
    adc3 = ads1115.readSingle(2)
    adc4 = ads1115.readSingle(3)

    analogVals = {
            "adc1": str(adc1),
            "adc2": str(adc2),
            "adc3": str(adc3),
            "adc4": str(adc4)
        }
    with open('analogValues.json', 'w') as f:
            json.dump(analogVals, f)

    
    # Temperatur auslesen
    if (os.path.isfile(sensor1) & os.path.isfile(sensor2)):
        tempSensVal = {
            "time": time.strftime('%H:%M:%S'),
            "temp1": str(readTempLines(sensor1)),
            "temp2": str(readTempLines(sensor2))
        }
        with open('temperaturValues.json', 'w') as f:
            json.dump(tempSensVal, f)
    


    #########################################################################################
    # hole neuen Zeitstempel
    endzeit = datetime.now()

    # berechne wartezeit bis zum nächsten schleifendurchlauf
    sleeptime = startzeit + delta_time - endzeit

    # sleep
    if (sleeptime.total_seconds() > 0):
        time.sleep(sleeptime.total_seconds())
    else:
        print("Warning: loop takes longer then time_delta!")
        print(sleeptime.total_seconds())
        with open(path_log, 'a') as f:
            f.write(str(startzeit) + "Warning: loop takes longer then time_delta!" + '\n')
        time.sleep(1)
# ende Schleife

print('end of program')
