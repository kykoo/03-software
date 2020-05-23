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
        l = p.poll(10000)
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
                    logger.exception('sock.send(request); request={}'.format(requests))
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
    s.setblocking(False)
    s.settimeout(10)
    p = uselect.poll()
    p.register(s, uselect.POLLIN | uselect.POLLOUT | uselect.POLLHUP | uselect.POLLERR)

    iter = 0
    while iter < 3:
        try:
            s.connect(socket.getaddrinfo(CTLR_IPADDRESS, 6543)[0][-1])
            logger.info('Connection successful.')
            break
        except OSError as exc:
            logger.debug('*************************************************')
            logger.exception('retry request to ctlr, current_iter={}, OSError code={}'.format(iter,exc.args[0]))
            logger.debug('*************************************************')
            time.sleep(5)
            iter += 1
            continue
        except:
            logger.debug('*************************************************')
            logger.exception('retry request to ctlr, current_iter={}, non-OSError')
            logger.debug('*************************************************')
            time.sleep(5)
            iter += 1
            continue
    if iter ==3:
        logger.debug('**********failed in the end****************')
        return

    response = None
    try:
        response = s_handler(p,requests)
        logger.debug('request: finished. response={}'.format(response))
    except:
        logger.exception('Unexpected error')
    return response
