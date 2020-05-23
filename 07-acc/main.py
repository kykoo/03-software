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


wdt.feed()

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
# pycom.heartbeat(False)
pycom.heartbeat(True)


# LISHH12 SETUP
# +/- 2G, 100 Hz
acc = LIS2HH12.LIS2HH12()
acc.set_full_scale(LIS2HH12.FULL_SCALE_2G)
acc.set_odr(LIS2HH12.ODR_100_HZ)
# acc.set_register(LISHH12.CTRL4_REG, 3, 6, 3) # LPF 50 Hz, BW[2:1]=11

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

    if i%100==0:
        wdt.feed()

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


wdt.feed()

from network import Bluetooth
import time
bt = Bluetooth()
bt.start_scan(-1)

print("getting BLE advert")
isDataSent = False
failureCount = 0
while isDataSent == False:
    adv = bt.get_adv()
    if adv and bt.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL) == 'gpy4gcam':
        print('found gpy4gcam')
        try:
            conn = bt.connect(adv.mac)
            services = conn.services()
            print('printing services...')
            for idx, service in enumerate(services):
                time.sleep(0.050)
                chars = service.characteristics()
                print('printing characteristics')
                for idx_,char in enumerate(chars):
                    if (char.properties() & Bluetooth.PROP_READ):
                        print('service = {:x}, char = {:x} value = {}'.format(service.uuid(),char.uuid(), char.read()))
                        if char.uuid() == 0xaa2:
                            print('0xaa2 found')
                            char.write(b'x0f')
                            isDataSent = True
                            time.sleep(0.050)
        except:
            pass
    else:
        print('not found gpy4gcam')
        failureCount += 1
        if failureCount > 5:
            bt.stop_scan()
            bt.start_scan(-1)
            failureCount = 0
        time.sleep(0.50)
    wdt.feed()

#
# GO TO SLEEP
#

# print("set to 1 before sleep")
# p_out.value(1)
# p_out.hold(True)

# time.sleep(1)
# py.setup_sleep(60*6)

try:
    print(a)
    print('print a success')
except:
    print('print a failed')


wdt.feed()
print("go to sleep")
time.sleep(1)
py.setup_sleep(5)
py.go_to_sleep()
