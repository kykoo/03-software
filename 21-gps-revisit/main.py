#
# GPS fixes the time first, then solves for the 3D position
#
import math
import time
import utime
from L76micropyGPS import L76micropyGPS
from micropyGPS import MicropyGPS
from pytrack import Pytrack
import gc

def attach_crc(cmd_str):
    a = cmd_str[1:]
    crc = 0
    for ch in a:
        crc ^= ord(ch)
    return cmd_str + '*' + '{:X}'.format(crc) +'\r\n'

py = Pytrack()
GPS_I2CADDR = const(0x10)
print('starting to configure GPS...')
if 1:
    py.i2c.writeto(GPS_I2CADDR, "$PMTK185,1*23\r\n")
    py.i2c.writeto(GPS_I2CADDR, bytes([0]))
if 0:
    print('sending rmc only cmd...')
    rmc = "$PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29\r\n"
    py.i2c.writeto(GPS_I2CADDR, rmc)
    py.i2c.writeto(GPS_I2CADDR, bytes([0]))
if 1:
    print('GGA and RMC only...')
    cmd = attach_crc("$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
    py.i2c.writeto(GPS_I2CADDR, cmd)
    py.i2c.writeto(GPS_I2CADDR, bytes([0]))

if 0:
    # searchmode = "$PMTK353,1,0,0,0,0*2B\r\n"
    # searchmode = "$PMTK353,1,1,1,0,0*2B\r\n"
    searchmode = attach_crc('$PMTK353,1,1,0,1,0')
    py.i2c.writeto(GPS_I2CADDR, searchmode)
    py.i2c.writeto(GPS_I2CADDR, bytes([0]))

# gps+glonass        : stats=5 sometimes 4, fix=2,
# gps+glonass+GALILEO: state=4,             fix=2
# gps+beiDou         : the same
# gps+galileo        : the same
# gps+galileo-f      : the same
# gps+glonass+galileo/f :
buff = ''
while True:
    nmea_ = py.i2c.readfrom(GPS_I2CADDR, 255)
    buff += nmea_.decode('ASCII')
    nmeas = buff.split('\r\n')
    for idx, nmea in enumerate(nmeas):
        if idx < len(nmeas)-1:
            if 1:
                print(nmea.replace('\n',''))
            else:
                nmea_c = nmea.replace('\n','')
                nmea_segs = nmea_c.split(',')
                key = 'GGA'
                if key in nmea_segs[0] or 'PMTK' in nmea_segs[0] or 'RMC' in nmea_segs[0]:
                    print(nmea_c)
        else:
            buff = nmea

buff = b''
while True:
    someNmeaData = py.i2c.readfrom(GPS_I2CADDR, 512)
    buff += someNmeaData
    NMEAS = buff.decode('ASCII').replace('\n\n','').split('\r\n')
    for idx, nmea in enumerate(NMEAS):
        if idx < len(NMEAS)-1:
            nmea = nmea.replace('\n','').replace('\r','')
            segments = nmea.split(',')
            # if 'RMC' in segments[0] or 'GLL' in segments[0] or 'GGA' in segments[0] or 'GSA' in segments[0]:
                # print(nmea)
            if 0: 
                key = 'GGA'
                if key in segments[0]:
                    print(nmea)
            else:
                print(nmea)

        else:
            buff = nmea.encode()
    time.sleep(0.1)

#
# You will need the following lines
# The print statements can be removed - they are just here to debug
#

# enable GC
# gc.enable()
#
# print("Free Mem: {}".format(gc.mem_free()))
#
# # Start GPS, you need this line
# py = Pytrack()
#
# print("Free Mem post pytrack instantiation: {}".format(gc.mem_free()))
#
# # Start a microGPS object, you need this line
# my_gps = MicropyGPS(location_formatting='dd')
#
# print("Free Mem post my_gps instantiation: {}".format(gc.mem_free()))
#
# # Start the L76micropyGPS object, you need this line
# L76micropyGPS = L76micropyGPS(my_gps, py)
#
# # Start the thread, you need this line
# gpsThread = L76micropyGPS.startGPSThread()
#
# print("startGPSThread thread id is: {}".format(gpsThread))
#
# #
# # Do what you like now, examples below
# # at some point you should want to read GPS/GNS data
# # you need none of these lines, but I would assume
# # at least one line doing something with my_gps object ...
# #
#
# #start rtc
# rtc = machine.RTC()
# print("Free Mem post rtc instantiation: {}".format(gc.mem_free()))
# start = utime.ticks_ms()
# print("RTC time : {}".format(rtc.now()))
# print('Aquiring GPS signal ', end='')
# #try to get gps date to config rtc
#
# #
# # Just and example while thread to spit out
# # GPS/GNS data to the console/uart
# #
# while (True):
#     print("my_gps.parsed_sentences: {}".format(my_gps.parsed_sentences))
#     print("my_gps.satellites_in_use: {}".format(my_gps.satellites_in_use))
#     print("my_gps.date: {}".format(my_gps.date))
#     print("my_gps.timestamp: {}".format(my_gps.timestamp))
#     timestamp = my_gps.timestamp
#     dt = my_gps.time_since_fix()/1000
#     timestamp_ = (timestamp[0],timestamp[1],timestamp[2]+dt)
#     print("my_gps.timestamp: {}".format(timestamp_))
#     print("my_gps.hdop: {}".format(my_gps.hdop))
#     print("my_gps.fix_type: {}".format(my_gps.fix_type))
#     print("Free Mem: {}".format(gc.mem_free()))
#     time.sleep(1)

# switch off heartbeat LED
#pycom.heartbeat(False)
#print('Going to kipp 2 secs in 1 sec')
#time.sleep(1)
#py.setup_sleep(2)
#py.go_to_sleep(gps=True)
