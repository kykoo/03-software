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
from onewire import DS18X20
from onewire import OneWire
from pysense import Pysense
from SI7006A20 import SI7006A20

uploading_dir = '/sd/data/uploading'
uploaded_dir = '/sd/data/'
remote_incoming_dir = '/sd/data/incoming'    # the remote folder in CTLR

debug_mode = True
debug_mode = False

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
acc = None
acc_d = None
rmsdACC = None
CTLR_IPADDRESS = '192.168.1.51'
filename = None
openSD = None
logfile = None
logfile_new = None
wdt = None
wdt_timeout = 90*60*1000 # 90 mins
ow = None
temp = None
py = None
sensor = None


# setup()      state0
# config()     state1
# measure()    state2
# deep_sleep() state3

def setup():
    global logger, rtc, sd, iCAM, iACC, CTLR_IPADDRESS, logfile, filename
    global wdt, ow, temp, py, sensor

    gc.enable()

    # HW Setup
    wdt = WDT(timeout=wdt_timeout)
    sd = SD()
    rtc = RTC()
    os.mount(sd,'/sd')
    # Enable WiFi Antenna
    Pin('P12', mode=Pin.OUT)(True)

    # TEMPERATURE SENSORS: DS18B20 and SI7006A20
    ow = OneWire(Pin('P10'))
    temp = DS18X20(ow)
    py = Pysense()
    sensor = SI7006A20(py)


    # SYSTEM VARIABLES
    iCAM = pycom.nvs_get('iCAM') # pycom.nvs_set('iCAM',1)
    iACC = pycom.nvs_get('iACC') # pycom.nvs_set('iACC',1)

    logfile='/sd/log/{}.log'.format(datetime_string(time.time()))
    logging.basicConfig(level=logging.DEBUG,filename=logfile)
    logger = logging.getLogger(__name__)

    # # NETWORK VARIABLES
    # pbconf = pybytes.get_config()
    # AP = pbconf['wifi']['ssid']
    # if AP == 'wings':
    #     CTLR_IPADDRESS = '192.168.1.51'
    # elif AP == 'RUT230_7714':
    #     CTLR_IPADDRESS = '192.168.1.100'
    #     # CONNECT TO AP
    #     wlan = WLAN(mode=WLAN.STA)
    #     while not wlan.isconnected():
    #         nets = wlan.scan()
    #         for net in nets:
    #             if net.ssid == 'RUT230_7714':
    #                 pybytes.connect_wifi()
    #
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

def config_measurement():
    #
    # GETTING TIME AND STATE OF CONTROLLER
    #
    global logger, rtc, sd, T_exec, T_meas, logfile_new
    global acc, acc_d, wdt_timeout


    logger.info('Config_measurement...')

    # GETTING STATE AND TIME FROM CTLR
    stateCTLR = None
    wdt = WDT(timeout=25*1000)
    while True:
        requests = 'get,state;get,time;set,state{},1'.format(iACC)
        logger.info('sending request to CTLR: "{}"...'.format(requests))
        try:
            response = socket_client.request(requests)
        except:
            logger.exception('The Step1 Request failed.')
        if response:
            response_ = response.split(';')
            stateCTLR = int(response_[0])
            if stateCTLR not in [1]:
                time_gps = int(response_[1])
                rtc.init(time.localtime(time_gps))
                break
        time.sleep(1)
    logger.info('stateCTLR = {} and time={}'.format(stateCTLR,rtc.now()))
    wdt.feed()

    # RENAME LOGFILE
    logfile_new = '/sd/log/{}.log'.format(datetime_string(time.time()))
    logging.fclose()
    os.rename(logfile,logfile_new)
    logging.basicConfig(level=logging.DEBUG,filename=logfile_new)

    logger.info('stateCTLR={}'.format(stateCTLR))

    if stateCTLR in [2,8]:
        logger.info('stateCTLR in [2,8]={}'.format(stateCTLR in [2,8]))
        T_exec = 60*5
        T_meas = 20
        # T_meas = 60*3
        # T_meas = 10
    elif stateCTLR in [4]:
        T_exec = 60*10
        T_meas = 60*1
    elif stateCTLR in [3,5,6,7]:
        logger.info('stateCTLR in [3,5,6,7]={}'.format(stateCTLR in [3,5,6,7]))
        T_exec = 60*10
        T_meas = 60*1
        deep_sleep()

    wdt_timeout = int(T_exec*1000*1.5)
    wdt = WDT(timeout=wdt_timeout)
    acc   = [array.array('f', [0.0 for j in range(T_meas*100)]) for i in range(3)]
    acc_d = [array.array('f', [0.0 for j in range(T_meas*100)]) for i in range(3)]

    gc.collect()

    return

