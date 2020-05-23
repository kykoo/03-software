from network import Bluetooth
import time
import machine
import gc
import _thread
# import utime


gc.enable()

lastclientAccessTime = 0
isClientConnected = False

def uuid2bytes(uuid):
    import ubinascii
    uuid = uuid.encode().replace(b'-',b'')
    tmp = ubinascii.unhexlify(uuid)
    return bytes(reversed(tmp))


char1_read_counter = 0
char2_read_counter = 0

def conn_cb (bt_o):
    # import utime
    global clientAccessTime, isClientConnected

    events = bt_o.events()
    if  events & Bluetooth.CLIENT_CONNECTED:
        print(" [BLE] Client connected")
        isClientConnected = True
        lastclientAccessTime = time.time()

    elif events & Bluetooth.CLIENT_DISCONNECTED:
        print(" [BLE] Client disconnected")
        isClientConnected = False



# def char2_cb_handler(chr):
#     global char2_read_counter
#     char2_read_counter += 1
#     if char2_read_counter > 0xF1:
#         return char2_read_counter

def char1_cb_handler(chr):
    global char1_read_counter
    char1_read_counter += 1

    events = chr.events()
    if  events & Bluetooth.CHAR_WRITE_EVENT:
        print("Write request with value = {}".format(chr.value()))
    else:
        if True:
        #if char1_read_counter < 3:
            print('Read request on char 1')
        else:
            return 'ABC DEF'

def char2_cb_handler(chr):
    global char2_read_counter
    char2_read_counter += 1

    events = chr.events()
    if  events & Bluetooth.CHAR_WRITE_EVENT:
        print("Write request with value = {}".format(chr.value()))
        bluetooth.disconnect_client()
    elif events & Bluetooth.CHAR_READ_EVENT:
        if True:
        #if char1_read_counter < 3:
            print('Read request on char 2')
        else:
            return 'ABC DEF'

#
# mkfifo ~/myfifo
# while sleep 1; do socat /dev/ttyACM1,b115200,echo=0,raw ~/myfifo; done &
# minicom -o -D ~/myfifo

bluetooth = Bluetooth()
bluetooth.set_advertisement(name='gpy4gcam', service_uuid=uuid2bytes('d9293538-3087-11ea-aec2-2e728ce88125'))
bluetooth.callback(trigger=Bluetooth.CLIENT_CONNECTED | Bluetooth.CLIENT_DISCONNECTED, handler=conn_cb)
bluetooth.advertise(True)
# srv1 = bluetooth.service(uuid=uuid2bytes('d9293538-3087-11ea-aec2-2e728ce88125'), isprimary=True, nbr_chars=2)
srv1 = bluetooth.service(uuid=0xAA1, isprimary=True, nbr_chars=2)
cv = '2020-01-01 00:00:00'
chr1 = srv1.characteristic(uuid=0xaaa1, value=cv)
chr2 = srv1.characteristic(uuid=0xaaa2, value=9)
char1_cb = chr1.callback(trigger=Bluetooth.CHAR_WRITE_EVENT | Bluetooth.CHAR_READ_EVENT, handler=char1_cb_handler)
char2_cb = chr2.callback(trigger=Bluetooth.CHAR_WRITE_EVENT | Bluetooth.CHAR_READ_EVENT, handler=char2_cb_handler)

# srv1.start()

def chr1_update(Now):
# rtc = machine.RTC()
# Now = rtc.now()
    strDateTime = '{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(Now[0]+1,Now[1],Now[2],Now[3],Now[4],Now[5])
    # srv1.stop()
    # chr1 = srv1.characteristic(uuid=2, value=strDateTime)
    # char1_cb = chr1.callback(trigger=Bluetooth.CHAR_WRITE_EVENT | Bluetooth.CHAR_READ_EVENT, handler=char1_cb_handler)
    # srv1.start()
    # print("chr1_update done.")
    try:
        chr1.value(strDateTime)
    except:
        pass


def removeIdleClient():
    # import utime
    global isClientConnected
    while True:
        if isClientConnected and time.time()-lastclientAccessTime > 20:
        # if time.time()-lastclientAccessTime > 20:
            isClientConnected = False
            bluetooth.disconnect_client()
            print('idle client removed')
        time.sleep(2)

# _thread.start_new_thread(removeIdleClient,())
