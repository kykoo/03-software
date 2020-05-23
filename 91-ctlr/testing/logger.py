#!/usr/bin/python3
import argparse
import serial
import time
import sys
import datetime
import os

parser = argparse.ArgumentParser(description='log serial outputs')
parser.add_argument('serialPortNumber', help='serial port number /dev/ttyACM{i}')
args = parser.parse_args()

serialPort = '/dev/ttyACM{}'.format(args.serialPortNumber)


filename = 'ttyACM{}-{}.log'.format(args.serialPortNumber, datetime.datetime.now().strftime('%Y%m%d-%H%M00'))

with open(filename,'a') as fp:
    while True:
        # Check port exist
        print('****checking if {} exists.'.format(serialPort),end='')
        while True:
            if os.path.exists(serialPort):
                break
            print('.', end='')
            time.sleep(1)
        print('')
        # Opening port
        print('****opening serial port',end='')
        while True:
            try:
                ser =  serial.Serial(serialPort, 115200, timeout=1) 
                print('')
                break
            except serial.SerialException as exc:
                if exc.errno==2:
                    print('.',end='')
                    time.sleep(1)
        # Read and Write
        try:
            while True:
                line = ser.readline()   # read a '\n' terminated line
                line_asc=line.decode('ASCII')
                print(line_asc,end='')
                fp.write(line_asc)
                fp.flush()
        except serial.SerialException as exc:
            ser.close()
            print('serial error detected. closing')
        except KeyboardInterrupt:
            ser.close()
            fp.close()
            break

