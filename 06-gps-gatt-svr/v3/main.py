import shmGPSclock
import shmBLE
import time
import machine
from machine import WDT

# TEST
rtc = machine.RTC()
wdt = WDT(timeout=1000000)  # enable it with a timeout of 2 seconds


count = 0
while (True):
    wdt.feed()
    count += 1
    print("{:4} {:} {:3} {:3} {} {:} {:3} {}".format(
        count,shmGPSclock.my_gps.parsed_sentences,
        shmGPSclock.my_gps.fix_type,
        shmGPSclock.my_gps.satellites_in_use,
        shmGPSclock.my_gps.date,
        shmGPSclock.my_gps.timestamp,
        shmGPSclock.my_gps.hdop,
        shmGPSclock.gc.mem_free()))
    if shmGPSclock.my_gps.fix_type > 1:
        if False:
            Tnow = rtc.now()
            shmBLE.chr1_update(Tnow)
        else:
            try:
                Tnow = rtc.now()
                shmBLE.chr1_update(Tnow)
            except:
                pass

    time.sleep(1)
    if count%10==0:
        shmGPSclock.gc.collect()
