# How to USE
#
# import gmail
# to = 'dr.ki.koo@gmail.com'
# subject = 'email from WiPy'
# contents = 'Hello World \n 2nd sentence... WoW!'
# gmail.send(to,subject,contents)

import smtplib

def send(to,subject,contents):
    #to = 'dr.ki.koo@gmail.com'
    gmail_user = 'shm.fsdl.mon@gmail.com'
    gmail_pwd =  "veshm1234"
    #smtpserver = smtplib.SMTP("smtp.gmail.com", 587, tls=False)
    # smtpserver = smtplib.SMTP("smtp.gmail.com", 465, tls=False)
    smtpserver = smtplib.SMTP("smtp.gmail.com", 465, tls=True)
    smtpserver.starttls()
    smtpserver.helo()
    smtpserver.login(gmail_user, gmail_pwd)
    msg    = 'To:' + to + '\n' +\
             'From: ' + gmail_user + '\n' + \
             'Subject: ' + subject + ' \n' + \
             contents
    smtpserver.sendmail(gmail_user, to, msg)
    smtpserver.close()


# if __name__ == '__main__':
