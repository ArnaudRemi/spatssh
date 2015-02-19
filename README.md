# spatssh
ssh serveur to connect to other ssh server.

How to install it :
./build //to create spatssh.deb.
sudo dpkg --install spatssh.deb //to install spatssh like standart program and service.
sudo update-rc.d spatssh defaults //to enable spatssh service on startup
sudo update-rc.d -f spatssh remove //to disable spatssh service on startup
