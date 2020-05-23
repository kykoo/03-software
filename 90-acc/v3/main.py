import machine
import math
import network
import os
import time
from machine import SD
import pycom
from machine import Pin
from machine import RTC
import gc
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
import uerrno


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
wdt_timeout = 90*60*1000

# setup()      state0
# config()     state1
# measure()    state2
# deep_sleep() state3

def setup():
    global logger, rtc, sd, iCAM, iACC, CTLR_IPADDRESS, logfile, filename
    global wdt

    gc.enable()

    # HW Setup
    wdt = WDT(timeout=wdt_timeout)
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
    gc.collect()

    return

def config_measurement():
    #
    # GETTING TIME AND STATE OF CONTROLLER
    #
    global logger, rtc, sd, T_exec, T_meas, logfile_new
    logger.info('Config_measurement...')

    # GETTING STATE AND TIME FROM CTLR
    stateCTLR = None
    wdt = WDT(timeout=25*1000)
    while stateCTLR not in [2,4]:
        response = None
        while not response:
            requests = 'get,state;get,time;set,state{},1'.format(iACC)
            logger.info('sending request to CTLR: "{}"...'.format(requests))
            try:
                response = socket_client.request(requests)
            except:
                logger.exception('1st request failed.')
            # try:
            #     response = socket_client.request(requests)
            # except OSError as exc:
            #     # if exc.args[0] ==
            #     pass
            # except:
            #     raise
            time.sleep(1)
        response_list = response.split(';')
        stateCTLR = int(response_list[0])
        time_gps = int(response_list[1])
        rtc.init(time.localtime(time_gps))
        logger.info('stateCTLR = {} and time={}'.format(stateCTLR,rtc.now()))
    wdt.feed()
    wdt = WDT(timeout=wdt_timeout)

    # RENAME LOGFILE
    logfile_new = '/sd/log/{}.log'.format(datetime_string(time.time()))
    logging.fclose()
    os.rename(logfile,logfile_new)
    logging.basicConfig(level=logging.DEBUG,filename=logfile_new)

    if stateCTLR == 2:
        T_exec = 60*5
        T_meas = 20
    elif stateCTLR == 4:
        T_exec = 60*60
        T_meas = 60*3
    gc.collect()

    return

def measure():
    #
    # MEASURE
    #
    global T_meas, T_exec, T_now, T_start, X, Y, Z, rmsACC

    logger.info("Measuring ACC... ")
    ACC.setup()

    request = 'set,state{},2'.format(iACC)
    logger.info('sending request to the sever: "{}"'.format(request))
    response = socket_client.request(request)

    T_now = time.time()
    T_start = getNextGridTime(T_now+1, T_exec)
    logger.debug("T_cur={},{}".format(T_now,  datetime_string(T_now  )))
    logger.debug("T_st ={},{}".format(T_start,datetime_string(T_start)))
    logger.info("Waiting for {} seconds ...".format(T_start - T_now))
    waitUntil(T_start)

    # MESURING
    pycom.heartbeat(False)
    pycom.rgbled(0x000F00)
    logger.info('starting measuring...')
    X,Y,Z,Xrms,Yrms,Zrms,Xavg,Yavg,Zavg = ACC.measure(Td=T_meas)
    rmsACC = (Xrms**2+Yrms**2+Zrms**2)**0.5
    logger.info('Avg(X,Y,Z)=(%f,%f,%f)',Xavg,Yavg,Zavg)
    logger.info('RMS(X,Y,Z)=(%f,%f,%f)',Xrms,Yrms,Zrms)
    pycom.rgbled(0x000000)
    time.sleep_ms(100)
    pycom.heartbeat(True)

    gc.collect()
    return

def store_to_SD():
    global filename

    filename = '/sd/data/uploading/gcam{}-acc{}-'.format(iCAM,iACC) + datetime_string(T_start)
    with open(filename,'wb') as file:
        for i in range(len(X)):
            file.write(ustruct.pack('<ddd',X[i],Y[i],Z[i]))
        logger.info("data written to SD.")
    gc.collect()
    return

