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
try:
    import interactive
except ImportError:
    from . import interactive

class Client:

    def __init__(self, hostname="127.0.0.1", port=2200, username="spatssh"):
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
            print('Trying ssh-agent key %s' % hexlify(key.get_fingerprint()))
            try:
                transport.auth_publickey(username, key)
                print('... success!')
                return
            except paramiko.SSHException:
                print('... nope.')


    def manual_auth(self, username, hostname):
        default_auth = 'p'
        auth = input('Auth by (p)assword, (r)sa key, or (d)ss key? [%s] ' % default_auth)
        if len(auth) == 0:
            auth = default_auth

        if auth == 'r':
            default_path = os.path.join(os.environ['HOME'], '.ssh', 'id_rsa')
            path = input('RSA key [%s]: ' % default_path)
            if len(path) == 0:
                path = default_path
            try:
                key = paramiko.RSAKey.from_private_key_file(path)
            except paramiko.PasswordRequiredException:
                password = getpass.getpass('RSA key password: ')
                key = paramiko.RSAKey.from_private_key_file(path, password)
            self.t.auth_publickey(username, key)
        elif auth == 'd':
            default_path = os.path.join(os.environ['HOME'], '.ssh', 'id_dsa')
            path = input('DSS key [%s]: ' % default_path)
            if len(path) == 0:
                path = default_path
            try:
                key = paramiko.DSSKey.from_private_key_file(path)
            except paramiko.PasswordRequiredException:
                password = getpass.getpass('DSS key password: ')
                key = paramiko.DSSKey.from_private_key_file(path, password)
            self.t.auth_publickey(username, key)
        else:
            pw = getpass.getpass('Password for %s@%s: ' % (username, hostname))
            self.t.auth_password(username, pw)

    def init_network(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.hostname, self.port))
        except Exception as e:
            print('*** Connect failed: ' + str(e))
            traceback.print_exc()
            raise

        try:
            self.t = paramiko.Transport(sock)
        except Exception as e:
            print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
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
                print('*** SSH negotiation failed.')
                raise

            try:
                keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
            except IOError:
                try:
                    keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
                except IOError:
                    print('*** Unable to open host keys file')
                    keys = {}

            # check server's host key -- this is important.
            key = self.t.get_remote_server_key()
            if self.hostname not in keys:
                print('*** WARNING: Unknown host key!')
            elif key.get_name() not in keys[self.hostname]:
                print('*** WARNING: Unknown host key!')
            elif keys[self.hostname][key.get_name()] != key:
                print('*** WARNING: Host key has changed!!!')
                raise
            else:
                print('*** Host key OK.')

            # get username
            if self.username == '':
                default_username = getpass.getuser()
                self.username = input('Username [%s]: ' % default_username)
                if len(self.username) == 0:
                    self.username = default_username

            self.agent_auth(self.t, self.username)
            if not self.t.is_authenticated():
                self.manual_auth(self.username, self.hostname)
            if not self.t.is_authenticated():
                print('*** Authentication failed. :(')
                self.t.close()
                raise

            chan = self.t.open_session()
            chan.get_pty()
            chan.invoke_shell()
            print('*** Here we go!\n')
            # soit on push dans ce chan, soit on remplace interactive shell par un bridge char by char
            interactive.interactive_shell(chan)
            chan.close()
            self.t.close()

        except Exception as e:
            print('*** Caught exception: ' + str(e.__class__) + ': ' + str(e))
            traceback.print_exc()
            try:
                self.t.close()
            except:
                pass
            raise


