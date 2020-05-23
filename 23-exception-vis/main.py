# import traceback
import sys
import logging
from machine import SD
import os
import _thread
import time


sd = SD()
os.mount(sd,'/sd')

logging.basicConfig(level=logging.DEBUG,filepath='/sd/log.txt')
logger = logging.getLogger(__name__)

def g():
   f1()

def f1():
   raise Exception("hi f1")

def f2():
   raise Exception("hi f2")

def f3():
   raise Exception("hi f3")

try:
   g()
except Exception:
   # track = traceback.format_exc()
   # print(track)
   logger.exception('hello exception!')
   # sys.print_exception(e)

print("---------------------")



def h1():
   f2()

_thread.start_new_thread(h1,())
time.sleep(3)
print("============================")

def h2():
    try:
       f3()
    except Exception:
       # track = traceback.format_exc()
       # print(track)
       logger.exception('hello exception!')
       # sys.print_exception(e)

_thread.start_new_thread(h2,())
time.sleep(3)

print("******************************")


g()
