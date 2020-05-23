# boot.py -- run on boot-up

from machine import WDT
wdt = WDT(timeout=30000)
a=1
