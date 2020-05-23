from network import WLAN
from machine import Pin
import time


wlan = WLAN(mode=WLAN.STA)
wlan.antenna(WLAN.EXT_ANT)
Pin('P12', mode=Pin.OUT)(True)

c = 0
while True:
    print('{} {}'.format(c,wlan.isconnected()))
    print(wlan.scan())
    time.sleep(1)
    c += 1
