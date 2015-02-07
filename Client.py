import base64
from binascii import hexlify
import getpass
import os
import select
import socket
import sys
import time
import traceback
from paramiko.py3compat import input

import paramiko
import interactive

class Client:

    def __init__(self, bridge, hostname="127.0.0.1", port=2200, username="spatssh"):
        self.bridge = bridge
        self.hostname = hostname
        self.port = port
        self.username = username

    def agent_auth(self, transport, username):
        """
        Attempt to authenticate to the given transport using any of the private
        keys available from an SSH agent.
        """

        agent = paramiko.Agent()
        agent_keys = agent.get_keys()
        if len(agent_keys) == 0:
            return

        for key in agent_keys:
            self.bridge.chan.send('Trying ssh-agent key %s' % hexlify(key.get_fingerprint()))
            try:
                transport.auth_publickey(username, key)
                self.bridge.chan.send('... success!')
                return
            except paramiko.SSHException:
                self.bridge.chan.send('... nope.')


    def manual_auth(self, username, hostname):
        default_auth = 'p'
        self.bridge.chan.send('Auth by (p)assword, (r)sa key, or (d)ss key? [%s] \r\n' % default_auth)
        auth = self.bridge.fchan.readline().strip('\r\n')
        if len(auth) == 0:
            auth = default_auth


        if auth == 'r':
            self.rsa_auth(username)
        elif auth == 'd':
            self.dss_auth(username)
        else:
            self.password_auth(username, hostname)

    def rsa_auth(self, username):
        default_path = os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
        self.bridge.chan.send('RSA key [%s]: \r\n' % default_path)
        path = self.bridge.fchan.readline().strip('\r\n')
        if len(path) == 0:
            path = default_path
        try:
            key = paramiko.RSAKey.from_private_key_file(path)
        except paramiko.PasswordRequiredException:
            self.bridge.chan.send('RSA key password: \r\n')
            password = self.bridge.fchan.readline().strip('\r\n')
            key = paramiko.RSAKey.from_private_key_file(path, password)
        self.t.auth_publickey(username, key)

    def dss_auth(self, username):
        default_path = os.path.join(os.environ['HOME'], '.ssh', 'id_dsa')
        self.bridge.chan.send('DSS key [%s]: \r\n' % default_path)
        path = self.bridge.fchan.readline().strip('\r\n')
        if len(path) == 0:
            path = default_path
        try:
            key = paramiko.DSSKey.from_private_key_file(path)
        except paramiko.PasswordRequiredException:
            self.bridge.chan.send('DSS key password: \r\n')
            password = self.bridge.fchan.readline().strip('\r\n')
            key = paramiko.DSSKey.from_private_key_file(path, password)
        self.t.auth_publickey(username, key)

    def password_auth(self, username, hostname):
        self.bridge.chan.send('Password for %s@%s: \r\n' % (username, hostname))
        pw = self.bridge.fchan.readline().strip('\r\n')
        self.t.auth_password(username, pw)
        # self.t.auth_password("spatssh", "password123")

    def init_network(self):
        print("init network")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.hostname, self.port))
        except Exception as e:
            self.bridge.chan.send('*** Connect failed: ' + str(e))
            traceback.print_exc()
            raise

        try:
            self.t = paramiko.Transport(sock)
        except Exception as e:
            self.bridge.chan.send('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
            traceback.print_exc()
            try:
                self.t.close()
            except:
                pass
            raise

    def launch(self):
        self.init_network()
        try:
            try:
                self.t.start_client()
            except paramiko.SSHException:
                self.bridge.chan.send('*** SSH negotiation failed.')
                raise

            try:
                keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
            except IOError:
                try:
                    keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
                except IOError:
                    self.bridge.chan.send('*** Unable to open host keys file')
                    keys = {}

            # check server's host key -- this is important.
            key = self.t.get_remote_server_key()
            if self.hostname not in keys:
                self.bridge.chan.send('*** WARNING: Unknown host key!')
            elif key.get_name() not in keys[self.hostname]:
                self.bridge.chan.send('*** WARNING: Unknown host key!')
            elif keys[self.hostname][key.get_name()] != key:
                self.bridge.chan.send('*** WARNING: Host key has changed!!!')
                raise
            else:
                self.bridge.chan.send('*** Host key OK.')

            # get username
            if self.username == '':
                default_username = "spatssh"
                self.bridge.chan.send('Username [%s]: \r\n' % default_username)
                self.username = self.bridge.fchan.readline().strip('\r\n')
                if len(self.username) == 0:
                    self.username = default_username

            self.agent_auth(self.t, self.username)
            if not self.t.is_authenticated():
                self.manual_auth(self.username, self.hostname)
            if not self.t.is_authenticated():
                self.bridge.chan.send('*** Authentication failed. :(')
                self.t.close()
                raise

            self.chan = self.t.open_session()
            self.chan.get_pty()
            self.chan.invoke_shell()
            # interactive.interactive_shell(self.chan)
            self.connect_chans()
            self.chan.close()
            self.t.close()
        except Exception as e:
            self.bridge.chan.send('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
            traceback.print_exc()
            try:
                self.t.close()
            except:
                pass
            raise

    def connect_chans(self):
        print("connect chans")
        inputs = [self.chan, self.bridge.chan]
        try:
            while True:
                inputready,outputready,errorready = select.select(inputs,[],[])
                for i in inputready:
                    if i == self.chan:
                        str = self.chan.recv(1024)
                        if str is None or str == "":
                            raise
                        self.bridge.chan.send(str)
                    elif i == self.bridge.chan:
                        str = self.bridge.chan.recv(1024)
                        if str is None or str == "":
                            raise
                        self.chan.send(str)
                    else:
                        print("if select error")
        except:
            pass
        print("disconnect chans")


