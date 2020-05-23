import _thread
import time

# case 1
# module_lock = _thread.allocate_lock()
module_lock = []


def func_module():
    global module_lock
    while True:
        module_lock.acquire()
        for i in range(50):
            print('m', end='')
            time.sleep_ms(1)
        module_lock.release()
        time.sleep_ms(10)

# case 1
# _thread.start_new_thread(func_module,())
