
# ACC SENSOR CONFIGURATION CONSTANTS

# FULL_SCALE_2G = const(0)
# FULL_SCALE_4G = const(2)
# FULL_SCALE_8G = const(3)
#
# ODR_POWER_DOWN = const(0)
# ODR_10_HZ = const(1)
# ODR_50_HZ = const(2)
# ODR_100_HZ = const(3)
# ODR_200_HZ = const(4)
# ODR_400_HZ = const(5)
# ODR_800_HZ = const(6)

from pysense import Pysense
import LIS2HH12
import array
from machine import Pin
import time
import logging
import gc


gc.enable()

logger = logging.getLogger(__name__)
wdt = ''
gc = ''
acc = ''
py = Pysense()
Fs = 100

def avg(U):
    Usum = 0.0
    count = 0
    for u in U:
        Usum += u
        count += 1
    Uavg = Usum/count
    return Uavg

def rms(U):
    Ussum = 0.0
    count  = 0
    Uavg = avg(U)
    for u in U:
        Ussum += (u-Uavg)**2.0
        count += 1
    Urms = (Ussum/count)**0.5
    return Urms

def setup(watchdogTimer=None):
    global acc, Fs, wdt

    # wdt = watchdogTimer

    # LISHH12 SETUP
    acc = LIS2HH12.LIS2HH12()
    acc.set_full_scale(LIS2HH12.FULL_SCALE_2G) #  +/- 2G, the smallest one
    acc.set_odr(LIS2HH12.ODR_100_HZ)           #  100 Hz
    Fs = 100
    logger.debug("setup LIS2HH12 Done.")
    # acc.set_register(LISHH12.CTRL4_REG, 3, 6, 3) # LPF 50 Hz, BW[2:1]=11

def measure(x,Td=60):

    for j in range(Fs*Td):
        while not acc.new_data_available():
            time.sleep_us(10)
        x_ = acc.acceleration()
        for i in range(3):
            x[i][j] = x_[i]

    return  

    # # Td in seconds
    # # logger.debug("start to measure...")
    #
    # X = array.array('f')
    # Y = array.array('f')
    # Z = array.array('f')
    #
    # for i in range(Fs*Td):
    #     while not acc.new_data_available():
    #         time.sleep_us(10)
    #     acc_ = acc.acceleration()
    #     # logger.debug("{:8.5f}, {:8.5f}, {:8.5f}".format(acc_[0], acc_[1], acc_[2]))
    #     X.append(acc_[0])
    #     Y.append(acc_[1])
    #     Z.append(acc_[2])
    #     # if i%Fs == 0:
    #     #     wdt.feed()
    #
    # Xrms = rms(X)
    # Yrms = rms(Y)
    # Zrms = rms(Z)
    # Xavg = avg(X)
    # Yavg = avg(Y)
    # Zavg = avg(Z)
    # # logger.info('Avg(X,Y,Z)=(%f,%f,%f)',avg(X),avg(Y),avg(Z))
    # # logger.info('RMS(X,Y,Z)=(%f,%f,%f)',Xrms,Yrms,Zrms)
    # # logger.debug("start to measure Done.")
    # return X, Y, Z, Xrms, Yrms, Zrms, Xavg, Yavg, Zavg