def send_file():

    _files = os.listdir('/sd/data/uploading')
    logger.info('{} file(s) to upload from /sd/data/uploading...'.format(len(_files)))
    time.sleep(15*(iACC-1))
    for _file in _files:
        _file_fullpath  = '/sd/data/uploading/' + _file
        # _file='gcam1-acc1-2020-0507-201110'
        #        0         0         0
        _dateStr   = _file[11:20]  # yyyy-mmdd
        _timestamp = _file[11:]    # yyyy-mmdd-HHMMSS
        _dest_path = '/sd/data/' + _dateStr
        logger.info("FTP to CTLR: Remote={} ...".format(_dest_path))
        os.chdir('/sd/data/uploading')

        iter = 0
        out = None
        while iter <3:
            try:
                out = dropfile.dropfile(CTLR_IPADDRESS, 21, _dest_path,'micro', 'python', _file)
                logger.debug('out={}'.format(out))
                if out ==0:
                    break # Successful
                if out == -1:
                    logger.debug('*************************************************')
                    logger.debug('retry dropfile, current_iter={}, connection timeout; svr busy'.format(iter))
                    logger.debug('*************************************************')
                    iter += 1
                    time.sleep(5) # waiting until the connection is closed by the svr
                    continue
                else:
                    logger.debug('*************************************************')
                    logger.debug('retry dropfile, current_iter={}, svr response out={}'.format(iter,out))
                    logger.debug('*************************************************')
                    iter += 1
                    time.sleep(5) # waiting until the connection is closed by the svr
                    continue
            except OSError as exc:
                # if exc.args[0] == uerrno.ECONNRESET or exc.args[0] == uerrno.ECONNABORTED or \
                #     exc.args[0] == uerrno.ETIMEDOUT:
                    logger.debug('*************************************************')
                    logger.exception('retry dropfile, current_iter={}, errorcode={}'.format(iter,exc.args[0]))
                    logger.debug('*************************************************')
                    time.sleep(30)
                    iter += 1
                    continue
            except:
                logger.debug('*************************************************')
                logger.exception('retry dropfile, current_iter={}, non-OSError'.format(iter))
                logger.debug('*************************************************')
                time.sleep(30)
                iter += 1
                continue
        if out==0:
            logger.info("FTP Successful.")
            _file_fullpath_new = _file_fullpath.replace('uploading','uploaded')
            os.rename(_file_fullpath, _file_fullpath_new)
            logger.info('file moved to uploaded folder.')
            request = 'set,file{},{};'.format(iACC,_timestamp)
            logger.info('sending request to the sever: "{}"'.format(request))
            response = socket_client.request(request)
        else:
            logger.info("****** FTP Failed after all *******")
    # filename='/sd/data/uploading/gcam1-acc1-2020-0507-201110'
    #           0         0         0         0         0
    timestamp = filename[30:] # yyyy-mmdd-HHMMSS
    request = 'set,state{},3;set,rms{},{},{:.6f};'.format(iACC,iACC,timestamp,rmsACC)
    logger.info('sending request to the sever: "{}"'.format(request))
    response = socket_client.request(request)

    diskutil.house_keeping('/sd/data/uploaded',25,'acc')
    diskutil.house_keeping('/sd/log',3,'log')
    logger.info('available space = {:,} bytes'.format(os.getfree('/sd')))
    gc.collect()
    return

def _deep_sleep():

    T_now = time.time()
    T_next = getNextGridTime(T_now + 90, T_exec) # 90 sec is time for booting
    logger.info('time_now  = {}'.format(datetime_string(T_now)))
    logger.info('time_next = {}'.format(datetime_string(T_next)))
    logger.info("Going to Sleep for {} seconds...".format(T_next-90 - (T_now)))
    time.sleep(2)

    ACC.py.setup_sleep(T_next-90 - T_now + 10*(iACC-1))
    gc.collect()
    ACC.py.go_to_sleep()

def deep_sleep():
    global T_now


    _deep_sleep()


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
    _deep_sleep()
