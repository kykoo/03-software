import socket
import time
import uerrno
import uselect
import pycom
import logging
from machine import WDT

CTLR_IPADDRESS = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def s_handler(p, requests):

    returnFlag = False
    while not returnFlag:
        logger.debug('s_handler: 1. starting polling...')
        l = p.poll(5000)
        if len(l) ==0:
            logger.debug('s_handler: polling timeout, returning...')
            returnFlag = True
        for t in l:
            sock = t[0]
            event = t[1]
            if(event & uselect.POLLERR or event & uselect.POLLHUP):
                logger.debug('s_handler: pollerr or pollup')
                sock.close()
                returnFlag = True
                continue
            if(event & uselect.POLLOUT):
                try:
                    sock.send(requests)
                    p.modify(sock, uselect.POLLIN | uselect.POLLHUP | uselect.POLLERR)
                    logger.debug('s_handler: 2. sending data done...')
                    # continue
                except:
                    raise
            if(event & uselect.POLLIN):
                try:
                    logger.debug('s_handler: 3. receiving data...')
                    r = sock.recv(64)
                    # If recv() returns with 0 the other end closed the connection
                    if len(r) == 0:
                        sock.close()
                        logger.debug('s_handler: len(r)=0, sock.close()')
                        returnFlag = True
                        continue
                    else:
                        sock.close()
                        logger.debug("s_handler: 4. Data received: {}. sock closed.".format(str(r)))
                        returnFlag = True
                        return r.decode('ASCII')
                except:
                    logger.exception('s_handler: receiving and handling data failed.')

    return

def request(requests):
    s = socket.socket()
    s.setblocking(True)
    p = uselect.poll()
    p.register(s, uselect.POLLIN | uselect.POLLOUT | uselect.POLLHUP | uselect.POLLERR)

    try:
        wdt = WDT(timeout=10*1000)
        s.settimeout(1.0)
        s.connect(socket.getaddrinfo(CTLR_IPADDRESS, 6543)[0][-1])
        logger.info('request: connected to the server...')
        wdt.feed()
        wdt.init(5*60*1000)
        response = s_handler(p,requests)
        logger.debug('request: finished. response={}'.format(response))
        return response
    except socket.timeout:
        logger.debug('request: Timeout error occurred...')
    except:
        raise
    return
