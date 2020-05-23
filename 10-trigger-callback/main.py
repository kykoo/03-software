from machine import Pin
import time
import _thread
import logging
import pycom


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("__main__")

pycom.heartbeat(False)

DEV_PWR_STATE = 0   # bits representing the current PWR state of [ ... CAM RPI Modem]
                    # only lower 3 bits used
DEV_PWR_CMD_M = 0   # bits representing commands for Modem from various sources
                    # [ ...   Wake-up-override Scheduled-Wake-Up Trigger]
                    # only lower 3 bits used
DEV_PWR_CMD_R = 0   # The same for Raspberry Pi
DEV_PWR_CMD_C = 0   # The same for Camera

trigStates = {
              'tr':[0.0,0.0,0.0],   # rising edge time
              'tf':[0.0,0.0,0.0],   # falling edge time
              'dt':[None,None,None],# time difference between above
              'flag':0,             # Flag
              'State': 0,           # 0: listening state, 1: recording state
              'dT': 3,              # The duration of trigger-invoked actions
              't_end':0             # = now + dT, End time for trigger-invoked actions
             }

trigStates_lock = _thread.allocate_lock()

swState = {'t0':0, 't1':10000, 'State':0}

def trigger_handler(arg):
    global trigStates, trigStates_lock
    # for e.g. arg.id()='P9', trigID = 9, idx=0
    trigID = int(arg.id()[1:])
    idx = trigID - 9
    if arg.value() == 1:
        trigStates_lock.acquire()
        trigStates['tr'][idx] = time.ticks_ms()
        trigStates_lock.release()
        logger.debug("trigger_handler: rising edge detected at pin %s", arg.id())
    else:
        tf = time.time()
        trigStates_lock.acquire()
        trigStates['tf'][idx] = time.ticks_ms()
        trigStates['dt'][idx] = trigStates['tf'][idx] - trigStates['tr'][idx]
        # logger.debug('trigger_handler: tr=%d, tf=%d, dt=%d',trigStates['tr'][idx],trigStates['tf'][idx],trigStates['dt'][idx])
        if 500 < trigStates['dt'][idx] and trigStates['dt'][idx]  < 1500:
            trigStates['flag'] = trigStates['flag'] | 1 << idx
            logger.debug('trigger_handler: falling edge detected at pin %s, flag condition met', arg.id())
        else:
            logger.debug('trigger_handler: falling edge detected at pin %s, flag condition NOT met', arg.id())
        trigStates_lock.release()




trigPins = []
for i in range(3):
    trigPins.append(Pin('P{}'.format(i+9), mode=Pin.IN, pull=Pin.PULL_DOWN))
    trigPins[i].callback(Pin.IRQ_RISING|Pin.IRQ_FALLING, trigger_handler)

def enableTriggerHandler(cmd):
    global trigPins
    for i in range(3):
        if cmd:
            trigPins[i].callback(Pin.IRQ_RISING|Pin.IRQ_FALLING, trigger_handler)
        else:
            trigPins[i].callback(Pin.IRQ_RISING|Pin.IRQ_FALLING, None)

def bitRead(number,pos):
    return (number & 1<<pos) >> pos


count = 0
while (True):

    # Trigger Source Handling
    trigStates_lock.acquire()
    if trigStates['State']==0:  # Listening mode
        if trigStates['flag']:
            logger.debug('State=%d, flag=%d', trigStates['State'], trigStates['flag'])
            logger.debug(' State transiention to 1')
            DEV_PWR_CMD_M |= 1<<0
            DEV_PWR_CMD_R |= 1<<0
            DEV_PWR_CMD_C |= 1<<0
            trigStates['State'] = 1
            trigStates['t_end'] = time.time() + trigStates['dT']
            enableTriggerHandler(False)
    elif trigStates['State']==1:  # Video recording mode
        if time.time() < trigStates['t_end']:
            logger.debug(' Keep recording...')
            pass
        else:
            logger.debug(' Recording terminating after timeout...')
            trigStates['flag'] = 0
            trigStates['State'] = 0
            DEV_PWR_CMD_M &= ~(1<<0)
            enableTriggerHandler(True)
    trigStates_lock.release()

     


    # PWR CONTROL FOR 3G MODEM
    if bitRead(DEV_PWR_STATE,0)==0 and DEV_PWR_CMD_M:
        logger.debug('Power Controlling: 3G modem: powering on')
        DEV_PWR_STATE |= 1<<0
        pycom.rgbled(0xFF0000)
    elif bitRead(DEV_PWR_STATE,0)==1 and DEV_PWR_CMD_M==0:
        logger.debug('Power Controlling: 3G modem: powering off')
        DEV_PWR_STATE &= ~(1<<0)
        pycom.rgbled(0x000000)

    time.sleep(1)
    # print('count = {}'.format(count))
    # count += 1

# import shmGPSclock
# import shmBLE
# import time
# import machine
# from machine import WDT
#
#
# # TEST
# rtc = machine.RTC()

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


#
#
# wdt = WDT(timeout=1000000)  # enable it with a timeout of 2 seconds
#
# from network import WLAN
# wlan = WLAN(mode=WLAN.AP, ssid='gpy-wifi', auth=(WLAN.WPA2,'1234567890'), channel=6, antenna=WLAN.INT_ANT)
#
#
# # Thread function to update RTC
# def updateRTC():
#     now = ((shmGPSclock.my_gps.date[2]+2000,       # yr
#             shmGPSclock.my_gps.date[1],            # Month
#             shmGPSclock.my_gps.date[0],            # day
#             shmGPSclock.my_gps.timestamp[0],       # Hr
#             shmGPSclock.my_gps.timestamp[1],       # Min
#             int(shmGPSclock.my_gps.timestamp[2]))) # Sec
#     print(' [GPSclock] GPS time fixed. Updating RTC...')
#     print(' [GPSclock] ',end='')
#     print(now)
#     rtc.init(now)
#     print(rtc.now())
#
# # THE MAIN LOOP
# count = 0
# while (True):
#     wdt.feed()
#     count += 1
#
#     # GPS Parsing
#     shmGPSclock.L76micropyGPS.gpsParsing()
#
#     # SHOW INFO FROM GPS
#     print("{:4} {:} {:3} {:3} {} {:} {:3} {}".format(
#         count,shmGPSclock.my_gps.parsed_sentences,
#         shmGPSclock.my_gps.fix_type,
#         shmGPSclock.my_gps.satellites_in_use,
#         shmGPSclock.my_gps.date,
#         shmGPSclock.my_gps.timestamp,
#         shmGPSclock.my_gps.hdop,
#         shmGPSclock.gc.mem_free()))
#
#     if shmGPSclock.my_gps.fix_type > 1 and count%4 ==0:
#         # RTC Updating
#         updateRTC()
#         Tnow = rtc.now()
#         # BLE Char Updating
#         shmBLE.chr1_update(Tnow)
#
#     if count%10==0:
#         shmGPSclock.gc.collect()
#         shmBLE.gc.collect()
#
#     time.sleep(0.25)
