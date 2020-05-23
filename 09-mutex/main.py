import _thread
import time
import moduleA

# def th_func(case,j):
#     if case == 1:
#         while True:
#             for i in range(50):
#                 print('a', end='')
#                 time.sleep_ms(1)
#             # time.sleep_ms(10)
#     if case == 2:
#         while True:
#             for i in range(50):
#                 print('b', end='')
#                 time.sleep_ms(1)
#             # time.sleep_ms(10)
#     if case == 3:
#         while True:
#             for i in range(50):
#                 print('c', end='')
#                 time.sleep_ms(1)
#             # time.sleep_ms(10)
# for i in range(1,4):
#     _thread.start_new_thread(th_func,(i,2))

lock = _thread.allocate_lock()
module_lock =_thread.allocate_lock()
moduleA.module_lock = module_lock

_thread.start_new_thread(moduleA.func_module,())

def th_func(case):
    global lock
    if case == 1:
        while True:
            lock.acquire()
            moduleA.module_lock.acquire()
            for i in range(50):
                print('a', end='')
                time.sleep_ms(1)
            moduleA.module_lock.release()
            lock.release()
            # time.sleep_ms(10)
    if case == 2:
        while True:
            lock.acquire()
            moduleA.module_lock.acquire()
            for i in range(50):
                print('b', end='')
                time.sleep_ms(1)
            moduleA.module_lock.release()
            lock.release()
            # time.sleep_ms(10)
    if case == 3:
        while True:
            lock.acquire()
            moduleA.module_lock.acquire()
            for i in range(50):
                print('c', end='')
                time.sleep_ms(1)
            moduleA.module_lock.release()
            lock.release()
            # time.sleep_ms(10)
for i in range(1,4):
    _thread.start_new_thread(th_func,(i,))

while True:
    time.sleep(2)
