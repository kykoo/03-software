import time

def datetime_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}-{:0>2d}{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2],t_[3],t_[4],t_[5])

def date_string(time_sec):
    t_ = time.localtime(time_sec)
    return '{}-{:0>2d}{:0>2d}'.format(t_[0],t_[1],t_[2])

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
