import machine
import time
from machine import ADC

adc = machine.ADC()
# adc_c = adc.channel(pin='P19', attn=ADC.ATTN_11DB)
adc_c = adc.channel(pin='P18', attn=ADC.ATTN_11DB)
adc_c()

# Output Vref of P22
# adc.vref_to_pin('P22')
# while True:
#     time.sleep(1)



# Set calibration - see note above
adc.vref(1100)

while True:
    adc_c()
    print(adc_c.voltage())
    time.sleep(1)
#
# while True:
#   val = adc_pin.voltage()
#   print(val)
#   # print(adc_pin.value_to_voltage(val))
#   time.sleep(1)
