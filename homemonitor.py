# This script monitors Protovac's HOME key to kick the user
# back to the home screen
#
# Runs as root

import os
import serial

ser = serial.Serial('/dev/ttyAMA1', baudrate=9600)


try:
    while True:
        if ser.read() == b'\x01' and ser.read() == b'N' and ser.read() == b'\r':
            print('Home key pressed, killing login process...')
            os.system('killall -9 login')
finally:
    print('Closing serial port...')
    ser.close()

