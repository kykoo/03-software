# A very simple FTP file dropper for WiPy enabled devices
#
# Version 1.0 Date 02.01.2016
# Version 1.1 Date 09.01.2016
#  - Replaced __ by _ according Perl Style Guidlines
#  - Return >= 300 status in case _sendfile had an error
#  - Changed error range from >=400 to >=300 for login issues
#  - Send QUIT before closing the connection
#  - Nonfunctional cleanups
#
# TO EXECUTE THIS:
# execfile('dropfile.py')
# dropfile('192.168.178.2', 21, 'dest_path', 'user', 'passwd', 'any.file')
#
# THE RETURN VALUES:
#    0 Everything went fine.
#   <0 Something with the sockets (file or FTP) isn't working out
#   >0 The status value from FTP
#
# WARNING:
# Simplified stuff which may break your code:
# 1. If FTP server responds with multiple line you're doomed
# 2. No support of ACCT, if FTP requires account should be easy to fix
# 3. No Active FTP, I did not manage to generate a new port with the WiPy socket.
# 4. No REST support.
# 5. And most important: It's not fully tested
# YOU'VE BEEN WARNED!


import os
import sys
import socket

_TIMEOUT = 10
_MAXLINE = 8192
_BLOCKSIZE = 8192
_CRLF = '\r\n'
_ENCODING = "latin-1"

def dropfile(host, port, cwd, user, passwd, file):
    # First try to reach and connect to FTP
    print('before connect')
    my_socket, my_file, status = _connect(host, port)
    print('after connect')

    if not my_socket:
        #COULD NOT REACH FTP
        return -1

    # Now try to log in
    print('before login')
    status = _login(my_socket, my_file, user, passwd)
    print('after login')
    if status >= 300:
        #COULD NOT LOGIN
        _close(my_socket, my_file)
        return status

    print('before cwd')
    if cwd:
        status = _changedir(my_socket, my_file, cwd)
        if status != 250:
            #COULD NOT CHANGE PATH
            _close(my_socket, my_file)
            return status
    print('after cwd')

    print('before sendfile')
    status = _sendfile(my_socket, my_file, file)
    if status >= 300 or status < 0:
        #SOMETHING WENT WRONG HERE
        _close(my_socket, my_file)
        return status
    print('after sendfile')
    return _close(my_socket, my_file)


def _connect(host, port):
    try:
        res = socket.getaddrinfo(host, port)
    except:
        #SOMETHING WRONG WITH THE SERVER OR PARAPETERS
        return('' ,'' ,-4)

    my_socket = None
    for sock in res:
        af, socktype, proto, canonname, sa = sock

        try:
            my_socket = socket.socket(af, socket.SOCK_STREAM, proto)
            break
        except:
            if my_socket:
                my_socket.close()
            continue

    if not my_socket:
        #NO VALID SOCKET FOUND
        return('', '', -5)

    my_socket.settimeout(_TIMEOUT)
    my_socket.connect(sa)

    my_file = my_socket.makefile()
    response, status = _getresponse(my_file)

    if status < 0 or status >= 400:
        #SOMETHING WENT WRONG
        _close(my_socket, my_file)
        return('', '', status)

    return(my_socket, my_file, status)


def _login(my_socket, my_file, user, passwd):
    resp, status = _sendcmd(my_socket, my_file, 'USER ' + user)
    print('{}{}'.format(resp.decode(),status))

    if status == 331:
        #Password required
        resp, status = _sendcmd(my_socket, my_file, 'PASS ' + passwd)
        print(resp)
    return status


def _changedir(my_socket, my_file, cwd):
    resp, status = _sendcmd(my_socket, my_file, 'CWD ' + cwd)
    return status


