# -*- coding: utf-8 -*-
"""
ReadResol

Reads Resol Solar Controller Serial interface and posts the data into Homematic

The serial stream format is split in packages with the initial signature of

aa 10 40 21 32 10 00 03 00 49 aa 10 00 21 32 10 00 01 04 07

The subsequent section of the packages contains the temperature and
pump speed and pump runtime data

"""

import sys
import time
import binascii
import logging
import logging.handlers as handlers
import serial
import urllib3

LOGFILE = '/var/log/readresol.log'
LOGTOSTDOUT = False
LOGTARGET = ['homematic', 'iobroker']
#LOGTARGET = ['iobroker', 'homematic']
#LOGFILE = '/home/rainer/Dokumente/readresol-code/readresol.log'
HOMEMATICPATH = "http://homematic.ps.minixhofer.com"
HMISEIDS = "3144,26625,3145,7490,7491,7492,7493"
IOBROKERPATH = "http://server2.ps.minixhofer.com:8087"
IOBROKERDIR = "0_userdata.0.SolarThermie"
IOBROKERDPTS = ["Solarkollektor_Temperatur", "Schwimmbad_Temperatur", "Boiler_Temperatur", "Solarpumpengeschwindigkeit", "Solarventil", "Laufzeit_Solarpumpe", "Laufzeit_Solarventil"]
PORTNAME = '/dev/RESOL'
TIMEOUT = 60*2 # Timeout if no serial data collected within 2 minutes
loghandlers = [handlers.TimedRotatingFileHandler(LOGFILE, when='D', interval = 7)]
if LOGTOSTDOUT:
    loghandlers.append(logging.StreamHandler())
logging.basicConfig(level=logging.INFO,\
                    format='%(asctime)s %(levelname)-8s %(message)s',\
                    handlers=loghandlers,\
                    datefmt='%Y-%m-%d %H:%M:%S')
#logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',level=logging.DEBUG,datefmt='%Y-%m-%d %H:%M:%S')

def write_to_homematic(data):
    """
    Writes measurement data from meternr into Homematic using the ISE-IDs
    specified in HMISEIDS[<meternr>]

    Parameters
    ----------
    meternr : Integer
        Modbus number of meter to be read
    hmdata : String
        String to be written into Homematic with XML-API call

    Returns
    -------
    None.

    """
    try:
        http = urllib3.PoolManager()
        request = HOMEMATICPATH + "/config/xmlapi/statechange.cgi?ise_id=" \
                        + HMISEIDS + "&new_value=" + data
        http.request('GET', request)
        logging.debug('Data written to Raspberrymatic.')
        logging.debug('GET request: %s',request)
    except IOError:
        logging.error('URLError. Trying again in next time interval.')

def write_to_iobroker(data):
    """
    Writes measurement data from meternr into iobroker using the simple-API and
    the datapoints specified in IOBROKERDPTS

    Parameters
    ----------
    iobdata : String
        String to be written into iobroker with simple-API call

    Returns
    -------
    None.

    """
    try:
        http = urllib3.PoolManager()
        request = IOBROKERPATH + "/setBulk?" + data
        http.request('GET', request)
        logging.debug('Data written to IOBroker.')
        logging.debug('GET request: %s',request)
    except IOError:
        logging.error('URLError. Trying again in next time interval.')

# 9600 baud, 8 databits, no parity, 1 stopbit and no handshake (rtscts=False)

ser = serial.Serial(port=PORTNAME,baudrate=9600, bytesize=serial.EIGHTBITS, timeout=10, \
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, rtscts=False)

ser.flushInput()

timeout_start = time.time()

