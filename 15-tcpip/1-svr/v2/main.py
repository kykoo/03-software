import usocket
import _thread
import time
import logging


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
    # Receive maxium of 12 bytes from the client
    logger.debug('receiving data...')
    r = clientsocket.recv(12)
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
    clientsocket.send(str(n))
    logger.debug('sending data done...')
    # Close the socket and terminate the thread
    logger.debug('closing clientsocket...')
    clientsocket.close()
    logger.debug('closing clientsocket done...')

# Set up server socket
logger.debug('Setting up server socket...')
serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
serversocket.bind(("192.168.1.51", 6543))
# Accept maximum of 5 connections at the same time
serversocket.listen(1)
logger.debug('Setting up server socket done...')

# Unique data to send back
c = 0
while True:

    # Accept the connection of the clients
    logger.debug('starting to accept...')
    (clientsocket, address) = serversocket.accept()
    logger.debug('starting to accept done...')
    # Start a new thread to handle the client
    logger.debug('starting_new_thread ...')
    #_thread.start_new_thread(client_thread, (clientsocket, ))
    client_thread(clientsocket,c)
    logger.debug('starting_new_thread done ...')
    c = c+1
