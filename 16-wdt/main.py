from machine import WDT
import time


wdt = WDT(timeout=5000)  # enable it with a timeout of 2 seconds
wdt.feed()

c = 0
while True:
    print(c)
    time.sleep(1)
    c += 1
