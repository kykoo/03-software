import time
import os
import uerrno
import pycom
import struct

def datetime_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}-{:0>2d}{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2],t_[3],t_[4],t_[5])

def date_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2])

def mkdir(path):
    try:
        cwd = os.getcwd()
        os.chdir(path)
        os.chdir(cwd)
        return False
    except OSError as exc:
        if exc.args[0] == uerrno.ENOENT:
            os.mkdir(path)
            return False
        else:
            raise
    except:
        raise

def getNextGridTime(T_now,T_exec):
    res = T_now%T_exec
    if res != 0:
        T_start = T_now - res + T_exec
    else:
        T_start = T_now
    return T_start

def waitUntil(T_start):
    while True:
        if time.time() >= T_start:
            break
    return

def nvs_get_f(varName):
    # value_bytes = pycom.nvs_get(varName)
    # return struct.unpack('f',value_bytes)[0]
    value_int = pycom.nvs_get(varName)
    value = float(value_int)/100.0
    return value


def nvs_set_f(varName,value):
    # value_bytes = struct.pack('f',value)
    # pycom.nvs_set(varName,value_bytes)
    value_int = int(value*100)
    pycom.nvs_set(varName,value_int)
    return

def disk_status():
    flash_used = 100-os.getfree('/flash')/(4*1024)*100 # in (%)
    sd_used = 100-os.getfree('/sd')/(32*1024*1024)*100 # in (%)
    return [int(flash_used), int(sd_used)]
