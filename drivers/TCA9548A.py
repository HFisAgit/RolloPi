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
    if not isinstance(i2c_channel_setup, int) or not 0 <= i2c_channel_setup < len(channel_array):
        raise ValueError(f"Ungültiger TCA9548A-Kanal: {i2c_channel_setup!r}")

    print("[TCA9548A] Öffne SMBus 1", flush=True)
    bus = smbus.SMBus(1)

    print(f"[TCA9548A] Wähle Kanal {i2c_channel_setup} (Maske {hex(channel_array[i2c_channel_setup])}) "
          f"am Multiplexer {hex(multiplexer)}", flush=True)
    try:
        bus.write_byte(multiplexer, channel_array[i2c_channel_setup])
        print(f"[TCA9548A] Kanal {i2c_channel_setup} erfolgreich ausgewählt", flush=True)
    except OSError as err:
        print(f"[TCA9548A] I2C-Schreibfehler an {hex(multiplexer)} beim Wählen von Kanal "
              f"{i2c_channel_setup}: {err!r}", flush=True)
        try:
            status = bus.read_byte(multiplexer)
            print(f"[TCA9548A] Multiplexer-Status nach Fehler: {bin(status)}", flush=True)
        except OSError as status_error:
            print(f"[TCA9548A] Statusabfrage ebenfalls fehlgeschlagen: {status_error!r}", flush=True)
        raise

    time.sleep(0.01)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Verwendung: python3 TCA9548A.py <multiplexer_addr> <i2c_channel>")
        print("Beispiel: python3 TCA9548A.py 0x70 0")
        sys.exit(1)
    
    multiplexer_addr = int(sys.argv[1], 0)  # 0x70 oder 112
    i2c_channel = int(sys.argv[2])
    
    I2C_setup(multiplexer_addr, i2c_channel)
    print(f"I2C-Kanal {i2c_channel} aktiviert (Multiplexer: {hex(multiplexer_addr)})")