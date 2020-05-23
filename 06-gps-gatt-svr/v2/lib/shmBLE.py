from network import Bluetooth
import time
import machine
# import _thread


char1_read_counter = 0

def conn_cb (bt_o):
    events = bt_o.events()
    if  events & Bluetooth.CLIENT_CONNECTED:
        print(" [BLE] Client connected")
    elif events & Bluetooth.CLIENT_DISCONNECTED:
        print(" [BLE] Client disconnected")


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



bluetooth = Bluetooth()
bluetooth.set_advertisement(name='gpy4gcam', service_uuid=1)
bluetooth.callback(trigger=Bluetooth.CLIENT_CONNECTED | Bluetooth.CLIENT_DISCONNECTED, handler=conn_cb)
bluetooth.advertise(True)

srv1 = bluetooth.service(uuid=1, isprimary=True, start=False)
cv = '2020-01-01 00:00:00'
chr1 = srv1.characteristic(uuid=2, value=cv)
char1_cb = chr1.callback(trigger=Bluetooth.CHAR_WRITE_EVENT | Bluetooth.CHAR_READ_EVENT, handler=char1_cb_handler)
srv1.start()

def chr1_update(Now):
# rtc = machine.RTC()
# Now = rtc.now()
    strDateTime = '{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(Now[0]+1,Now[1],Now[2],Now[3],Now[4],Now[5])
    # srv1.stop()
    # chr1 = srv1.characteristic(uuid=2, value=strDateTime)
    # char1_cb = chr1.callback(trigger=Bluetooth.CHAR_WRITE_EVENT | Bluetooth.CHAR_READ_EVENT, handler=char1_cb_handler)
    # srv1.start()
    # print("chr1_update done.")
    chr1.value(strDateTime)



# cv = '2020 0102 00:00:00'
# chr1.value(cv)

# chr1 = srv1.characteristic(uuid=2, value='2020 0102 00:00:00')
# char1_cb = chr1.callback(trigger=Bluetooth.CHAR_WRITE_EVENT | Bluetooth.CHAR_READ_EVENT, handler=char1_cb_handler)
# srv1.start()

# srv1 = bluetooth.service(uuid=1, isprimary=True, start=False)
# chr1 = srv1.characteristic(uuid=2, value='2020 0101 00:00:00')
# char1_cb = chr1.callback(trigger=Bluetooth.CHAR_WRITE_EVENT | Bluetooth.CHAR_READ_EVENT, handler=char1_cb_handler)
# srv1.start()

# bluetooth.advertise(False)
# srv1.stop()
# chr1.value(strDateTime)
# srv1.start()
# bluetooth.advertise(True)

# bluetooth.advertise(False)
# srv1.stop()
# chr1.value(strDateTime)
# srv1.start()
# bluetooth.advertise(False)

# chr1 = srv1.characteristic(uuid=2, value=strDateTime)
# char1_cb = chr1.callback(trigger=Bluetooth.CHAR_WRITE_EVENT | Bluetooth.CHAR_READ_EVENT, handler=char1_cb_handler)
