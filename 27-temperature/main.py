from pysense import Pysense
from SI7006A20 import SI7006A20
import time

py = Pysense()
sensor = SI7006A20(py)


while True:
    time.sleep(1)
    print('temp={}, humidity={}'.format(sensor.temperature(),sensor.humidity()))
