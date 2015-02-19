# config file for the spatssh server.

# "username": "password"
users = {'foo': 'bar',
         'root': 'toor',
         'tutu': 'toto',
         'remi': 'coucou'}

# "servername": ("ip", port)
servers = {"Debian7_1": ("172.16.134.128", 22),
           "localhost": ("127.0.0.1", 22),
           "Debian7_2": ("172.16.134.202", 22)}
