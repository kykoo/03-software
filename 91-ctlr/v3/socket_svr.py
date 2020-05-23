import usocket
import _thread
import time
import logging
import errno
import gc
import json
import pycom


def service_task(requests):
    global e
    requests_list = requests.decode('ASCII').split(';')
    responses=b''
    for request in requests_list:
        cmd_args=request.split(',')
        if 'get' in cmd_args[0]:
            var_lock.acquire()
            if 'state' in cmd_args[1]:
                responses +=  (str(state)+';').encode('ASCII')
            elif 'time' in cmd_args[1]:
                responses += (str(time.time())+';').encode('ASCII')
            elif 'icam' in cmd_args[1]:
                responses += (str(iCAM)+';').encode('ASCII')
            var_lock.release()
        elif 'set' in cmd_args[0]:
            var_lock.acquire()
            if 'rms' in cmd_args[1]:
                inode = int(cmd_args[1][3])
                acc_rms[inode-1] = float(cmd_args[2])
                responses +=  ('done;').encode('ASCII')
            elif 'state' in cmd_args[1]:
                inode = int(cmd_args[1][5])
                acc_state[inode-1] = int(cmd_args[2])
                responses +=  ('done;').encode('ASCII')
            var_lock.release()

    return responses

def client_handling(clientsocket):
    logger.info('client_handling:------------------------')
    while True:
        # Receive maxium of 12 bytes from the client
        try:
            r = clientsocket.recv(64)
            logger.info('client_handling: 1. data received.')
        except usocket.error as exc:
            if exc.args[0] == errno.ECONNRESET:
                logger.debug('client_handling: ECONNRESET')
            else:
                logger.debug('client_handling: error code {}...'.format(exc.args[0]))
                raise
            logger.debug('client_handling: clientsocket.close()...')
            clientsocket.close()
            logger.debug('client_handling: returning...')
            return
        except:
            logger.exception('client_handling: unhandled in client_handling*********************')
        time.sleep(0.1)

        # If recv() returns with 0 the other end closed the connection
        if len(r) == 0:
            clientsocket.close()
            logger.debug('client_handling: 5. leng(r)=0, socket closed. finished.')
            return
        else:
            # Do something wth the received data...
            logger.debug("client_handling: 2. Received data={}".format(str(r)))
            # Serving the client request
            responses=service_task(r)
            logger.debug('client_handling: 3. requests served. response={}.'.format(responses))
            # Sends back some data
            clientsocket.send(responses)
            logger.debug('client_handling: 4. response sent.')

def accept_thread():
    global thread_id
    thread_id_lock.acquire()
    thread_id = _thread.get_ident()
    thread_id_lock.release()

    while True:
        # try:
        # Accept the connection of the clients
        # logger.info('Client accepting started... mem_free={}'.format(gc.mem_free()))
        logger.info('Client accepting started...')
        try:
            (clientsocket, address) = serversocket.accept()
            logger.info('Client accpeted...')
            # Start a new thread to handle the client
            logger.info('new thread for handling client starting...')
            # _thread.start_new_thread(client_handling, (clientsocket, ))
            client_handling(clientsocket)
            logger.info(' handling clinet done.')
        except usocket.error as exc:
            if exc.args[0] == errno.EAGAIN:
                logger.info('No client access attempts.')
                continue
            else:
                logger.info('****************************************')
                logger.info('error code {}...'.format(exc.args[0]))
                logger.info('****************************************')
                # raise
        except:
            logger.exception('*Unhandled in accept_thread**************')
        # gc.collect()


# gc.enable()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# VARIABLE DEFINITION
state = 0
switch_setupMode = False
acc_state = [0,0,0] # 0=startup, 1=getting data, 2=measuring, 3=reporting, 4=sending file, 5=sleep
acc_rms = [0.0,0.0,0.0]
acc_last_timestamp = [None,None,None]
rpi_state = 0       # 0=startup, 1=getting data, 2=recording/daily-report, 3=reporting, 4=sleep
var_lock = _thread.allocate_lock()
serversocket = None

thread_id = None
thread_id_lock = _thread.allocate_lock()

# LOADING SYSTEM VARIABLES
iCAM = pycom.nvs_get('iCAM')   # pycom.nvs_set('iCAM',1)

# LOADING CONFIG.JSON
with open('/flash/config.json','r') as file:
    config = json.load(file)
acc_threshold = config['acc_threshold']
logger.debug('acc_threshold = {}'.format(acc_threshold))

# Set up server socket
def setup():
    global serversocket
    logger.debug('Server Socket Configuration...')
    serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
    serversocket.bind(("", 6543))
    serversocket.listen(10) # Accept maximum of 5 connections at the same time
    serversocket.settimeout(10)
    # logger.debug('Setting up server socket done...')
    # logger.debug('gc mem_alloc/free = {}/{}...'.format(gc.mem_alloc(),gc.mem_free()))
