from network import WLAN
from machine import Pin
import time
import machine
from machine import Pin

pin_relay_AP = Pin('P20',mode=Pin.OUT, pull=Pin.PULL_DOWN)
pin_relay_AP.value(1)
c=0
print('AP turned on...')
while True:
    time.sleep(1)
    print('{}/60'.format(c))
    c+=1
    if c>60:
        break

wlan = WLAN(mode=WLAN.STA)
# wlan.antenna(WLAN.EXT_ANT)
# Pin('P12', mode=Pin.OUT)(True)
def connect(nets):
    for net in nets:
        # if net.ssid == 'wings':
        #     print('Network found!')
        #     wlan.connect(net.ssid, auth=(net.sec, '1234567890'), timeout=5000)
        #     while not wlan.isconnected():
        #         machine.idle() # save power while waiting
        #     return
        if net.ssid == 'RUT230_7714':
            print('Network found!')
            wlan.connect(net.ssid, auth=(net.sec, 'Ei09UrDg'), timeout=5000)
            while not wlan.isconnected():
                machine.idle() # save power while waiting
            print('WLAN connection succeeded!')
            break

c = 0
while True:
    print('{} {}'.format(c,wlan.isconnected()))
    nets = wlan.scan()
    print(nets)
    time.sleep(1)
    c += 1

    if c > 2 and not wlan.isconnected():
        connect(nets)
        break

# c = 0
# while True:
#     print('{} {}'.format(c,wlan.isconnected()))
#     nets = wlan.scan()
#     print(nets)
#     time.sleep(1)
#     c += 1
#
#     if c > 2 and not wlan.isconnected():
#         connect(nets)
#         break
