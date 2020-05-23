import array
import ustruct
from machine import SD
import os


sd = SD()
os.mount(sd,'/sd')

acc = array.array('f',[0,1,3])
filename = '/sd/test-write'
with open(filename,'wb') as file:
    file.write(ustruct.pack('<fff',acc[0],acc[1],acc[2]))
