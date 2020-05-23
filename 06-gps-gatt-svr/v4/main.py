import shmGPSclock
import shmBLE
import time
import machine
from machine import WDT


# TEST
rtc = machine.RTC()

# | gps  | i2c, my_gps | get nmea via i2c, nmea parsing, updating my_gps variables | 0.25 sleep
# | ble  | my_gps, i2c | chr1 update via i2c                                       |
# | rtc  | i2c         | updating rtc via i2c  every 1 mins                        |
# | trig | newData     | check the RMS value and trigger rpi                       | on new value
#
# | ble callback | newData | basically threaded. | chr1_lock
#
# Loop levels
#
# - most frequent: gps parsing 4 Hz
# - next frequent: ble-chr1 update 1 Hz
# - next frequent: rtc update 60 sec
# - next frequent: trigger on_new_value




wdt = WDT(timeout=1000000)  # enable it with a timeout of 2 seconds

from network import WLAN
wlan = WLAN(mode=WLAN.AP, ssid='gpy-wifi', auth=(WLAN.WPA2,'1234567890'), channel=6, antenna=WLAN.INT_ANT)


# Thread function to update RTC
def updateRTC():
    now = ((shmGPSclock.my_gps.date[2]+2000,       # yr
            shmGPSclock.my_gps.date[1],            # Month
            shmGPSclock.my_gps.date[0],            # day
            shmGPSclock.my_gps.timestamp[0],       # Hr
            shmGPSclock.my_gps.timestamp[1],       # Min
            int(shmGPSclock.my_gps.timestamp[2]))) # Sec
    print(' [GPSclock] GPS time fixed. Updating RTC...')
    print(' [GPSclock] ',end='')
    print(now)
    rtc.init(now)
    print(rtc.now())

# THE MAIN LOOP
count = 0
while (True):
    wdt.feed()
    count += 1

    # GPS Parsing
    shmGPSclock.L76micropyGPS.gpsParsing()

    # SHOW INFO FROM GPS
    print("{:4} {:} {:3} {:3} {} {:} {:3} {}".format(
        count,shmGPSclock.my_gps.parsed_sentences,
        shmGPSclock.my_gps.fix_type,
        shmGPSclock.my_gps.satellites_in_use,
        shmGPSclock.my_gps.date,
        shmGPSclock.my_gps.timestamp,
        shmGPSclock.my_gps.hdop,
        shmGPSclock.gc.mem_free()))

    if shmGPSclock.my_gps.fix_type > 1 and count%4 ==0:
        # RTC Updating
        updateRTC()
        Tnow = rtc.now()
        # BLE Char Updating
        shmBLE.chr1_update(Tnow)

    if count%10==0:
        shmGPSclock.gc.collect()
        shmBLE.gc.collect()

    time.sleep(0.25)
