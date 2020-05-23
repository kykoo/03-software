import usocket
import _thread
import time
import logging
import errno

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

d = 0
e = 0
d_lock = _thread.allocate_lock()
e_lock = _thread.allocate_lock()

def server(requests):
    global e
    requests_list = requests.decode('ASCII').split(';')
    responses=b''
    for request in requests_list:
        cmd_args=request.split(',')
        if 'get' in cmd_args[0]:
            if 'd' in cmd_args[1]:
                d_lock.acquire()
                responses +=  (str(d)+';').encode('ASCII')
                d_lock.release()
        elif 'set' in cmd_args[0]:
            if 'e' in cmd_args[1]:
                e_lock.acquire()
                e = int(cmd_args[2])
                e_lock.release()
                responses +=  ('done;').encode('ASCII')
    logger.debug('responses={}...'.format(responses))
    return responses


# Thread for handling a client
def client_handling(clientsocket,n):
    while True:
        # Receive maxium of 12 bytes from the client
        logger.debug('receiving data...')
        try:
            r = clientsocket.recv(64)
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
            # Serving the client request
            logger.debug('serving requests...')
            responses=server(r)
            logger.debug('serving requests done...')
            # Sends back some data
            logger.debug('sending data...')
            clientsocket.send(responses)
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
        client_handling(clientsocket,c)
        logger.debug('starting_new_thread done ...')
        logger.debug('accept_thread ...')
        c = c+1
        # except:
        #     logger.debug('Error occurred 1...')
        #     logger.exception('Error occurred 2...')


# 2020-04-03 Get/Set version
#   What exactly is bytes?
#   a byte = 8 bits, bytes is a sequence of binary data, machine readable
#   whereas string is human readable
#   OK, now fine. server echo's client's request
#
#   Done smoothly


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