def measure_acc():
    #
    # MEASURE
    #
    global T_meas, T_exec, T_now, T_start, acc, acc_d, rmsdACC


    logger.info("=== Measuring ACC ===".format(T_meas))
    ACC.setup()

    request = 'set,state{},2'.format(iACC)
    logger.info('sending request to the sever: "{}"'.format(request))
    response = socket_client.request(request)

    T_now = time.time()
    logger.debug('T_now={}'.format(T_now))
    logger.debug('T_exec={}'.format(T_exec))
    T_start = getNextGridTime(T_now+1, T_exec)
    logger.debug("T_cur={},{}".format(T_now,  datetime_string(T_now  )))
    logger.debug("T_st ={},{}".format(T_start,datetime_string(T_start)))
    logger.info("Waiting for {} seconds ...".format(T_start - T_now))
    if debug_mode == False:
        waitUntil(T_start)

    # MESURING
    pycom.heartbeat(False)
    pycom.rgbled(0x000F00)
    logger.info('starting measuring for {} sec...'.format(T_meas))

    ACC.measure(acc, Td=T_meas)

    pycom.rgbled(0x000000)
    time.sleep_ms(100)
    pycom.heartbeat(True)

    decimate(acc, acc_d, 4)

    mean_ = mean(acc_d)
    rmsd_ = rmsd(acc_d)
    rmsdACC = (rmsd_[0]**2+rmsd_[1]**2+rmsd_[2]**2)**0.5
    logger.info('Avg(X,Y,Z)=(%f,%f,%f)',mean_[0],mean_[1],mean_[2])
    logger.info('RMS(X,Y,Z)=(%f,%f,%f)',rmsd_[0],rmsd_[1],rmsd_[2])

    gc.collect()
    return

def store_to_SD():
    global filename

    filename = '{}/gcam{}-acc{}-acc-{}'.format(uploading_dir,iCAM,iACC,datetime_string(T_start))
    with open(filename,'wb') as file:
        for j in range(len(acc_d[0])):
            if j%4 == 0:
                file.write(ustruct.pack('<fff',acc_d[0][j],acc_d[1][j],acc_d[2][j]))
                # file.write(ustruct.pack('<fff',acc[0][j],acc[1][j],acc[2][j]))
        logger.info("data written to SD.")
    gc.collect()
    return

def measure_temperature():

    try:
        tmp1 = temp.measure()
    except:
        tmp1 = -100
    try:
        tmp2 = sensor.temperature()
        hum = sensor.humidity()
    except:
        tmp2 = -100
        hum = -100

    tmp_datafile = '{}/gcam{}-acc{}-tmp-{}.csv'.format(uploading_dir,iCAM,iACC,date_string(time.time()))
    with open(tmp_datafile,'a') as file:
        file.write('{}, {:.1f},{:.1f},{:.0f}\n'.format(datetime_string(T_start), tmp1, tmp2, hum))
    return

def send_file():

    logger.info("FTP to CTLR: Remote={} ...".format(remote_incoming_dir))

    files = os.listdir(uploading_dir)

    logger.info('{} file(s) found on {}...'.format(len(files),uploading_dir))
    time.sleep(15*(iACC-1))

    for file in files:
        if 'tmp-{}'.format(date_string(today())) in file: # Skip unfinished temperature file
            logger.info('ftp skipped on {}.'.format(file))
            continue
        # file='gcam1-acc1-acc-2020-0507-201110'
        #       0         0         0        0
        timestamp = file[15:]    # yyyy-mmdd-HHMMSS
        os.chdir(uploading_dir)

        iter = 0
        out = None
        while iter <3:
            try:
                out = dropfile.dropfile(CTLR_IPADDRESS, 21, remote_incoming_dir,'micro', 'python', file)
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
            logger.info("FTP Successful for {}".format(file))
            # MOVE UPLOADED FILES INTO UPLOADED_DIR
            # yyyy-mmdd-HHMMSS
            # 0         0
            yearString = timestamp[:4]
            monthdayString = timestamp[5:9]
            target_dir   = '{}/{}/{}'.format(uploaded_dir, yearString, monthdayString)
            target_dir_p = '{}/{}'.format(uploaded_dir, yearString)
            mkdir(target_dir_p)
            mkdir(target_dir)
            os.rename('{}/{}'.format(uploading_dir,file), '{}/{}'.format(target_dir,file))
            logger.info('file moved to uploaded folder.')
            if '-acc-' in file:
                request = 'set,file{},{};'.format(iACC,timestamp)
                logger.info('sending request to the sever: "{}"'.format(request))
                response = socket_client.request(request)
        else:
            logger.info("****** FTP Failed after all *******")
    timestamp = datetime_string(T_start) # yyyy-mmdd-HHMMSS
    request = 'set,state{},3;set,rms{},{},{:.3f};'.format(iACC,iACC,timestamp,rmsdACC)
    logger.info('sending request to the sever: "{}"'.format(request))
    response = socket_client.request(request)

    # diskutil.house_keeping('/sd/data',15,'acc')
    # diskutil.house_keeping('/sd/data/uploading',10,'acc')
    # diskutil.house_keeping('/sd/log',3,'log')
    # logger.info('available space = {:,} bytes'.format(os.getfree('/sd')))
    gc.collect()
    return

if debug_mode:
    setup()
    config_measurement()
    measure_acc()
    measure_temperature()
    store_to_SD()
    send_file()
else:
    try:
        setup()
        config_measurement()
        measure_acc()
        measure_temperature()
        store_to_SD()
        send_file()
        deep_sleep()
    except Exception:
        pass
        # logger.exception('Unknown exception caught for emailing...')
        # logging.fclose()
        #
        # to = 'dr.ki.koo@gmail.com'
        # subject = 'WG: Exception Report from GCAM{}-ACC{}'.format(iCAM,iACC)
        # logger.info('logfile_new={}'.format(logfile_new))
        # with open(logfile_new, 'r') as file:
        #     logs = file.read()
        # contents = 'Log file\n--------\n' + logs
        # gmail.send(to,subject,contents)
    finally:
        _deep_sleep()


# import os
# from machine import SD
# sd = SD()
# os.mount(sd,'/sd')
# os.fsformat('/sd')
# os.mkdir('/sd/data')
# os.mkdir('/sd/data/uploading')
# os.mkdir('/sd/log')
