import math
import time
from L76micropyGPS import L76micropyGPS
from micropyGPS import MicropyGPS
from pytrack import Pytrack
import gc
import pycom
import machine
import _thread
import logging
from machine import Pin


# gpsState
# 0 : no fixed yet
# 1 : Fixed
# 2 : Sleep
gpsState = 0

logger = logging.getLogger(__name__)


# enable GC
# gc.enable()

# logger.debug("Free Mem: {}".format(gc.mem_free()))

# Start GPS, you need this line
py = Pytrack()
# logger.debug("Free Mem post pytrack instantiation: {}".format(gc.mem_free()))

# Start a microGPS object, you need this line
my_gps = MicropyGPS(location_formatting='dd')
# logger.debug("Free Mem post my_gps instantiation: {}".format(gc.mem_free()))
L76micropyGPS = L76micropyGPS(my_gps, py)
# gpsThread = L76micropyGPS.startGPSThread()
# print("startGPSThread thread id is: {}".format(gpsThread))

rtc = machine.RTC()

# p = Pin('P3',mode=Pin.OUT)
# p.value()

def showTime():
    now = ((my_gps.date[2]+2000,       # yr
            my_gps.date[1],            # Month
            my_gps.date[0],            # day
            my_gps.timestamp[0],       # Hr
            my_gps.timestamp[1],       # Min
            int(my_gps.timestamp[2]))) # Sec
    logger.debug(now)


def update_RTC_from_GPS():
    # GPS Parsing
    L76micropyGPS.gpsParsing_until_gpsFix()
    logger.debug('GPS time fixed. Updating RTC...')
    # RTC Updating
    now = ((my_gps.date[2]+2000,       # yr
            my_gps.date[1],            # Month
            my_gps.date[0],            # day
            my_gps.timestamp[0],       # Hr
            my_gps.timestamp[1],       # Min
            int(my_gps.timestamp[2]) + 1)) # Sec
    # while L76micropyGPS.my_gps.time_since_fix() < 1000:
    #     time.sleep_ms(1)
    rtc.init(now)
    logger.debug('GPSclock = '+str(now))
    return
