import usocket
import _thread
import time
import logging
import errno

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("__main__")
# logger.debug("Test message: %d(%s)", 100, "foobar")
# logger.info("Test message2: %d(%s)", 100, "foobar")
# logger.warning("Test message3: %d(%s)")
# logger.error("Test message4")
# logger.critical("Test message5")
# logging.info("Test message6")

# Thread for handling a client
def client_thread(clientsocket,n):
    while True:
        # Receive maxium of 12 bytes from the client
        logger.debug('receiving data...')
        try:
            r = clientsocket.recv(12)
        except usocket.error as exc:
            if exc.args[0] == errno.ECONNRESET:
                logger.debug('receiving data error: ECONNRESET')
            else:
                logger.debug('error code {}...'.format(exc.args[0]))
                raise
            logger.debug('clientsocket.close()...')
            clientsocket.close()
            logger.debug('returning...')
            return
        logger.debug('receiving data done...')
        time.sleep(0.1)

        # If recv() returns with 0 the other end closed the connection
        if len(r) == 0:
            logger.debug('leng(r)=0, closing socket...')
            clientsocket.close()
            logger.debug('leng(r)=0, closing socket done...')
            return
        else:
            # Do something wth the received data...
            logger.debug("Received: {}".format(str(r)))
            # Sends back some data
            logger.debug('sending data...')
            clientsocket.send(str(n) + ' ACK')
            logger.debug('sending data done...')
            # # Close the socket and terminate the thread
            # logger.debug('closing clientsocket...')
            # clientsocket.close()
            # logger.debug('closing clientsocket done...')

# Set up server socket
logger.debug('Setting up server socket...')
serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
serversocket.bind(("192.168.1.51", 6543))
# Accept maximum of 5 connections at the same time
serversocket.listen(3)
serversocket.settimeout(5)
logger.debug('Setting up server socket done...')


def accept_thread():
    # Unique data to send back
    c = 0
    while True:
        # try:
        # Accept the connection of the clients
        logger.debug('starting to accept...')
        try:
            (clientsocket, address) = serversocket.accept()
        except usocket.error as exc:
            if exc.args[0] == errno.EAGAIN:
                logger.debug('OSError Errno 11 EAGAIN... retrying...')
                continue
            else:
                logger.debug('error code {}...'.format(exc.args[0]))
                raise
        # try:
        #     (clientsocket, address) = serversocket.accept()
        # except socket.timeout:
        #     logger.debug('timeout for acceptting... retry...')
        #     continue
        # except:
        #     raise
        logger.debug('starting to accept done...')
        # Start a new thread to handle the client
        logger.debug('starting_new_thread ...')
        #_thread.start_new_thread(client_thread, (clientsocket, ))
        client_thread(clientsocket,c)
        logger.debug('starting_new_thread done ...')
        logger.debug('accept_thread ...')
        c = c+1
        # except:
        #     logger.debug('Error occurred 1...')
        #     logger.exception('Error occurred 2...')

_thread.start_new_thread(accept_thread,())
d=0
while True:
    logger.debug('main loop: {}'.format(d))
    time.sleep(1)
    d += 1

# socket.recv(12) Error What is this?
# The error code unknown

# P1:   Another Error
#       Accept doesn't return for a new connection
#
#       two possibilities:
#           - the thread ended silently which is not likely
#           - accept function is not seeing connections from client
#
# Trial 1:
#       OK, let's try to use timeout for accept (i.e. using socket.settimeout())
#       then, server socket accepting must work nearly always,
#       socket.recv is a non-blocking function. that is not affected.
#       if this fails again, then it may be a problem of the clinet or the svr socket itself
#       However, timeout for accept looks a good approach; it handles unexpected situation for the svr SOL_SOCKET
#
# Trial 2:
#       Ok, I can determine if this is a problem of svr socket or client.
#       Rebooting a problematic side will fix the problem
#
#       I didn't try this somehow; I used an exception handling for ECONNRESET in recv()
#
# Trial 3:
#       OK, Exception handling for ECONNRESET is used for recv()

# OK, Trial 1 and 3 fixed the problem
#
# I even use an exception handling for EAGAIN for accept()
#
# So what I used are
# - socket.settimeout()
# - Handling ECONNRESET exception for clientsocket.recv()
# - Handling EAGAIN exception for socket.accept()
