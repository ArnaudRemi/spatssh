import config
from Client import Client

class Bridge:

    chan = None
    fchan = None
    username = ""
    public_key = ""
    currentserver = ""

    def __init__(self):
        pass

    def discuss_with_client(self):
        if self.chan is None:
            return
        self.chan.send('\r\n\r\nWelcome to SpatSSH!\r\n\r\n')
        self.chan.send('We are ready to connect you to one of our servers\r\n')
        while True:
            self.chan.send('Which one would you like to be connected at?\r\n')
            self.chan.send('Chose the server between: ')
            for sname in config.servers.keys():
                self.chan.send(sname + " ")
            self.chan.send('\r\n')
            self.fchan = self.chan.makefile('rU')
            servername = self.fchan.readline().strip('\r\n')
            if servername == "":
                self.chan.send('\r\nThe server name is empty.\r\n')
                response = self.ask_if_client_leaving()
                if response:
                    break
            elif servername in config.servers:
                self.chan.send('\r\nI\'m trying to connect you to ' + servername + '.\r\n')
                ret = self.bridge_to(servername)
                if ret == "exit":
                    break
            else:
                self.chan.send('\r\n' + servername + ' does not exist.\r\n')
            self.chan.send('\r\n')

    def ask_if_client_leaving(self):
        self.chan.send('Do you want to leave us? (Y/N) :')
        response = self.fchan.readline().strip('\r\n')
        if response == "Y" or response == "y":
            return True
        return False

    def shutdown_connection(self):
        self.chan.close()

    def bridge_to(self, servername):
        ip, port = config.servers[servername]
        try:
            sshclient = Client(self, ip, port, self.username)
            sshclient.launch()
            response = self.ask_if_client_leaving()
            if response:
                return "exit"
            return "continue"
        except:
            pass