while time.time() < timeout_start + TIMEOUT:
    try:
        #Wait for the 3-byte sequence 'aa 10 40' which defines the boundary between packages
        header = ser.read(1)
        if header == bytes.fromhex('aa'):
            header += ser.read(2)
            if header == bytes.fromhex('aa 10 40'):
            #Check if remaining signature is correct as well
                header += ser.read(17)
                if header == bytes.fromhex(('aa 10 40 21 32 10 00 03 00 49 '
                                            'aa 10 00 21 32 10 00 01 04 07')):
                #Read data part of the packet
                    ser_bytes = ser.read(24)
                    logging.debug('Data packet: %s', binascii.hexlify(ser_bytes, ','))
                    timeout_start = time.time() # Reset Timeout
                    chksum11 = ser_bytes[5]
                    temp1 = ser_bytes[0] + ser_bytes[1] * 256 + \
                        (128 if ser_bytes[4] & 1 << 0 else 0)
                    if temp1 > 16383:
                        temp1 = -(~temp1 & 16383)
                    temp1 /= 10
                    temp2 = ser_bytes[2] + ser_bytes[3] * 256 + \
                        (128 if ser_bytes[4] & 1 << 2 else 0)
                    if temp2 > 16383:
                        temp2 = -(~temp2 & 16383)
                    temp2 /= 10
                    chksum12 = ser_bytes[11]
                    temp3 = ser_bytes[6] + ser_bytes[7] * 256 + \
                        (128 if ser_bytes[10] & 1 << 0 else 0)
                    if temp3 > 16383:
                        temp3 = -(~temp3 & 16383)
                    temp3 /= 10
                    pusp1 = ser_bytes[8]
                    pusp2 = ser_bytes[9]
                    chksum21 = ser_bytes[10]
                    chksum22 = ser_bytes[11]
                    rflg1 = ser_bytes[12]
                    rflg2 = ser_bytes[13]
                    error = ser_bytes[14]
                    unknown = ser_bytes[15]
                    chksum31 = ser_bytes[16]
                    chksum32 = ser_bytes[17]
                    rtim1 = ser_bytes[18] + 256 * ser_bytes[19]
                    rtim2 = ser_bytes[20] + 256 * ser_bytes[21]
                    chksum41 = ser_bytes[22]
                    chksum42 = ser_bytes[23]
                    logtime = time.time()
                    logging.info((
                           'T1:%f T2:%f T3:%f vP1:%d vP2:%d rf1:%d rf2:%d '
                           'error:%d tp1:%d tp2:%d chksum11:%d chksum12:%d '
                           'chksum21:%d chksum22:%d chksum31:%d chksum32:%d '
                           'chksum41:%d chksum42:%d unknown:%d') , \
                                 temp1, temp2, temp3, pusp1, pusp2, rflg1, rflg2, \
                                 error, rtim1, rtim2, chksum11, chksum12, \
                                 chksum21, chksum22, chksum31, chksum32, chksum41, chksum42, \
                                 unknown)
                    #Write temperatures, solar pump speed, solar valve setting,
                    #and runtimes to homematic
                    if 'homematic' in LOGTARGET:
                        hmdata = ('%(T1).1f,%(T2).1f,%(T3).1f,'
                                '%(PUMPSPEED1)d,%(PUMPSPEED2)d,'
                                '%(RUNTIME1)d,%(RUNTIME2)d') % \
                            {"T1": temp1, "T2": temp2, "T3": temp3,
                            "PUMPSPEED1": pusp1,"PUMPSPEED2": pusp2,
                            "RUNTIME1": rtim1, "RUNTIME2": rtim2}
                        write_to_homematic(hmdata)
                    #Write temperatures, solar pump speed, solar valve setting,
                    #and runtimes to iobroker
                    #Set Solarventil to false if pusp2==0 otherwise to true
                    #We convert the Solarventil state already to a string and lowercase since the uppercase
                    #values True and False are interpreted as strings leading to info messages in the iobroker log
                    if 'iobroker' in LOGTARGET:
                        pusp2 = str(pusp2 != 0).lower()
                        iobdpts = [IOBROKERDIR + "." + dpt + "=" + str([temp1, temp2, temp3, pusp1, pusp2, rtim1, rtim2][i]) for i,dpt in enumerate(IOBROKERDPTS)]
                        iobdata = '&'.join(iobdpts)
                        write_to_iobroker(iobdata)
#                        for i,dpt in enumerate(IOBROKERDPTS):
#                            iobdata = IOBROKERDIR + "." + dpt + "?value=" + str([temp1, temp2, temp3, pusp1, pusp2, rtim1, rtim2][i])
#                            write_to_iobroker(iobdata)
                else:
                    logging.error('Serial package header %s incorrect, skipping data', header)
    except KeyboardInterrupt:
        ser.close()
        logging.warning("Keyboard Interrupt")
        sys.exit()

ser.close()
logging.warning('Waited %s seconds and never saw what I wanted', TIMEOUT)
