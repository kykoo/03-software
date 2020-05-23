import math
import time
import utime
from L76micropyGPS import L76micropyGPS
from micropyGPS import MicropyGPS
from pytrack import Pytrack
import gc
import pycom
import machine
import _thread


# RTC Initialisation
rtc = machine.RTC()
print("Free Mem post rtc instantiation: {}".format(gc.mem_free()))
start = utime.ticks_ms()
print("RTC time : {}".format(rtc.now()))


# Thread function to update RTC
def updateRTC():
    while True:
        if my_gps.fix_type < 2:
            # print(' [GPSclock] GPS time not fixed yet')
            pass
        else:
            now = ((my_gps.date[2]+2000,       # yr
                    my_gps.date[1],            # Month
                    my_gps.date[0],            # day
                    my_gps.timestamp[0],       # Hr
                    my_gps.timestamp[1],       # Min
                    int(my_gps.timestamp[2]))) # Sec
            print(' [GPSclock] GPS time fixed. Updating RTC...')
            print(' [GPSclock] ',end='')
            print(now)
            rtc.init(now)
            print(rtc.now())
            time.sleep(60)
        time.sleep(1)


# enable GC
gc.enable()
print("Free Mem: {}".format(gc.mem_free()))

# Start GPS, you need this line
py = Pytrack()
print("Free Mem post pytrack instantiation: {}".format(gc.mem_free()))

# Start a microGPS object, you need this line
my_gps = MicropyGPS(location_formatting='dd')
print("Free Mem post my_gps instantiation: {}".format(gc.mem_free()))
L76micropyGPS = L76micropyGPS(my_gps, py)
gpsThread = L76micropyGPS.startGPSThread()
# print("startGPSThread thread id is: {}".format(gpsThread))

# Thread to Update RTC
_thread.start_new_thread(updateRTC,())
