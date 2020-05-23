# boot.py -- run on boot-up

from machine import WDT
wdt = WDT(timeout=60000)
a=1
