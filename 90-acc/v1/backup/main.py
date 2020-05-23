import machine
import math
import network
import os
import time
import gc
from machine import SD
import pycom
from machine import Pin
from machine import RTC
import ACC
import logging
from math import floor, ceil
import socket_client
import ustruct
import dropfile
from network import WLAN
import json
import diskutil
import pycom


def datetime_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}-{:0>2d}{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2],t_[3],t_[4],t_[5])

def date_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2])

pybytes.smart_config(False)
#
# STARTING (state=0)
#
state = 0
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Greeting
logger.info('Starting ACC...')
# AP SELECTION!
pbconf = pybytes.get_config()
AP = pbconf['wifi']['ssid']
if AP == 'wings':
    CTLR_IPADDRESS = '192.168.1.51'
elif AP == 'RUT230_7714':
    CTLR_IPADDRESS = '192.168.1.100'
socket_client.CTLR_IPADDRESS = CTLR_IPADDRESS

logger.info('AP={}'.format(AP))
# LOADING SYSTEM VARIABLES
if 0:
    pycom.nvs_set('iCAM',1)
    pycom.nvs_set('iACC',1)
else:
    iCAM = pycom.nvs_get('iCAM')
    iACC = pycom.nvs_get('iACC')
logger.debug('CAM{}-ACC{}'.format(iCAM, iACC))

rtc = RTC()
sd = SD()
os.mount(sd,'/sd')

# CONNECT TO RUT230_7714
wlan = WLAN(mode=WLAN.STA)
if not wlan.isconnected():
    logger.debug('Waiting for AP to be visible...')
    c = 1
    while c:
        logger.debug('scanning trial:{}...'.format(c))
        nets = wlan.scan()
        c += 1
        for net in nets:
            if net.ssid == 'RUT230_7714':
                logger.debug('Network found!')
                c = 0
    logger.debug('Waiting for AP to be visible Done.')
    logger.debug('connecting to Wifi...')
    if 1:
        pybytes.connect_wifi()
    else:
        wlan.ifconfig(config=('192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8'))
        wlan.connect('RUT230_7714', auth=(WLAN.WPA2, 'Ei09UrDg'), timeout=5000)
        while not wlan.isconnected():
            machine.idle() # save power while waiting
    logger.debug('connecting to Wifi done...')

#
# GETTING TIME AND STATE OF CONTROLLER (state=1)
#
state = 1
c = 1
while c:
    requests = 'get,state;get,time;set,state1,{}'.format(state)
    logger.debug('socket_client.request  {}...'.format(requests))
    response = socket_client.request(requests)
    logger.debug('socket_client.request done. Response={}.'.format(response))
    c += 1
    if response:
        response_list = response.split(';')
        state = int(response_list[0])
        time_gps = int(response_list[1])
        rtc.init(time.localtime(time_gps))
        logger.debug('state of controller = {} and time={}'.format(state,rtc.now()))
        if state in [2,4]:
            logger.debug('CTLR state={}; starting node job...'.format(state))
            c = 0
        else:
            logger.debug('CTLR state={}; waiting until CTLR ready...'.format(state))
    else:
        logger.debug('no response from controller')
    time.sleep(1)

if state == 2:
    T_exec = 60
elif state == 4:
    T_exec = 3600
#
# MEASURE (state=2)
#
nsecOfMeasure = 5
# Setup
logger.debug("Setting up ACC ... ")
ACC.setup(wdt)
wdt.feed()
logger.debug("Setting up ACC Done.")
response = socket_client.request('set,state{},2'.format(iACC))
time_current = time.time()
#time_start = (floor(time_current/10)+1)*10
res = time_current%T_exec
if res != 0:
    time_start = time_current - res + T_exec
else:
    time_start = time_current
# Acc Measurement
logger.debug("Time_current = {}, Time_start = {}...".format(\
        time_current,time_start))
logger.debug("Time_current = {}".format(datetime_string(time_current)))
logger.debug("Time_start   = {}...".format(datetime_string(time_start)))

logger.debug("Waiting for {} seconds ...".format(time_start-time_current))
while True:
    if time.time() >= time_start:
        break
# MESURING
logger.debug("Measuring ACC...")
pycom.heartbeat(False)
pycom.rgbled(0x000F00)
X,Y,Z,Xrms,Yrms,Zrms = ACC.measure(Td=nsecOfMeasure)
rmsACC = (Xrms**2+Yrms**2+Zrms**2)**0.5
logger.debug("Measuring ACC Done.")
pycom.rgbled(0x000000)
time.sleep_ms(100)
pycom.heartbeat(True)
# STORING FILE INTO SD CARD
logger.debug("Storing data into SD...")
filename = '/sd/gcam{}-acc{}-'.format(iCAM,iACC) + datetime_string(time_start)
with open(filename,'wb') as file:
    for i in range(len(X)):
        file.write(ustruct.pack('<ddd',X[i],Y[i],Z[i]))
logger.debug("Storing data into SD Done.")

#
# REPORTING (state=3)
#
logger.debug("Reporting state=3 to CTLR ...")
response = socket_client.request('set,state{},3;set,rms{},{}'.format(iACC,iACC,rmsACC))
logger.debug("Reporting state=3 to CTLR Done.")

#
# SENDING FILE (state=4)
#
response = socket_client.request('set,state{},4'.format(iACC))
logger.debug("Transferring file to CTLR via FTP ...")
logger.debug("Remote Path={} ...".format('/sd/data/{}'.format(date_string(time_start))))
os.chdir('/sd')
out = dropfile.dropfile(CTLR_IPADDRESS, 21, '/sd/data/{}'.format(date_string(time_start)), 'micro', 'python', filename)
if out==0:
    logger.debug("success")
else:
    logger.debug('Failed.')
logger.debug("Transferring file to CTLR via FTP Done.")

# logger.info('creating a file ...')
# diskutil.create_file('/sd/gcam{}-acc{}-{}'.format(iCAM,iACC,datetime_string(time.time())),1)
# logger.info('creating a file Done.')
diskutil.house_keeping('/sd/',20,'acc')
logger.info('available space = {}GiB'.format(os.getfree('/sd')))

#
# DEEP SLEEP (state=5)
#
response = socket_client.request('set,state{},5'.format(iACC))
t_now = time.time()
res = (t_now+43)%T_exec
if res != 0:
    t_next = t_now + 43 - res + T_exec
else:
    t_next = t_now + 43
logger.debug('time_now  = {}'.format(datetime_string(t_now)))
logger.debug('time_next = {}'.format(datetime_string(t_next)))
logger.debug("Going to Sleep for {} seconds...".format(t_next-40 - (t_now)))
time.sleep(3)
ACC.py.setup_sleep(t_next-40 - (t_now+3))
ACC.py.go_to_sleep()
