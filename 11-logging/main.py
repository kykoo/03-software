from machine import SD
import os
import logging
import time
import pycom


sd = SD()
os.mount(sd,'/sd')
a=os.listdir('/sd')
print(a)


count = 0
while True:
    print('count={}'.format(count))
    count += 1
    time.sleep(1)
    if count > 0:
        break


nday = pycom.nvs_get('day')
nhr = pycom.nvs_get('hr')

logging.basicConfig(level=logging.INFO,filename='/sd/log%04d.txt' % nday)
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("__main__")
logger.debug("Test message: %d(%s)", 100, "foobar")
logger.info("Test message2: %d(%s)", 100, "foobar")
logger.warning("Test message3: %d(%s)", 100, 'test')
logger.error("Test message4")
logger.critical("Test message5")
logging.info("Test message6")

try:
    1/0
except:
    logger.exception("Some trouble (%s)", "expected")

if nhr < 23:
    nhr += 1
    pycom.nvs_set('hr',nhr)
else:
    nday +=1
    nhr = 0
    pycom.nvs_set('day',nday)
    pycom.nvs_set('hr',nhr)
