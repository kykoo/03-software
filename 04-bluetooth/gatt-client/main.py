from network import Bluetooth
import machine
import time
from pytrack import Pytrack

py = Pytrack()

bt = Bluetooth()
bt.start_scan(-1)

count=0
no_adv_count = 0
while True:
  adv = bt.get_adv()
  count += 1
  if adv and bt.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL) == 'gpy':
  #if adv:
      print("{}: AVD FOUND and {}".format(count,bt.resolve_adv_data(adv.data, Bluetooth.ADV_NAME_CMPL)))
      try:
          conn = bt.connect(adv.mac)
          services = conn.services()
          for service in services:
              time.sleep(0.050)
              if type(service.uuid()) == bytes:
                  print('Reading chars from service = {}'.format(service.uuid()))
              else:
                  print('Reading chars from service = %x' % service.uuid())
              chars = service.characteristics()
              for char in chars:
                  if (char.properties() & Bluetooth.PROP_READ):
                      print('char {} value = {}'.format(char.uuid(), char.read()))
          conn.disconnect()
          #break
      except:
          pass
  else:
      print("{}-{}: adv not found".format(count,no_adv_count))
      no_adv_count += 1
      if no_adv_count > 5:
          # bt.stop_scan()
          # time.sleep(1)
          # bt.start_scan(-1)
          # machine.reset()
          # bt.start_scan(-1)
          # no_adv_count = 0
          print("py.go_to_sleep()")
          py.setup_sleep(3)
          py.go_to_sleep()
  time.sleep(1)
