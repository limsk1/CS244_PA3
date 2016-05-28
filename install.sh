git clone git://github.com/mininet/mininet
mininet/util/install.sh -a
wget https://iperf.fr/download/ubuntu/libiperf0_3.1.2-1_amd64.deb
wget https://iperf.fr/download/ubuntu/iperf3_3.1.2-1_amd64.deb
sudo dpkg -i libiperf0_3.1.2-1_amd64.deb iperf3_3.1.2-1_amd64.deb
rm libiperf0_3.1.2-1_amd64.deb iperf3_3.1.2-1_amd64.deb
sudo apt-get update
apt-get install --assume-yes libfreetype6-dev libxft-dev
apt-get install --assume-yes python-dev python-pip
pip install matplotlib
pip install termcolor
