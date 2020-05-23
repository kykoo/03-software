#!/usr/bin/env python3

import ssl
import socket
from binascii import b2a_base64, a2b_base64

SMTP_PORT = 25
SMTP_SSL_PORT = 465
CRLF = "\r\n"
bCRLF = b"\r\n"
_MAXLINE = 1024  # a good enough value for now

NL = '\n'
EMPTYSTRING = ''

class SMTPException(OSError):
    pass

class SMTPServerDisconnected(SMTPException):
    pass

class SMTPResponseException(SMTPException):
    def __init__(self, code, msg):
        self.smtp_code = code
        self.smtp_error = msg
        self.args = (code, msg)

class SMTPSenderRefused(SMTPResponseException):
    def __init__(self, code, msg, sender):
        self.smtp_code = code
        self.smtp_error = msg
        self.sender = sender
        self.args = (code, msg, sender)

class SMTPRecipientsRefused(SMTPException):
    def __init__(self, recipients):
        self.recipients = recipients
        self.args = (recipients,)

class SMTPDataError(SMTPResponseException):
    pass

class SMTPConnectError(SMTPResponseException):
    pass

class SMTPHeloError(SMTPResponseException):
    pass

class SMTPAuthenticationError(SMTPResponseException):
    pass

def encode_base64(s, maxlinelen=76, eol=NL):
    if not s:
        return s

    encvec = []
    max_unencoded = maxlinelen * 3 // 4
    for i in range(0, len(s), max_unencoded):
        enc = b2a_base64(s[i:i + max_unencoded]).decode("ascii")
        if enc.endswith(NL) and eol != NL:
            enc = enc[:-1] + eol
        encvec.append(enc)
    return EMPTYSTRING.join(encvec)

def _fix_eols(data):
    return data.replace(r'\r', '').replace('\r', '').replace(r'\n', CRLF).replace('\n', CRLF)

def quoteaddr(addrstring):
    return "<%s>" % addrstring

