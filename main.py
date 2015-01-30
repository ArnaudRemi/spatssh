import base64
from binascii import hexlify
import os
import socket
import sys
import traceback

import paramiko
from paramiko.py3compat import b, u, decodebytes
from Server import Server
from Spatssh import Spatssh

HOST = ''
PORT = 2200

# setup logging
paramiko.util.log_to_file('paramiko-spatshh.log')

#host_key = paramiko.DSSKey(filename='test_dss.key')



spatssh = Spatssh()

# Socket init for the SSh communication
spatssh.init_socket(HOST, PORT)

# a mettre dans une boucle
# waiting for the SSH client, return client socket
client = spatssh.wait_client()
print('Got a connection!')


try:
    chan = spatssh.auth_client(client)
    if chan is not None:
        print('Authenticated!')
    else:
        sys.exit(1)

    
    #à remplacer par le choix du serveur final
    chan.send('\r\n\r\nWelcome to my dorky little BBS!\r\n\r\n')
    chan.send('We are on fire all the time!  Hooray!  Candy corn for everyone!\r\n')
    chan.send('Happy birthday to Robot Dave!\r\n\r\n')
    chan.send('Username: ')
    f = chan.makefile('rU')
    username = f.readline().strip('\r\n')
    chan.send('\r\nI don\'t like you, ' + username + '.\r\n')
    chan.close()

except Exception as e:
    print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
    traceback.print_exc()
    try:
        t.close()
    except:
        pass
    sys.exit(1)

