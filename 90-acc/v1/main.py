import machine
import math
import network
import os
import time
# import gc
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
from kk_util import *
import gmail
import sys


iCAM = None
iACC = None
logger = None
AP = None
rtc = None
sd = None
T_exec = None
T_meas = None
T_now = None
T_start = None
X = None
Y = None
Z = None
rmsACC = None
CTLR_IPADDRESS = None
filename = None
openSD = None
logfile = None
logfile_new = None
wdt = None

# setup()      state0
# config()     state1
# measure()    state2
# deep_sleep() state3

def setup():
    global logger, rtc, sd, iCAM, iACC, CTLR_IPADDRESS, logfile, filename
    global wdt

    # HW Setup
    wdt = WDT(timeout=20*1000)
    sd = SD()
    rtc = RTC()
    os.mount(sd,'/sd')

    # SYSTEM VARIABLES
    iCAM = pycom.nvs_get('iCAM') # pycom.nvs_set('iCAM',1)
    iACC = pycom.nvs_get('iACC') # pycom.nvs_set('iACC',1)

    logfile='/sd/log/{}.log'.format(datetime_string(time.time()))
    logging.basicConfig(level=logging.DEBUG,filename=logfile)
    logger = logging.getLogger(__name__)

    # NETWORK VARIABLES
    pbconf = pybytes.get_config()
    AP = pbconf['wifi']['ssid']
    if AP == 'wings':
        CTLR_IPADDRESS = '192.168.1.51'
    elif AP == 'RUT230_7714':
        CTLR_IPADDRESS = '192.168.1.100'
        # CONNECT TO AP
        wlan = WLAN(mode=WLAN.STA)
        while not wlan.isconnected():
            nets = wlan.scan()
            for net in nets:
                if net.ssid == 'RUT230_7714':
                    pybytes.connect_wifi()
        # wlan.ifconfig(config=('192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8'))
        # wlan.connect('RUT230_7714', auth=(WLAN.WPA2, 'Ei09UrDg'), timeout=5000)
        # while not wlan.isconnected():
        #     machine.idle() # save power while waiting
    socket_client.CTLR_IPADDRESS = CTLR_IPADDRESS

    # GREETING
    logger.info('--------------------')
    logger.info(' Starting CAM{}-ACC{}'.format(iCAM, iACC))
    logger.info('--------------------')
    logger.info('AP={}'.format(AP))
    return

def config_measurement():
    #
    # GETTING TIME AND STATE OF CONTROLLER
    #
    global logger, rtc, sd, T_exec, T_meas, logfile_new
    logger.info('Config_measurement...')

    # GETTING STATE AND TIME FROM CTLR
    stateCTLR = None
    while stateCTLR not in [2,4]:
        response = None
        while not response:
            requests = 'get,state;get,time;set,state{},1'.format(iACC)
            response = socket_client.request(requests)
            logger.info('request sent to CTLR:{}...'.format(requests))
            time.sleep(1)
        response_list = response.split(';')
        stateCTLR = int(response_list[0])
        time_gps = int(response_list[1])
        rtc.init(time.localtime(time_gps))
        logger.info('stateCTLR={} and time={}'.format(stateCTLR,rtc.now()))

    logger.info('Starting ACC node job...')
    # RENAME LOGFILE
    logfile_new = '/sd/log/{}.log'.format(datetime_string(time.time()))
    logging.fclose()
    os.rename(logfile,logfile_new)
    logging.basicConfig(level=logging.DEBUG,filename=logfile_new)

    if stateCTLR == 2:
        T_exec = 60
        T_meas = 5
    elif stateCTLR == 4:
        T_exec = 3600
        T_meas = 60*3
    return

def measure():
    #
    # MEASURE
    #
    global T_meas, T_exec, T_now, T_start, X, Y, Z, rmsACC

    logger.info("Measuring ACC... ")
    response = socket_client.request('set,state{},2'.format(iACC))
    ACC.setup()

    T_now = time.time()
    T_start = getNextGridTime(T_now+1, T_exec)
    logger.debug("T_cur={},{}".format(T_now,  datetime_string(T_now  )))
    logger.debug("T_st ={},{}".format(T_start,datetime_string(T_start)))
    logger.info("Waiting for {} seconds ...".format(T_start - T_now))
    waitUntil(T_start)

    # MESURING
    pycom.heartbeat(False)
    pycom.rgbled(0x000F00)
    X,Y,Z,Xrms,Yrms,Zrms,Xavg,Yavg,Zavg = ACC.measure(Td=T_meas)
    rmsACC = (Xrms**2+Yrms**2+Zrms**2)**0.5
    logger.info('Avg(X,Y,Z)=(%f,%f,%f)',Xavg,Yavg,Zavg)
    logger.info('RMS(X,Y,Z)=(%f,%f,%f)',Xrms,Yrms,Zrms)
    pycom.rgbled(0x000000)
    time.sleep_ms(100)
    pycom.heartbeat(True)
    return

def store_to_SD():
    global filename

    logger.info("Storing data into SD...")
    filename = '/sd/gcam{}-acc{}-'.format(iCAM,iACC) + datetime_string(T_start)
    with open(filename,'wb') as file:
        for i in range(len(X)):
            file.write(ustruct.pack('<ddd',X[i],Y[i],Z[i]))
    return

def send_file():
    logger.info("FTP to CTLR ...")
    logger.info("Remote={} ...".format('/sd/data/{}'.format(date_string(T_start))))
    os.chdir('/sd')
    # out = dropfile.dropfile(CTLR_IPADDRESS, 21, '/sd/data/{}'.format(date_string(T_start)), 'micro', 'python', filename)
    out = dropfile.dropfile(CTLR_IPADDRESS, 21, '/sd/data', 'micro', 'python', filename)
    if out==0:
        logger.info("FTP Successful.")
    else:
        logger.info("FTP Failed.")
    diskutil.house_keeping('/sd/data',20,'acc')
    logger.info('available space = {}GiB'.format(os.getfree('/sd')))

def deep_sleep():
    global T_now

    response = socket_client.request('set,state{},3'.format(iACC))
    T_now = time.time()
    T_next = getNextGridTime(T_now + 43, T_exec)
    logger.info('time_now  = {}'.format(datetime_string(T_now)))
    logger.info('time_next = {}'.format(datetime_string(T_next)))
    logger.info("Going to Sleep for {} seconds...".format(T_next-40 - (T_now)))
    time.sleep(3)

    ACC.py.setup_sleep(T_next-40 - (T_now+3))
    ACC.py.go_to_sleep()
    return

def deep_sleep_exception():
    T_now = time.time()
    T_next = getNextGridTime(T_now + 43, T_exec)
    logger.info('time_now  = {}'.format(datetime_string(T_now)))
    logger.info('time_next = {}'.format(datetime_string(T_next)))
    logger.info("Going to Sleep for {} seconds...".format(T_next-40 - (T_now)))
    time.sleep(3)

    ACC.py.setup_sleep(T_next-40 - (T_now+3))
    ACC.py.go_to_sleep()
    return

try:
    setup()
    config_measurement()
    measure()
    store_to_SD()
    send_file()
    deep_sleep()
except Exception:
    logger.exception('Unknown exception caught for emailing...')
    logging.fclose()

    to = 'dr.ki.koo@gmail.com'
    subject = 'WG: Exception Report from GCAM{}-ACC{}'.format(iCAM,iACC)
    logger.info('logfile_new={}'.format(logfile_new))
    with open(logfile_new, 'r') as file:
        logs = file.read()
    contents = 'Log file\n--------\n' + logs
    gmail.send(to,subject,contents)
finally:
    deep_sleep_exception()
