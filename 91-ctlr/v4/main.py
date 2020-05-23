import micropython
import gc
import machine
from machine import SD, Pin, WDT, Timer, ADC
import pycom
import sys
import time
import logging
import _thread
import os
from network import WLAN
from network import Server
from math import floor
import socket_svr
import shmGPSclock
from kk_util import *
# from pysense import Pysense
# from SI7006A20.py import SI7006A20



logger = None
pin_relay_AP = None
pin_relay_LED = None
pin_switch_setupMode = None
pin_switch_RPi = None
AP = None
sd = None
wtd = None
thread_id = None
server = None
server_timer = None
adc_c = None
# si7006a20 = None
#
taskTime_daily = None
# taskTime_hourly = None

#
# UTILITY FUNCTIONS
#

def mem_info():
    # print(micropython.mem_info())
    mem_heap_alloc = gc.mem_alloc()
    mem_heap_free = gc.mem_free()
    mem_heap_total = mem_heap_alloc + mem_heap_free
    mem_heap_alloc_ratio = mem_heap_alloc/mem_heap_total*100
    mem_stack_alloc = micropython.stack_use()
    # print('heap alloc = {:,}/{:,},{:.1f}% in use, stack in use={}'.format(mem_heap_alloc,mem_heap_total,mem_heap_alloc_ratio,mem_stack_alloc))
    return (mem_heap_alloc_ratio, mem_stack_alloc)

