import math
import time
from L76micropyGPS import L76micropyGPS
from micropyGPS import MicropyGPS
from pytrack import Pytrack
import gc
import pycom
import machine
import _thread








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
#gpsThread = L76micropyGPS.startGPSThread()
# print("startGPSThread thread id is: {}".format(gpsThread))
