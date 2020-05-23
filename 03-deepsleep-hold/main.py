#!/usr/bin/env python

import machine
import math
import network
import os
import time
import utime
import gc
from pytrack import Pytrack
import pycom
from machine import Pin

gc.enable()
py = Pytrack()
pycom.heartbeat(False)
# pycom.heartbeat(True)

p_out = Pin('P20', mode=Pin.OUT)
if not p_out.hold():
    print("not on hold")
    p_out.value(1)
else:
    print("on hold")
    p_out.hold(False)
    p_out.toggle()
p_out.hold(True)
print("performed hold")

if p_out.value():
    pycom.rgbled(0x007f7f)
else:
    pycom.rgbled(0x007f00)
py.setup_sleep(3)
py.go_to_sleep()
