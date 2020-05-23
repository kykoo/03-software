import time
import pycom
import logging
import socket_client

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

c = 0
while True:
    requests = 'get,state;set,rms1,'+str(2*float(c)+1.0)
    logger.debug('socket_client.request  {}...'.format(requests))
    socket_client.request(requests)
    logger.debug('socket_client.request done...')
    logger.debug('mainloop: c = {}...'.format(c))
    time.sleep(1)
    c += 1

# Packaging socket_client 2020-0403
#   Done smoothly
