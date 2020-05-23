from network import Bluetooth
import time


def conn_cb (bt_o):
    events = bt_o.events()
    if  events & Bluetooth.CLIENT_CONNECTED:
        print("Client connected")
    elif events & Bluetooth.CLIENT_DISCONNECTED:
        print("Client disconnected")


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
        if char1_read_counter < 3:
            print('Read request on char 1')
        else:
            return 'ABC DEF'

bluetooth = Bluetooth()
bluetooth.set_advertisement(name='gpy', service_uuid=b'1234567890123456')
bluetooth.callback(trigger=Bluetooth.CLIENT_CONNECTED | Bluetooth.CLIENT_DISCONNECTED, handler=conn_cb)
bluetooth.advertise(True)

srv1 = bluetooth.service(uuid=b'1234567890123456', isprimary=True)
chr1 = srv1.characteristic(uuid=b'ab34567890123456', value=5)
char1_read_counter = 0
char1_cb = chr1.callback(trigger=Bluetooth.CHAR_WRITE_EVENT | Bluetooth.CHAR_READ_EVENT, handler=char1_cb_handler)
# srv1.start()


# srv2 = bluetooth.service(uuid=1234, isprimary=True)
# chr2 = srv2.characteristic(uuid=4567, value=0x1234)
# char2_read_counter = 0xF0
# char2_cb = chr2.callback(trigger=Bluetooth.CHAR_READ_EVENT, handler=char2_cb_handler)

# count = 0
# while True:
#     print("{}: sleep".format(count))
#     count += 1
#     time.sleep(2)
#     # bluetooth.advertise(True)
