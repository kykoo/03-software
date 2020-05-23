import machine
import pycom
import time
import shmGPSclock
import logging
from machine import SD, Pin, WDT
import os
import _thread
from network import WLAN
import gc
from math import floor


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# CHANGE AP IN pybytes_config.json!
pbconfig = pybytes.get_config()
AP = pbconfig['wifi']['ssid']
logger.info('Starting CTLR via AP={}'.format(AP))

wdt = WDT(timeout=20*60*100)
# RELAYS
pin_relay_AP = Pin('P20',mode=Pin.OUT, pull=Pin.PULL_DOWN)
pin_relay_LED = Pin('P19',mode=Pin.OUT, pull=Pin.PULL_DOWN)
pin_switch_setupMode = Pin('P9',mode=Pin.IN, pull=Pin.PULL_DOWN)
pin_switch_RPi = Pin('P7',mode=Pin.OUT, pull=Pin.PULL_DOWN)

if AP == 'RUT230_7714':
    logger.debug('Turning AP on and wait for it to be ready...')
    pin_relay_AP.value(1)
    wlan = WLAN(mode=WLAN.STA)
    c = 0
    found_AP = False
    while not found_AP:
        logger.debug('scanning trial:{}...'.format(c))
        nets = wlan.scan()
        for net in nets:
            if net.ssid == 'RUT230_7714':
                logger.debug('Network found!')
                found_AP = True
        c += 1
    logger.debug('Turning AP on and wait for it to be ready done...')
    if not wlan.isconnected():
        logger.debug('connecting to Wifi...')
        if 1:
            pybytes.connect_wifi()
        else: # No Internet Case
            wlan.ifconfig(config=('192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8'))
            wlan.connect('RUT230_7714', auth=(WLAN.WPA2, 'Ei09UrDg'), timeout=5000)
            while not wlan.isconnected():
                machine.idle() # save power while waiting
        logger.debug('connecting to Wifi done...')

import socket_svr

sd = SD()
os.mount(sd,'/sd')
# logger.debug('SD: mem_alloc/free = {}/{}...'.format(gc.mem_alloc(),gc.mem_free()))

# SVR Socket Initialisation
logger.debug('Starting Socket Svr Thread...')
_thread.start_new_thread(socket_svr.accept_thread,())
logger.debug('Starting Socket Svr Thread Done.')
logger.debug('Sock: mem_alloc/free = {}/{}...'.format(gc.mem_alloc(),gc.mem_free()))

# UPDATE TIME BY GPS

logger.debug('Starting GPS time fix...')
shmGPSclock.update_RTC_from_GPS()
socket_svr.state = 1
logger.debug('Starting GPS time fix Done.')
logger.debug('GPS: mem_alloc/free = {}/{}...'.format(gc.mem_alloc(),gc.mem_free()))

# while True:
#     logger.debug('test')
#     time.sleep(1)

def last_hr():
    """Hour number of the latest hour"""
    t_now = time.time()
    return floor((t_now - floor(t_now/(24*3600))*24*3600)/3600)


def Dt():
    """Number of seconds after the latest hour"""
    t_now = time.time()
    return t_now - floor(t_now/3600)*3600

def toggle_pwr_RPi():
    pin_switch_RPi.value(1)
    time.sleep(0.4)
    pin_switch_RPi.value(0)
    return

def overThreshold():
    socket_svr.var_lock.acquire()
    acc_rms = socket_svr.acc_rms
    socket_svr.var_lock.release()
    over_threshold = []
    for rms in acc_rms:
        over_threshold.append(rms > socket_svr.acc_threshold)
    return any(over_threshold)

