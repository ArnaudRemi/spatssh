#! /usr/local/bin/python3.4

import base64
from binascii import hexlify
import os
import socket
import sys
import traceback
import _thread

import paramiko
from paramiko.py3compat import b, u, decodebytes
from Server import Server
from Spatssh import Spatssh

HOST = ''
PORT = 2200


def thread_it(client):
    try:
        bridge = spatssh.auth_client(client)
        if bridge is not None:
            print('Authenticated!')
            bridge.discuss_with_client()
            bridge.shutdown_connection()
    except Exception as e:
        print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
        traceback.print_exc()

f = open('/var/run/spatssh.pid', 'w')
f.write(str(os.getpid()))
f.close()
# setup logging
paramiko.util.log_to_file('/var/log/paramiko-spatssh.log')

# host_key = paramiko.DSSKey(filename='test_dss.key')

spatssh = Spatssh()

# Socket init for the SSh communication
spatssh.init_socket(HOST, PORT)

# a mettre dans une boucle
while True:
    # waiting for the SSH client, return client socket
    client = spatssh.wait_client()
    print('Got a connection!')
    if client is None:
        pass

    # lancer un thread
    _thread.start_new_thread(thread_it, (client,))
    #thread_it()
