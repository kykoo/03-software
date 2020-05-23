import time
import logging
import _thread
import socket_svr

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

_thread.start_new_thread(socket_svr.accept_thread,())
d=0
e=0
while True:
    logger.debug('main loop: {} {}'.format(d,e))
    time.sleep(1)
    d += 1
    socket_svr.d_lock.acquire()
    socket_svr.d = d
    socket_svr.d_lock.release()
    socket_svr.e_lock.acquire()
    e = socket_svr.e
    socket_svr.e_lock.release()
