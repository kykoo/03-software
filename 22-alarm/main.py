from machine import Timer
import time

def _handler(alarm):
    print(time.time())


# a=Timer.Alarm(_handler,3600*24,periodic=True)

print('Timer.Alarm Tester...')
print(time.time())
a=Timer.Alarm(_handler,10,periodic=True)
