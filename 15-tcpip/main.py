# import dropfile_
#
# out = dropfile_.dropfile('192.168.1.2', 21, '/', 'kykoo', 'asdf9898', '/flash/data_source/usb_modeswitch.conf')
# #out = dropfile_.dropfile('192.168.1.3', 21, '/flash/data', 'micro', 'python', '/flash/data_source/usb_modeswitch.conf')
# print(out)
# print("success")
# # try:
# #     dropfile('192.168.1.3', 21, '/flash/data', 'micro', 'python', '/flash/data_source/usb_modeswitch.conf')
# #     print("success")
# # except E:
# #     print("failed")


# from ftplib import FTP
# ftp = FTP('192.168.1.2')
# ftp.


# import dropfile_
# out = dropfile_.dropfile('192.168.1.2', 21, 'Downloads', 'kykoo', 'asdf9898', '/flash/a.txt')
# print(out)
# print("success")

import dropfile
import os
os.chdir('data')
out = dropfile.dropfile('192.168.1.8', 21, '/flash/data', 'micro', 'python', 'a.txt')
print(out)
print("success") 