def _sendfile(my_socket, my_file, data_file):
    print('in _sendfile')
    try:
        fb = open(data_file, 'rb')
    except Exception as error:
        #PROBLEMS DURING OPEN SOURCE FILE
        print(error)
        return -8
    print('data_file opened')

    #resp, status = _sendcmd(my_socket, my_file, 'TYPE I')
    resp, status = _sendcmd(my_socket, my_file, 'TYPE A')
    print('_sendcmd {}{}'.format(resp,status))
    if status >=300:
        #COULD NOT SETUP TYPE
        return status

    resp, status = _sendcmd(my_socket, my_file, 'PASV')
    print('_sendcmd {}{}'.format(resp,status))

    IP, port, status = _parse227(resp)
    print('_parse227 {}{}'.format(port,status))
    if status != 0:
        return status

    res = socket.getaddrinfo(IP, port)
    print('_getaddrinfo {}'.format(res))

    data_socket = None
    for sock in res:
        af, socktype, proto, canonname, sa = sock
        if socktype != socket.SOCK_STREAM:
            continue
        try:
            data_socket = socket.socket(af, socket.SOCK_STREAM, proto)
            data_socket.settimeout(_TIMEOUT)
            data_socket.connect(sa)
        except:
            data_socket.close()

    if not data_socket:
        #NO VALID SOCKET FOUND
        return -7

    print('my_socket={}, my_file={}, data_file={}'.format(my_socket,my_file,data_file))
    data_file = data_file.split('/')[-1]
    resp, status = _sendcmd(my_socket, my_file, 'STOR ' + data_file)
    print('_sendcmd {}{}'.format(resp,status))

    print('line 176')
    if status >= 300:
        #SOME PROBLEM?
        return status

    # Finally transfer the file
    print('line 182')
    while 1:
        buf = fb.read(_BLOCKSIZE)
        if not buf:
            break
        data_socket.sendall(buf)
    print('line 188')
    fb.close()
    data_socket.close()

    print('line 192')
    resp, status = _getresponse(my_file)
    return status


def _close(my_socket, my_file):
    resp, status = _sendcmd(my_socket, my_file, 'QUIT')
    if status >=300:
        #COULD NOT SETUP TYPE
        return status

    try:
        if my_file is not None:
            my_file.close()
    finally:
        if my_socket is not None:
            my_socket.close()
    return 0


##########################
# General helper functions
##########################

def _getresponse(my_file):
    line, status = _getline(my_file)
    if status < 0:
        # PASS ERROR UP
        return('', status)

    try:
        status = int(line[0:3])
    except:
        status = 0;

    return(line, status )


def _getline(my_file):
    line = my_file.readline(_MAXLINE + 1)

    if not line:
        #RECEIVED EOF
        return('', -2)
    if len(line) > _MAXLINE:
        #MAXLINE EXCEEDED!
        return('', -1)
    if line[-2:] == _CRLF:
        line = line[:-2]
    elif line[-1:].decode() in _CRLF:
        line = line[:-1]
    return(line, 0)


def _sendcmd(my_socket, my_file, cmd):
    cmd = cmd + _CRLF
    my_socket.sendall(cmd.encode(_ENCODING))
    return _getresponse(my_file)


def _parse227(resp):
    # Decode the received string.
    # Do it manually, save memory by not use import re
    resp = resp.decode(_ENCODING)
    resplen = len(resp)
    startIP = 0
    while startIP < resplen:
        if resp[startIP] == '(':
            break
        startIP += 1

    startIP += 1
    endIP = startIP + 1
    coloncnt = 0

    while endIP < resplen:
        if resp[endIP] == ',':
            coloncnt += 1
            if coloncnt == 4:
                break
        endIP += 1

    IP = resp[startIP:endIP]
    IP = IP.replace(',', '.')

    startPort = endIP + 1
    pos = startPort
    while pos < resplen:
        if resp[pos] == ',':
            port = int(resp[startPort:pos]) << 8
            startPort = pos + 1
            pos += 2
            continue
        if resp[pos] == ')':
            port += int(resp[startPort:pos])
            break
        pos += 1

    if pos >= resplen:
        #MALFORMED RESPONSE
        return('', 0, -6)

    return(IP, port, 0)
