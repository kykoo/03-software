import usocket
import _thread
import time
import logging
import errno
import gc
import json
import pycom
from kk_util import *


def service_task(requests):
    global e, pwrLED, acc_threshold, rpi_state
    requests_list = requests.decode('ASCII').split(';')
    responses=b''
    for request in requests_list:
        cmd_args=request.split(',')
        if 'get' in cmd_args[0]:
            if 'icam' in cmd_args[1]:
                responses += (str(iCAM)+';').encode('ASCII')
            elif 'mem' in cmd_args[1]:
                responses += '{:.0f},{:.0f};'.format(mem[0],mem[1])
            elif 'disk' in cmd_args[1]:
                responses += '{:.0f},{:.0f};'.format(disk[0],disk[1])
            elif 'volt' in cmd_args[1]:
                responses += '{:.1f};'.format(volt)
            elif 'switch' in cmd_args[1]:
                responses += (str(switch_setupMode)+';').encode('ASCII')
            elif 'arms' in cmd_args[1]:
                responses += ('{},{:.3f},{},{:.3f},{},{:.3f};'.format(acc_rms[0],acc_rms[1],acc_rms[2],acc_rms[3],acc_rms[4],acc_rms[5])).encode('ASCII')
            elif 'astate' in cmd_args[1]:
                responses += ('{},{},{};'.format(acc_state[0],acc_state[1],acc_state[2])).encode('ASCII')
            elif 'afile' in cmd_args[1]:
                responses += '{},{},{};'.format(acc_file[0],acc_file[1],acc_file[2])
            elif 'state' in cmd_args[1]:
                responses +=  (str(state)+';').encode('ASCII')
            elif 'time' in cmd_args[1]:
                responses += (str(time.time())+';').encode('ASCII')
            elif 'threshold' in cmd_args[1]:
                responses += '{:.1f},{:.1f},{:.1f};'.format(acc_threshold[0],acc_threshold[1], acc_threshold[2])
            elif 'pwrLED' in cmd_args[1]:
                if pwrLED==1:
                    responses += 'on;'
                else:
                    responses += 'off;'

        elif 'set' in cmd_args[0]:
            if 'rpi_state' in cmd_args[1]:
                rpi_state = int(cmd_args[2])
                responses +=  'done;'
            elif 'rms' in cmd_args[1]:
                inode = int(cmd_args[1][3])-1
                acc_rms[2*inode] = cmd_args[2]
                acc_rms[2*inode+1] = float(cmd_args[3])
                responses +=  ('done;').encode('ASCII')
            elif 'file' in cmd_args[1]:
                inode = int(cmd_args[1][4])-1
                acc_file[inode] = cmd_args[2]
                responses +=  ('done;').encode('ASCII')
            elif 'state' in cmd_args[1]:
                inode = int(cmd_args[1][5])
                acc_state[inode-1] = int(cmd_args[2])
                responses +=  ('done;').encode('ASCII')
            elif 'threshold' in cmd_args[1]:
                threshold_1 = float(cmd_args[2])
                threshold_2 = float(cmd_args[3])
                threshold_3 = float(cmd_args[4])
                nvs_set_f('acc_threshold_1',threshold_1)
                nvs_set_f('acc_threshold_2',threshold_2)
                nvs_set_f('acc_threshold_3',threshold_3)
                acc_threshold = [threshold_1, threshold_2, threshold_3]
            elif 'pwrLED' in cmd_args[1]:
                if 'on' in cmd_args[2]:
                    pwrLED = 1
                elif 'off' in cmd_args[2]:
                    pwrLED = 0

    return responses

def client_handling(clientsocket):
    logger.info('client_handling:------------------------')
    clientsocket.settimeout(10)
    while True:
        # Receive from the client
        try:
            r = clientsocket.recv(128)
            logger.info('client_handling: 1. data received.')
        except usocket.error as exc:
            if exc.args[0] == errno.ECONNRESET:
                logger.debug('client_handling: ECONNRESET')
            else:
                logger.debug('client_handling: error code "{}"...'.format(exc.args[0]))
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

def accept():
    # global thread_id
    # thread_id_lock.acquire()
    # thread_id = _thread.get_ident()
    # thread_id_lock.release()


    # try:
    # Accept the connection of the clients
    # logger.info('Client accepting started... mem_free={}'.format(gc.mem_free()))
    # logger.info('Client accepting started...')
    try:
        (clientsocket, address) = serversocket.accept()
        logger.info('Client accpeted...')
        # Start a new thread to handle the client
        logger.info('handling client ...')
        # _thread.start_new_thread(client_handling, (clientsocket, ))
        client_handling(clientsocket)
        logger.info(' handling clinet done.')
    except usocket.error as exc:
        if exc.args[0] == errno.EAGAIN:
            # logger.info('No client access attempts.')
            pass
        else:
            logger.info('****************************************')
            logger.info('error code "{}"...'.format(exc.args[0]))
            logger.info('****************************************')
            # raise
    except:
        logger.exception('*Unhandled in accept_thread**************')
    # gc.collect()
    return


# gc.enable()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# VARIABLE DEFINITION
state = 0
switch_setupMode = None
acc_state = [0,0,0] # 0=startup, 1=getting data, 2=measuring, 3=reporting, 4=sending file, 5=sleep
acc_rms = ['',0.0,'',0.0,'',0.0]
acc_file = [None,None,None]
rpi_state = 0       # 0=startup, 1=getting data, 2=recording/daily-report, 3=reporting, 4=sleep
var_lock = _thread.allocate_lock()
serversocket = None
mem = [0,0]
disk = [0,0]
volt = 0
pwrLED = 0

# LOADING SYSTEM VARIABLES
iCAM = pycom.nvs_get('iCAM')   # pycom.nvs_set('iCAM',1)
acc_threshold = [   nvs_get_f('acc_threshold_1'),
                    nvs_get_f('acc_threshold_2'),
                    nvs_get_f('acc_threshold_3')]
# Set up server socket
def setup():
    global serversocket
    logger.debug('Server Socket Configuration...')
    serversocket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    serversocket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
    serversocket.bind(("", 6543))
    serversocket.listen(10) # Accept maximum of 5 connections at the same time
    serversocket.settimeout(1)
    # logger.debug('Setting up server socket done...')
    # logger.debug('gc mem_alloc/free = {}/{}...'.format(gc.mem_alloc(),gc.mem_free()))