def last_hr():
    """Hour number of the latest hour"""
    t_now = time.time()
    return (t_now - t_now//(24*3600)*(24*3600))//3600

def last_10min():
    """Hour number of the latest hour"""
    t_now = time.time()
    return (t_now - (t_now//3600)*3600)//600

def Dt():
    """Number of seconds after the latest hour"""
    t_now = time.time()
    return t_now - (t_now//(60*10))*60*10

def toggle_pwr_RPi():
    pin_switch_RPi.value(1)
    time.sleep(0.4)
    pin_switch_RPi.value(0)
    return

def overThreshold():
    isCompleted  = [ socket_svr.acc_state[i] == 3 for i in range(3)]
    isOverThresh = [ socket_svr.acc_rms[2*i+1] > socket_svr.acc_threshold[i] for i in range(3)]
    for i in range(3):
        if isCompleted[i] and isOverThresh[i]:
            return True
    return False

def checkWorkDone(unitName):
    if unitName in 'acc':
        # read data
        acc_workDone = [(state == 3) for state in socket_svr.acc_state]
        return all(acc_workDone)
    elif unitName in 'rpi':
        # read data
        return (socket_svr.rpi_state == 4)

def restart_server(alarm):
    server.deinit()
    server = Server(login=('micro','python'),timeout=60)
    logger.info('Server restarted.')
    return

def setup():
    global wdt, sd, logger, AP, pin_relay_AP, pin_relay_LED, pin_switch_setupMode, pin_switch_RPi,wdt
    global server, server_timer, adc_c, taskTime_daily, taskTime_hourly

    # Logger
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    logger.info('===========================')
    logger.info(' Starting CTLR ')
    logger.info('===========================')

    # HW Setup
    wdt = WDT(timeout=20*60*1000)
    wdt.feed()
    sd = SD()
    os.mount(sd,'/sd')
    adc = machine.ADC()
    # adc_c = adc.channel(pin='P19', attn=ADC.ATTN_11DB)
    adc_c = adc.channel(pin='P18', attn=ADC.ATTN_11DB)
    # Output Vref of P22
    # adc.vref_to_pin('P22')
    # while True:
    #     time.sleep(1)
    # Set calibration - see note above
    adc.vref(1100)

    # # TEMPERATURE/HUMIDITY SENSOR
    # py = Pysense()
    # si7006a20  = SI7006A20(py)

    pin_relay_AP = Pin('P20',mode=Pin.OUT, pull=Pin.PULL_DOWN)
    pin_relay_LED = Pin('P19',mode=Pin.OUT, pull=Pin.PULL_DOWN)
    pin_switch_setupMode = Pin('P9',mode=Pin.IN, pull=Pin.PULL_DOWN)
    pin_switch_RPi = Pin('P7',mode=Pin.OUT, pull=Pin.PULL_DOWN)

    # Network Setup
    # CHANGE AP IN pybytes_config.json!
    pbconfig = pybytes.get_config()
    AP = pbconfig['wifi']['ssid']

    # WIFI Connection
    if AP in ['GCAM1_AP', 'GCAM2_AP', 'GCAM2_AP']:
        pin_relay_AP.value(1)
        wlan = WLAN(mode=WLAN.STA)
        while not wlan.isconnected():
            nets = wlan.scan()
            logger.info(nets)
            if AP in [net.ssid for net in nets]:
                pybytes.connect_wifi()
            time.sleep(5)
            # for net in nets:
            #     if net.ssid == 'RUT230_7714':
            #         pybytes.connect_wifi()
        # # No Internet Case
        # wlan.ifconfig(config=('192.168.1.100', '255.255.255.0', '192.168.1.1', '8.8.8.8'))
        # wlan.connect('RUT230_7714', auth=(WLAN.WPA2, 'Ei09UrDg'), timeout=5000)
        # while not wlan.isconnected():
        #     machine.idle() # save power while waiting

    socket_svr.switch_setupMode = pin_switch_setupMode.value()
    socket_svr.setup()
    # _thread.stack_size(16384)

    # UPDATE TIME BY GPS
    logger.info('GPS time fixing start...')
    shmGPSclock.update_RTC_from_GPS()
    socket_svr.state = 1
    logger.info('GPS time fixing done...')

    server = Server()
    server.timeout(5)

    # Creating data/date folder of today
    dirToday = '/sd/data/{}'.format(date_string(time.time()))
    if mkdir(dirToday):
        logger.info('{} created'.format(dirToday))
    gc.enable()

    # CREATING FOLDER FOR FTP
    mkdir('/sd/data/{}'.format(date_string(time.time())))
    # PERIODIC TASKS
    taskTime_daily  = getNextGridTime(time.time(),3600*24)
    taskTime_hourly = getNextGridTime(time.time(),3600)
    # # FTP Server restarting every 10 mins
    # T_now = time.time()
    # T_next = getNextGridTime(T_now, 60*2)
    # logger.info('Waiting for the next gridTime {}sec'.format(T_next-T_now))
    # waitUntil(T_next)
    # server_timer = Timer.Alarm(restart_server,60*10,periodic=True)

def battery_volt():
    adc_c()
    return adc_c.voltage()/1000
# def measure_temp_humidity(timestamp):
#     temperature = si7006a20.temperature()
#     humidity = si7006a20.humidity()
#     datetime_str = datetime_string(timestamp)
#     fileName = '/sd/data/{}/gcam{}-si7-{}.csv'.format(date_string(timesamp),socket_svr.iCAM,datetime_str)
#     with open(fileName,'a') as file:
#         file.write('{}, {:.1f}, {:.1f}'.format(timestamp_str,temperature,humidity))
#     return

# *8 - *3: S4
# *3 - *5: S5
# *5 -   : S7
def stateTimeout(state):

    n1 = 6  # start    of S4 measuring
    n2 = 3  # deadline of S4 measuring
    n3 = 6  # deadline of S6 video rec

    if state == 4:
        return 60*n2  < Dt() < 60*n1
    elif state == 5:
        return 60*n1 < Dt()
    elif state==6:
        return 60*n3 < Dt()
    elif state==7:
        return 60*n1 < Dt()
    elif state==67:
        return 60*n1 < Dt()

def isDailyReportTime():
    return last_10min() == 1 # or last_10min() == 4
#
# MAIN LOOP
#

setup()
print('setup() executed ===================')
mem_info()

# uploadedToday = False


# STATE TRANSITION RULES AND CALLBACKS
while True:

    socket_svr.accept()

    # DISPLAY BASIC INFORMATION
    mem = mem_info()
    volt = battery_volt()

    setupMode = pin_switch_setupMode.value()
    state = socket_svr.state
    acc_rms = socket_svr.acc_rms
    acc_state = socket_svr.acc_state
    rpi_state = socket_svr.rpi_state
    pwrLED = socket_svr.pwrLED
    socket_svr.switch_setupMode = setupMode
    socket_svr.mem = mem
    socket_svr.disk = disk_status()
    socket_svr.volt = volt

    # logger.info('state={},setupMode={},acc_state=[{},{},{}],acc_rms[{:.1f},{:.1f},{:.1f}]mg,rpi_state={},mem={}'.\
    #         format(state,setupMode, acc_state[0],acc_state[1],acc_state[2],acc_rms[0]*1e3,acc_rms[1]*1e3,acc_rms[2]*1e3,rpi_state,gc.mem_free()))
    logger.info('S={},M={},AS=[{},{},{}],R=[{:.0f},{:.0f},{:.0f}]mg,RS={},h={:.0f}%,s={:,},l={}'.\
        format(state,setupMode, acc_state[0],acc_state[1],acc_state[2],acc_rms[1]*1e3,acc_rms[3]*1e3,acc_rms[5]*1e3,rpi_state,mem[0],mem[1],pwrLED))


    # STATE = 1 ----------------------------------------------------------------
    if socket_svr.state == 1:
        if setupMode==1:
            logger.info('State Transition to 2 (Setup Mode), turning rpi on...')
            socket_svr.state = 2
            toggle_pwr_RPi() # turning on
        if setupMode==0:
            logger.info('State Transition to 3 (Deploy Mode)...')
            socket_svr.state = 3

    # STATE = 2 ----------------------------------------------------------------
    elif socket_svr.state == 2:
        if setupMode ==1:
            pass # do nothing
        if setupMode ==0: # setupMode
            logger.info('State Transition to 3 (Deploy Mode)...')
            socket_svr.state = 3

    # STATE = 3 ----------------------------------------------------------------
    elif socket_svr.state == 3:
        if setupMode==1:
            logger.info('State Transition to 2 (Setup Mode)...')
            toggle_pwr_RPi() # turning on
            socket_svr.state = 2
        elif not stateTimeout(4):
            logger.info('State Transition to 4 (DAQ Mode)...')
            socket_svr.state = 4
            socket_svr.acc_state = [0,0,0]
        else:
            logger.info('State Transition to 5 (Sleep Mode)...')
            socket_svr.state = 5

    # STATE = 4 ----------------------------------------------------------------
    elif socket_svr.state == 4:
        if setupMode==1:
            logger.info('State Transition to 2 (Setup Mode)...')
            socket_svr.state = 2
            toggle_pwr_RPi() # turning on
        elif overThreshold() == True:
            if isDailyReportTime():
                logger.info('State Transition to 6/7 (Video-Recording/Daily Report Mode), turning rpi on...')
                socket_svr.state = 67
                socket_svr.rpi_state = 1
                toggle_pwr_RPi() # turning on
            else:
                logger.info('State Transition to 6 (Video-Recording Mode), turning rpi on...')
                socket_svr.state = 6
                socket_svr.rpi_state = 1
                toggle_pwr_RPi() # turning on
        elif checkWorkDone('acc') or stateTimeout(socket_svr.state):
            if isDailyReportTime():
                logger.info('State Transition to 7 (Daily-Report Mode)...')
                socket_svr.state = 7
                socket_svr.rpi_state = 1
                toggle_pwr_RPi()  # turning on
            else:
                logger.info('State Transition to 5 (Sleep Mode)...')
                socket_svr.state = 5

    # STATE = 5 ----------------------------------------------------------------
    elif socket_svr.state == 5:
        if setupMode==1:
            logger.info('State Transition to 2 (Setup Mode)...')
            socket_svr.state = 2
            toggle_pwr_RPi() # turning on
        elif stateTimeout(socket_svr.state):
            logger.info('State Transition to 4 (DAQ Mode)...')
            socket_svr.state = 4
            socket_svr.acc_state = [0,0,0]

    # STATE = 6 ----------------------------------------------------------------
    elif socket_svr.state == 6:
        if setupMode==1:
            logger.info('State Trasition from 6 to 2 Not Allowed...')
        elif checkWorkDone('rpi') or stateTimeout(socket_svr.state):
            # if isDailyReportTime():
            #     logger.info('State Transition to 7 (Daily-Report Mode)...')
            #     socket_svr.state = 7
            #     socket_svr.rpi_state = 1
            #     toggle_pwr_RPi()  # turning on
            # else:
            logger.info('State Transition to 5 (Sleep Mode)...')
            socket_svr.state = 5

    # STATE = 7 ----------------------------------------------------------------
    elif socket_svr.state == 7:
        if setupMode==1:
            logger.info('State Transition from 7 to 2 Not Allowed ...')
            # socket_svr.state = 2
        elif checkWorkDone('rpi') or stateTimeout(socket_svr.state):
            logger.info('State Transition to 5 (Sleep Mode)...')
            socket_svr.state = 5
    # STATE = 67 ----------------------------------------------------------------
    elif socket_svr.state == 67:
        if setupMode==1:
            logger.info('State Transition from 67 to 2 Not Allowed ...')
            # socket_svr.state = 2
        elif checkWorkDone('rpi') or stateTimeout(socket_svr.state):
            logger.info('State Transition to 5 (Sleep Mode)...')
            socket_svr.state = 5
    # STATE = 8 ----------------------------------------------------------------
    # NO RULES FOR STATE8

    # AP Power Control
    if socket_svr.state in [2,3,4,6,7,67,8]:
        pin_relay_AP.value(1)
    else:
        pin_relay_AP.value(0)

    # pwrLED
    if pwrLED==1:
        pin_relay_LED.value(1)
    else:
        pin_relay_LED.value(0)

    wdt.feed()

    #
    # PERIODIC TASKS
    #
    t_now = time.time()
    # DAILY TASK
    # logger.debug('t_now {}, taskTime_daily {}'.format(datetime_string(t_now), datetime_string(taskTime_daily)))
    if  t_now >= taskTime_daily:
        # prepare a folder every day
        # mkdir('/sd/data/{}'.format(date_string(taskTime_daily)))
        # uploadedToday = False
        taskTime_daily = getNextGridTime(t_now,3600*24)
    # # HOURLY TASK
    # if t_now >= taskTime_hourly:
    #     measure_temp_humidity(taskTime_hourly)
    #     taskTime_hourly = getNextGridTime(t_now,3600)

    gc.collect()
    # time.sleep(1)

# os.fsformat('/sd')
# os.mkdir('/sd/data')
# os.mkdir('/sd/data/incoming')
# os.mkdir('/sd')
