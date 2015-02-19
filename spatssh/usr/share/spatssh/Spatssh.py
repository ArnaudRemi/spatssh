import base64
from binascii import hexlify
import os
import socket
import sys
import traceback

import paramiko
from paramiko.py3compat import b, u, decodebytes
from Server import Server
from Bridge import Bridge


class Spatssh:

    # DoGSSAPIKeyExchange = True
    DoGSSAPIKeyExchange = False
    sock = None
    server = None
    transport = None

    def __init__(self):
        self.host_key = paramiko.RSAKey(filename='/etc/spatssh/id_rsa')
        print('Read key: ' + u(hexlify(self.host_key.get_fingerprint())))
        self.max_client = 100

    def accept_gss(self, accept):
        self.DoGSSAPIKeyExchange = accept

    def init_socket(self, host, port):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((host, port))
        except Exception as e:
            print('*** Bind failed: ' + str(e))
            traceback.print_exc()
            raise

    def wait_client(self):
        try:
            self.sock.listen(100)
            print('Listening for connection ...')
            client, addr = self.sock.accept()
            return client
        except Exception as e:
            print('*** Listen/accept failed: ' + str(e))
            traceback.print_exc()
            return None

    def auth_client(self, client):
        try:
            self.transport = paramiko.Transport(client, gss_kex=self.DoGSSAPIKeyExchange)
            self.transport.set_gss_host(socket.getfqdn(""))
            try:
                self.transport.load_server_moduli()
            except:
                print('(Failed to load moduli -- gex will be unsupported.)')
                raise
            bridge = Bridge()
            self.transport.add_server_key(self.host_key)
            self.server = Server(bridge)
            try:
                self.transport.start_server(server=self.server)
            except paramiko.SSHException:
                print('*** SSH negotiation failed.')
                return None

            # wait for auth
            chan = self.transport.accept(20)
            if chan is None:
                print('*** No channel.')
                return None
            bridge.chan = chan

            # wait the client ask for a shell
            self.server.event.wait(10)
            if not self.server.event.is_set():
                print('*** Client never asked for a shell.')
                return None
            return bridge

        except Exception as e:
            print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
            traceback.print_exc()
            try:
                self.transport.close()
            except:
                pass
            return None

    def close_spatshh(self):
        self.transport.close()
