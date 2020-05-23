import _thread
import gc
import binascii
import time
import logging
import ure

# http://www.gpsinformation.org/dale/nmea.htm#GGA
# https://forum.pycom.io/topic/1626/pytrack-gps-api/12

def attach_crc(cmd_str):
    a = cmd_str[1:]
    crc = 0
    for ch in a:
        crc ^= ord(ch)
    return cmd_str + '*' + '{:X}'.format(crc) +'\r\n'

class L76micropyGPS:

    GPS_I2CADDR = const(0x10)

    def __init__(self, my_gps, pytrack=None, sda='P22', scl='P21'):
        if pytrack is not None:
            self.i2c = pytrack.i2c
        else:
            from machine import I2C
            self.i2c = I2C(0, mode=I2C.MASTER, pins=(sda, scl))

        self.my_gps = my_gps

        self.logger = logging.getLogger(__name__)

        # config GPS hints
        # https://forum.pycom.io/topic/2449/changing-the-gps-frequency-and-configuring-which-nmea-sentences-the-gps-posts/7
        # Stop logging to local flash of GPS
        #self.stoplog = "$PMTK185,1*23\r\n"
        #self.i2c.writeto(GPS_I2CADDR, self.stoplog)
        self.i2c.writeto(GPS_I2CADDR, "$PMTK185,1*23\r\n")
        self.i2c.writeto(GPS_I2CADDR, bytes([0]))
        if 1: # RMC and GGA only
            cmd = attach_crc("$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
            self.i2c.writeto(GPS_I2CADDR, cmd)
            self.i2c.writeto(GPS_I2CADDR, bytes([0]))
        # # Use GPS, GONASS, GALILEO and GALILEO Full satellites
        # self.searchmode = "$PMTK353,1,1,1,0,0*2B\r\n"
        # self.i2c.writeto(GPS_I2CADDR, self.searchmode)
        # self.i2c.writeto(GPS_I2CADDR, bytes([0]))
        # # Only out RMC messages
        # self.rmc = "$PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29\r\n"
        # self.i2c.writeto(GPS_I2CADDR, self.rmc)
        # self.i2c.writeto(GPS_I2CADDR, bytes([0]))
        # output rate to 1Hz
        # self.fivehz = "$PMTK220,200*2C\r\n"
        # self.onehz  = "$PMTK220,1000*1F\r\n"
        # self.i2c.writeto(GPS_I2CADDR, self.onehz)
        # self.i2c.writeto(GPS_I2CADDR, bytes([0]))

        # Do an empty write ...
        #self.reg = bytearray(1)
        # can be also written as
        # self.i2c.writeto(GPS_I2CADDR, bytes([0]))
        #self.i2c.writeto(GPS_I2CADDR, self.reg)
        self.buff = b''

    def startGPSThread(self):
        # start thread feeding microGPS
        self.gps_thread = _thread.start_new_thread(self.feedMicroGPS,())
        return self.gps_thread

    def feedMicroGPS(self):
        self.logger.debug('Running feedGps_thread id: {}'.format(_thread.get_ident()))
        someNmeaData = ''
        while True:
            # get some NMEA data
            someNmeaData = str(self.i2c.readfrom(GPS_I2CADDR, 128))
            self.logger.debug(" feedGps_thread - gpsChars recieved : {}".format(len(someNmeaData)))
            self.logger.debug(" NMEA data: {}".format(str(someNmeaData)))

            # Pass NMEA data to micropyGPS object
            for x in someNmeaData:
                self.my_gps.update(str(x))
            time.sleep(1)

    def gpsParsing(self):
        for i in range(10):
            someNmeaData = self.i2c.readfrom(GPS_I2CADDR, 255)
            if 0:
                NMEAS_ = self.buff + someNmeaData.decode('ASCII')
                NMEAS = NMEAS_.split('\r\n')
                for idx, nmea in enumerate(NMEAS):
                    if idx < len(NMEAS)-1:
                        self.logger.debug(nmea.replace('\n',''))
                    else:
                        self.buff = nmea
            for x in str(someNmeaData):
                self.my_gps.update(str(x))
            time.sleep_ms(100)


    def gpsParsing_until_gpsFix(self):

        # CLEARING i2c buffer at the GPS chip
        while True:
            nmeas_ = self.i2c.readfrom(GPS_I2CADDR, 255)
            nmeas = nmeas_.decode('ASCII').replace('\n','')
            if nmeas == '':
                break

        buff = ''
        c = 0
        while True:
            nmeas_ = self.i2c.readfrom(GPS_I2CADDR, 255)
            buff += nmeas_.decode('ASCII')
            nmeas = buff.split('\r\n')
            for idx, nmea in enumerate(nmeas):
                if idx < len(nmeas)-1:
                    self.logger.debug(nmea.replace('\n',''))
                else:
                    buff = nmea
            for x in str(nmeas_):
                self.my_gps.update(str(x))
            self.logger.debug("{:3} {:3} {:} {:} {:3}".format(
                self.my_gps.fix_stat,
                self.my_gps.satellites_in_use,
                self.my_gps.timestamp,
                self.my_gps.date,
                self.my_gps.hdop))
            if c > 3 and self.my_gps.fix_stat > 0:
                return
            time.sleep_ms(100)
            c += 1
