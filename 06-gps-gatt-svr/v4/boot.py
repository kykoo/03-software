from machine import UART
import machine
from pytrack import Pytrack
import utime
import pycom



start = utime.ticks_us()
uart = UART(0, baudrate=115200)
os.dupterm(uart)

machine.main('main.py')

end = utime.ticks_us()
took = end - start
print("boot.py ... done in: {} uSec".format(took))

# wlan = WLAN(mode=WLAN.AP)
# original_ssid = wlan.ssid()
# original_auth = wlan.auth()
# wlan.mode(WLAN.AP)
# wlan.init(mode=WLAN.AP, ssid='wipy-wlan', auth=(WLAN.WPA2,'www.wipy.io'), channel=7, antenna=WLAN.INT_ANT)
