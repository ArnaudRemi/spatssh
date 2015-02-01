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

# host_key = paramiko.DSSKey(filename='test_dss.key')

spatssh = Spatssh()

# Socket init for the SSh communication
spatssh.init_socket(HOST, PORT)

# a mettre dans une boucle
# waiting for the SSH client, return client socket
client = spatssh.wait_client()
print('Got a connection!')
# if client is None:
    # break

# lancer un thread
try:
    bridge = spatssh.auth_client(client)
    if bridge is not None:
        print('Authenticated!')
    else:
        # close connection and socket
        # stop the thread
        sys.exit(1)
    bridge.discuss_with_client()
    bridge.shutdown_connection()

except Exception as e:
    print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
    traceback.print_exc()
