import socket
import _thread
import time
import uerrno
import uselect
import pycom
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def socket_thread(p, requests):

    returnFlag = False
    cursor = 0
    while True:
        logger.debug('starting polling...')
        l = p.poll(5000)
        logger.debug('starting polling done...')
        if len(l) ==0:
            logger.debug('polling timeout, returning...')
            returnFlag = True
        for t in l:
            sock = t[0]
            event = t[1]
            if(event & uselect.POLLERR or event & uselect.POLLHUP):
                logger.debug('pollerr or pollup')
                sock.close()
                returnFlag = True
                continue
            if(event & uselect.POLLOUT):
                try:
                    if cursor ==0:
                        logger.debug('sending data...')
                        sock.send(requests)
                        # We only want to send one message on this socket, in the future wait only for new incoming messages
                        p.modify(sock, uselect.POLLIN | uselect.POLLHUP | uselect.POLLERR)
                        logger.debug('sending data done...')
                        cursor += 1
                        continue
                    else:
                        pass
                except:
                    raise
                    # pass
            if(event & uselect.POLLIN):
                try:
                    logger.debug('receiving data...')
                    r = sock.recv(64)
                    logger.debug('receiving data done...')
                    # If recv() returns with 0 the other end closed the connection
                    if len(r) == 0:
                        sock.close()
                        logger.debug('len(r)=0, sock.close()')
                        returnFlag = True
                        continue
                    else:
                        # Do something with the received data...
                        logger.debug("Data received: " + str(r))
                        logger.debug("sock.close() ...")
                        sock.close()
                        logger.debug("sock.close() done ...")
                        returnFlag = True
                except:
                    pass
        if returnFlag is True:
            break
    return



def request(requests):
    logger.debug('setting up socket...')
    # List for storing our sockets
    socket_list = []

    # Set up the first socket in non-blocking mode
    s1 = socket.socket()
    s1.setblocking(True)
    s1.settimeout(3.0)
    # s1.setblocking(False)
    socket_list.append(s1)
    # # Set up the second socket in non-blocking mode
    # s2 = socket.socket()
    # s2.setblocking(False)
    # socket_list.append(s2)

    # Create a new poll object
    p = uselect.poll()
    # Register the sockets into the poll object, wait for all kind of events
    p.register(s1, uselect.POLLIN | uselect.POLLOUT | uselect.POLLHUP | uselect.POLLERR)
    # p.register(s2, uselect.POLLIN | uselect.POLLOUT | uselect.POLLHUP | uselect.POLLERR)
    logger.debug('setting up socket done...')

    for s in socket_list:
        try:
            logger.debug('connecting to the server...')
            out = s.connect(socket.getaddrinfo("192.168.1.51", 6543)[0][-1])
            logger.debug(out)
            logger.debug('connecting to the server done...')
            logger.debug('starting socket_thread...')
            socket_thread(p,requests)
            logger.debug('starting socket_thread done...')
        except socket.timeout:
            logger.debug('Timeout error occurred...')
        except:
            raise
    time.sleep(3)
