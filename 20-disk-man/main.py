import os
from machine import SD, RTC
import logging
import time
import sys
import diskutil

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

rtc = RTC()
rtc.ntp_sync('pool.ntp.org')
while not rtc.synced():
    logger.info('not synced yet...')
    time.sleep(1)
logger.info('synced done.')

targetDir = '/sd'
targetSpace = 1024*1024 # 1 GiB

sd = SD()
logger.info('mounting SD...')
os.mount(sd,'/sd')
logger.info('mounting success')


def date_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}-{:0>2d}{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2],t_[3],t_[4],t_[5])



# sys.exit('')

logger.info('free-space ={}'.format(os.getfree('/sd')))
while True:
    logger.info('creating a file ...')
    diskutil.create_file('/sd/acc{}'.format(date_string(time.time())),1)
    logger.info('creating a file Done.')
    free_space = os.getfree('/sd')
    logger.info('free-space ={}'.format(free_space))

    diskutil.house_keeping('/sd',15,'acc')
    logger.info('Disk space available after house-keeping: {}'.format(os.getfree(targetDir)))
    time.sleep(1)
