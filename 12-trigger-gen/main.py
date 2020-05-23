from machine import Pin
import time
import pycom


pycom.heartbeat(False)
pinTrig = Pin('P7', mode=Pin.OUT)

# while True:
#     print('1')
#     pycom.rgbled(0x000F00)
#     pinTrig.value(1)
#     time.sleep_ms(3000)
#     print('0')
#     pycom.rgbled(0x000000)
#     pinTrig.value(0)
#     time.sleep_ms(3000)

def go():
    print('1')
    pycom.rgbled(0x000F00)
    pinTrig.value(1)
    time.sleep_ms(300)
    print('0')
    pycom.rgbled(0x000000)
    pinTrig.value(0)