class SMTP (object):
    default_port = SMTP_PORT
    debuglevel = 0

    def __init__ (self, host='', port=0, local_hostname=None,
                  timeout=10000, source_address=None, tls=True):

        self._host = host
        self.timeout = timeout
        self.source_address = source_address
        self.tls = tls

        if host:
            (code, msg) = self.connect(host, port)
            if code != 220:
                raise SMTPConnectError(code, msg)
        if local_hostname is not None:
            self.local_hostname = local_hostname
        else:
            addr = '127.0.0.1'
            self.local_hostname = '[%s]' % addr

    def connect(self, host, port=0, source_address=None):
        if source_address:
            self.source_address = source_address

        if not port and (host.find(':') == host.rfind(':')):
            i = host.rfind(':')
            if i >= 0:
                host, port = host[:i], host[i + 1:]
                try:
                    port = int(port)
                except ValueError:
                    raise OSError("non numeric port")
        if not port:
            port = self.default_port
        if self.debuglevel > 0:
            print('connect:', (host, port), file=stderr)
        if self.tls:
            # ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_SEC)
            ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = ssl.wrap_socket(ss)
        else:
            self.sock = socket.socket()
        self.sock.settimeout(self.timeout)
        try:
            self.sock.connect(socket.getaddrinfo(host, port)[0][4])
        except:
            self.close()
        (code, msg) = self.getreply()
        if self.debuglevel > 0:
            print("connect:", msg, file=stderr)
        return (code, msg)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        try:
            code, message = self.docmd("QUIT")
            if code != 221:
                raise SMTPResponseException(code, message)
        except SMTPServerDisconnected:
            pass
        finally:
            self.close()

    def set_debuglevel(self, debuglevel):
        self.debuglevel = debuglevel

    def send(self, s):
        if self.debuglevel > 0:
            print('send:', repr(s), file=stderr)
        if hasattr(self, 'sock') and self.sock:
            if isinstance(s, str):
                s = s.encode("ascii")
            try:
                self.sock.send(s)
            except OSError:
                self.close()
                raise SMTPServerDisconnected('Server not connected')
        else:
            raise SMTPServerDisconnected('please run connect() first')

    def putcmd(self, cmd, args=""):
        if args == "":
            str = '%s%s' % (cmd, CRLF)
        else:
            str = '%s %s%s' % (cmd, args, CRLF)
        self.send(str)

    def getreply(self):
        resp = []
        while 1:
            try:
                line = self.sock.recv(_MAXLINE + 1)
            except OSError as e:
                self.close()
                raise SMTPServerDisconnected("Connection unexpectedly closed: " + str(e))
            if not line:
                self.close()
                raise SMTPServerDisconnected("Connection unexpectedly closed")
            if self.debuglevel > 0:
                print('reply:', repr(line), file=stderr)
            if len(line) > _MAXLINE:
                self.close()
                raise SMTPResponseException(500, "Line too long.")
            resp.append(line[4:].strip(b' \t\r\n'))
            code = line[:3]

            try:
                errcode = int(code)
            except ValueError:
                errcode = -1
                break
            # Check if multiline response.
            if line[3:4] != b"-":
                break

        errmsg = b"\n".join(resp)
        if self.debuglevel > 0:
            print('reply: retcode (%s); Msg: %s' % (errcode, errmsg), file=stderr)
        return errcode, errmsg

    def docmd(self, cmd, args=""):
        self.putcmd(cmd, args)
        return self.getreply()

    # std smtp commands
    def helo(self, name=''):
        self.putcmd("helo", name or self.local_hostname)
        (code, msg) = self.getreply()
        self.helo_resp = msg
        return (code, msg)

    def rset(self):
        return self.docmd("rset")

    def _rset(self):
        try:
            self.rset()
        except SMTPServerDisconnected:
            pass

    def noop(self):
        return self.docmd("noop")

    def mail(self, sender):
        self.putcmd("mail", "FROM:%s" % (quoteaddr(sender)))
        return self.getreply()

    def rcpt(self, recip):
        self.putcmd("rcpt", "TO:%s" % (quoteaddr(recip)))
        return self.getreply()

    def data(self, msg):
        self.putcmd("data")
        (code, repl) = self.getreply()
        if self.debuglevel > 0:
            print("data:", (code, repl), file=stderr)
        if code != 354:
            raise SMTPDataError(code, repl)
        else:
            if isinstance(msg, str):
                msg = _fix_eols(msg).encode('ascii')
            if msg[-2:] != bCRLF:
                msg = msg + bCRLF
            msg = msg + b"." + bCRLF
            self.send(msg)
            (code, msg) = self.getreply()
            if self.debuglevel > 0:
                print("data:", (code, msg), file=stderr)
            return (code, msg)

    def login(self, user, password):
        def encode_plain(user, password):
            s = "\0%s\0%s" % (user, password)
            return encode_base64(s.encode('ascii'), eol='')

        (code, resp) = self.docmd("AUTH", "%s %s" % ("LOGIN", encode_base64(user.encode('ascii'), eol='')))
        if code == 334:
            (code, resp) = self.docmd(encode_base64(password.encode('ascii'), eol=''))

        # 235 == 'Authentication successful'
        # 503 == 'Error: already authenticated'
        if code in (235, 503):
            return (code, resp)

        # Login failed. Return the result of last attempt.
        raise SMTPAuthenticationError(code, resp)

    def starttls(self, keyfile=None):
        (resp, reply) = self.docmd("STARTTLS")
        if resp == 220:
            self.helo_resp = None
        return (resp, reply)

    def sendmail(self, from_addr, to_addrs, msg):
        if isinstance(msg, str):
            msg = _fix_eols(msg).encode('ascii')
        (code, resp) = self.mail(from_addr)
        if code != 250:
            if code == 421:
                self.close()
            else:
                self._rset()
            raise SMTPSenderRefused(code, resp, from_addr)
        senderrs = {}
        if isinstance(to_addrs, str):
            to_addrs = [to_addrs]
        for each in to_addrs:
            (code, resp) = self.rcpt(each)
            if (code != 250) and (code != 251):
                senderrs[each] = (code, resp)
            if code == 421:
                self.close()
                raise SMTPRecipientsRefused(senderrs)
        if len(senderrs) == len(to_addrs):
            # the server refused all our recipients
            self._rset()
            raise SMTPRecipientsRefused(senderrs)
        (code, resp) = self.data(msg)
        if code != 250:
            if code == 421:
                self.close()
            else:
                self._rset()
            raise SMTPDataError(code, resp)
        #if we got here then the email was sent to at least one of the recipients
        return senderrs

    def close(self):
        if self.sock:
            self.sock.close()
        self.sock = None

    def quit(self):
        res = self.docmd("quit")
        self.ehlo_resp = self.helo_resp = None
        self.close()
        return res
