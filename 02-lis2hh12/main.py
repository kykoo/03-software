#!/usr/bin/env python
#
# Copyright (c) 2019, Pycom Limited.
#
# This software is licensed under the GNU GPL version 3 or any
# later version, with permitted additional terms. For more information
# see the Pycom Licence v1.0 document supplied with this file, or
# available at https://www.pycom.io/opensource/licensing
#

import machine
import math
import network
import os
import time
import utime
import gc
# from machine import RTC
from machine import SD
# from L76GNSS import L76GNSS
from pytrack import Pytrack
import pycom

# from LIS2HH12 import LIS2HH12
# from LIS2HH12 import FULL_SCALE_2G
# from LIS2HH12 import ODR_10_HZ

import LIS2HH12
import array

from machine import Pin


def avg(U):
    Usum = 0.0
    count = 0
    for u in U:
        Usum += u
        count += 1
    Uavg = Usum/count
    return Uavg

def rms(U):
    Ussum = 0.0
    count  = 0
    Uavg = avg(U)
    for u in U:
        Ussum += (u-Uavg)**2.0
        count += 1
    Urms = (Ussum/count)**0.5
    return Urms


gc.enable()

py = Pytrack()
pycom.heartbeat(False)
# pycom.heartbeat(True)

#
# GPIO OUTPUT
#

p_out = Pin('P20', mode=Pin.OUT)
if not p_out.hold():
    print("not on hold")
    p_out.value(1)
else:
    print("on hold")
    p_out.hold(False)
    p_out.toggle()
p_out.hold(True)
print("performing hold")

if p_out.value():
    pycom.rgbled(0x007f7f)
else:
    pycom.rgbled(0x007f00)

# # setup rtc
# rtc = machine.RTC()
# rtc.ntp_sync("pool.ntp.org")
# utime.sleep_ms(750)
# print('\nRTC Set from NTP to UTC:', rtc.now())
# utime.timezone(7200)
# print('Adjusted from UTC to EST timezone', utime.localtime(), '\n')


# LISHH12 SETUP
# +/- 2G, 100 Hz
acc = LIS2HH12.LIS2HH12()
acc.set_full_scale(LIS2HH12.FULL_SCALE_2G)
acc.set_odr(LIS2HH12.ODR_100_HZ)
# acc.set_register(LISHH12.CTRL4_REG, 3, 6, 3) # LPF 50 Hz, BW[2:1]=11


# l76 = L76GNSS(py, timeout=30)

sd = SD()
os.mount(sd, '/sd')
f = open('/sd/acc-rms.txt', 'a')

#
# MEASURE ACCELERATION
#

X = array.array('f')
Y = array.array('f')
Z = array.array('f')

for i in range(100*3):
    # coord = l76.coordinates()
    #f.write("{} - {}\n".format(coord, rtc.now()))
    # print("{} - {} - {}".format(coord, rtc.now(), gc.mem_free()))
    while not acc.new_data_available():
        time.sleep_us(10)
    acc_ = acc.acceleration()
    print("{:8.5f}, {:8.5f}, {:8.5f}".format(acc_[0], acc_[1], acc_[2]))
    X.append(acc_[0])
    Y.append(acc_[1])
    Z.append(acc_[2])

Xrms = rms(X)
Yrms = rms(Y)
Zrms = rms(Z)
print('Xavg={}'.format(avg(X)))
print('Yavg={}'.format(avg(Y)))
print('Zavg={}'.format(avg(Z)))
print('Xrms={}'.format(Xrms))
print('Yrms={}'.format(Yrms))
print('Zrms={}'.format(Zrms))

#
# SD MEMORY: SAVE RMS
#

f.write('{:8.5f}, {:8.5f}, {:8.5f}\n'.format(Xrms,Yrms,Zrms))
f.close()


# while True:
#     print("1")
#     p_out.value(1)
#     time.sleep(1)
#     print("0")
#     p_out.value(0)
#     time.sleep(1)


#
# GO TO SLEEP
#

# print("set to 1 before sleep")
# p_out.value(1)
# p_out.hold(True)

# print("go to sleep")
# time.sleep(1)
# py.setup_sleep(60*6)
py.setup_sleep(3)
py.go_to_sleep()
