import time
from network import WLAN
wlan=WLAN()
wlan.deinit()
wlan=WLAN(mode=WLAN.AP,ssid='gpy-wifi',antenna=WLAN.INT_ANT,hidden=False,auth=(WLAN.WPA2,'1234567890'))


while True:
    time.sleep(1)
    print('{}, {}, {}'.format(time.time(),wlan.mode(),wlan.isconnected()))