def checkWordDone(unitName):
    if unitName in 'acc':
        # read data
        socket_svr.var_lock.acquire()
        acc_state = socket_svr.acc_state
        socket_svr.var_lock.release()
        acc_workDone = []
        for state in acc_state:
            acc_workDone.append(state == 5)
        return all(acc_workDone)
    elif unitName in 'rpi':
        # read data
        socket_svr.var_lock.acquire()
        rpi_state = socket_svr.rpi_state
        socket_svr.var_lock.release()
        if rpi_state == 4:
            return True
        else:
            return False

def adminMode(turnOn):
    if turnOn:
        logger.debug('State Transition to 8 (Admin Mode)...')
        socket_svr.state = 8
    else:
        logger.debug('State Transition to 3 (Deploy Mode)...')
        socket_svr.state = 3
    return


while True:
    # DISPLAY BASIC INFORMATION
    setupMode = pin_switch_setupMode.value()
    socket_svr.var_lock.acquire()
    state = socket_svr.state
    acc_rms = socket_svr.acc_rms
    acc_state = socket_svr.acc_state
    rpi_state = socket_svr.rpi_state
    socket_svr.var_lock.release()

    logger.debug('state={}, setupMode={}, acc_state=[{}, {}, {}], acc_rms[{}, {}, {}], rpi_state={}'.\
            format(state,setupMode, acc_state[0],acc_state[1],acc_state[2],acc_rms[0],acc_rms[1],acc_rms[2],rpi_state))

    if socket_svr.state == 1:
        if setupMode:
            logger.debug('State Transition to 2 (Setup Mode), turning rpi on...')
            socket_svr.state = 2
            toggle_pwr_RPi() # turning on
        else:
            logger.debug('State Transition to 3 (Deploy Mode)...')
            socket_svr.state = 3
    elif socket_svr.state == 2:
        if not pin_switch_setupMode.value(): # setupMode
            logger.debug('State Transition to 3 (Deploy Mode), turning rpi off...')
            socket_svr.state = 3
            toggle_pwr_RPi() # turning off
    elif socket_svr.state == 3:
        if Dt() < 60*1: # start state=4 only after the beginning of each hr
            logger.debug('State Transition to 4 (DAQ Mode)...')
            socket_svr.state = 4
            socket_svr.acc_rms = [0.0, 0.0, 0.0]
            socket_svr.acc_state = [0, 0, 0]
        else:
            logger.debug('State Transition to 5 (Sleep Mode)...')
            socket_svr.state = 5
    elif socket_svr.state == 4:
        if overThreshold():
            logger.debug('State Transition to 6 (Video-Recording Mode), turning rpi on...')
            socket_svr.state = 6
            socket_svr.rpi_state = 0
            toggle_pwr_RPi() # turning on
        elif checkWorkDone('acc') or Dt() > 60*13: # go to sleep (state=5)
            logger.debug('State Transition to 5 (Sleep Mode)...')
            socket_svr.state = 5
    elif socket_svr.state == 5:
        if Dt() < 60*1:
            logger.debug('State Transition to 4 (DAQ Mode)...')
            socket_svr.state = 4
            socket_svr.acc_rms = [0.0, 0.0, 0.0]
            socket_svr.acc_state = [0, 0, 0]
        elif last_hr() == 4 and Dt() > 60*40:
            logger.debug('State Transition to 7 (Daily-Report Mode), turning rpi on...')
            socket_svr.state = 7
            socket_svr.rpi_state = 0
            toggle_pwr_RPi()  # turning on
    elif socket_svr.state == 6:
        if checkWorkDone('rpi') or Dt() > 60*30:
            logger.debug('State Transition to 5 (Sleep Mode)...')
            socket_svr.state = 5
    elif socket_svr.state == 7:
        if checkWorkDone('rpi') or (last_hr() == 4 and Dt() > 60*55):
            logger.debug('State Transition to 5 (Sleep Mode)...')
            socket_svr.state = 5

    # AP Power Control
    if socket_svr.state in [2,3,4,6,7,8]:
        pin_relay_AP.value(1)
    else:
        pin_relay_AP.value(0)
    wdt.feed()
    time.sleep(1)
