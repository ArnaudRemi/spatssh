import config
# from Client import Client

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
        # boucler / sortir si exit
        self.chan.send('We are ready to connect you to one of our servers\r\n')
        self.chan.send('Which one would you like to be connected at?\r\n')
        # for name in config dict
        # self.chan.send(name)
        self.chan.send('Server\'s name:')
        self.fchan = self.chan.makefile('rU')
        servername = self.fchan.readline().strip('\r\n')
        if servername == "":
            self.chan.send('\r\nThe server name is empty.\r\n')

            response = self.ask_if_client_leaving()
            # if response:
                # break
        if servername in config.servers:
            self.chan.send('\r\nI\'m trying to connect you to ' + servername + '.\r\n')
            ret = self.bridge_to(servername)
            # if ret == "exit":
                # break
        else:
            self.chan.send('\r\n' + servername + ' does not exist.\r\n')

    def ask_if_client_leaving(self):
        self.chan.send('Do you want to leave us? (Y/N) :')
        response = self.fchan.readline().strip('\r\n')
        if response == "Y":
            return True
        return False

    def shutdown_connection(self):
        self.chan.close()

    def bridge_to(self, servername):
        ip, port = config.servers[servername]
        # sshclient = Client(self.username, ip, port)

        pass
