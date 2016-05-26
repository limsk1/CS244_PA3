#!/usr/bin/python

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen
import termcolor as T
from helper import avg, stdev 

import sys
import os
import math
import re 

parser = ArgumentParser(description="Low-rate DoS tests")

parser.add_argument('--config-file', '-f',
                    help="Configuration file for benign hosts",
                    required = True)

parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-bottle', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    default = 1.5)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    default = '.')

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=1000)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=9)

parser.add_argument('--blen',
                    type=int,
                    help="Burst length in ms",
                    default = 100)

parser.add_argument('--plen',
                   type=int,
                   help="Length of one period",
                   default = 1000)

# Expt parameters
args = parser.parse_args()
num_hosts = 0
rtt_list = []

class AttackTopo(Topo):
    "Simple topology for low-rate DoS experiment."

    def build(self): 
        attacker = self.addHost('attacker')
        aServer = self.addHost('aServer')

        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')

        self.addLink(s0, s1, bw=args.bw_bottle, max_queue_size=args.maxq, delay = '2ms')
        self.addLink(attacker, s0, bw=args.bw_host, delay = '2ms') 
        self.addLink(aServer, s1, bw=args.bw_host, delay = '2ms')

        config_file = open(args.config_file, 'r')
        global num_hosts
        try:
            num_hosts = int(config_file.readline())
        except:
            print "Host configuration file should start with number of hosts"
            sys.exit(1)

        global rtt_list
        rtt_list = config_file.readline().split(' ')
        if len(rtt_list) != num_hosts:
            print "Wrong number of hosts specified"
            sys.exit(1)

        for i in range(0, num_hosts):
            try:
                hC = self.addHost('hC{}'.format(i))
                hS = self.addHost('hS{}'.format(i))
                delay = int(rtt_list[i])
                self.addLink(hC, s0, bw=args.bw_host, delay = str(delay - 4) + 'ms')
                self.addLink(hS, s1, bw=args.bw_host, delay = '2ms')
            except:
                print "Wrong configuration file"
                sys.exit(1) 
        return

def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

client_stream = []

def start_iperf(net):
    aServer = net.get('aServer')
    print "Starting iperf server..."
    aServer.popen("iperf3 -s -p 5001", shell=True)
    
    global client_stream
    for i in range(0, num_hosts):
        hC = net.get('hC{}'.format(i))
        hS = net.get('hS{}'.format(i))
        hS.popen("iperf3 -s -p 5001 --logfile {}/{}.txt".format(args.dir, i), shell=True)
        sleep(1)
        p = hC.popen("iperf3 -c {} -d -i 0 -f m -p {} -t {}".format(hS.IP(), 5001, args.time), shell=True)

#ping = h1.popen("ping %s -i 0.1 > %s/%s" %(h2.IP(), args.dir, "ping.txt") , shell=True)

def stop_iperf(net):
    os.system("killall -9 iperf3")

def configure_rto(net):
    rto_config = []
    for i in range(0, num_hosts):
        hC = net.get('hC{}'.format(str(i)))
        p = hC.popen("ip route change 10.0.0.0/8 dev hC{}-eth0 rto_min 900 scope link src {} proto kernel".format(i, hC.IP()), shell = True)
        rto_config.append(p)
        hS = net.get('hS{}'.format(str(i)))
        pS = hS.popen("ip route change 10.0.0.0/8 dev hS{}-eth0 rto_min 900 scope link src {} proto kernel".format(i, hS.IP()), shell = True)
        rto_config.append(pS)

    done = False
    while not done:
       done = True
       for p in rto_config:
           if p.poll() is None:
               done = False
               break


def start_attack(net):
    attacker = net.get('attacker')
    aServer = net.get('aServer')

    attacker.popen("python attacker.py -T %s -P %s -B %s -L %s" % (aServer.IP(), 5000, args.blen, args.plen), shell=True)


def get_byte_data():
    f = open('/proc/net/dev', 'r')
    lines = f.readlines()[2:]
    data = map(lambda x: x.split(':'), lines)
    data = map(lambda x: (x[0], float(x[1].split()[8])), data)
    return dict(data)

def calculate_byte_data(init, final, time):
    data = {}
    sum_tp = 0.0
    for k in init.keys():
        if re.match('s1-eth([3-9]|[1-9][0-9]+)', k) is None: continue
        data[k] = (final[k] - init[k]) * 8 / 1000000 / time
        sum_tp += data[k]

    def getKey(item):
        eth_num = re.match('s1-eth([3-9]|[1-9][0-9]+)', item[0]).group(1)
        return int(eth_num)

    data = sorted(data.items(), key=getKey)

    f = open('{}/result.txt'.format(args.dir), 'w')
    f.write(str(data) + "\n" + str(sum_tp))

def simulateAttack():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)

    print "Configuring TCP"

    print "Use TCP Reno"
    os.system("sysctl -w net.ipv4.tcp_congestion_control=reno")

    print "Disable F-RTO"
    os.system("sysctl -w net.ipv4.tcp_frto=0")

    topo = AttackTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)

    configure_rto(net)
    init_data = get_byte_data()
    start_attack(net)
    start = time()
    start_iperf(net)
    print "All benign flows start!"
    ping = net.get('hC0').popen("ping %s -i 0.1 > %s/%s" %(net.get('hS0').IP(), args.dir, "ping.txt") , shell=True)
    sleep(args.time)

    stop_iperf(net)
    total_time = time() - start
    final_data = get_byte_data()
    calculate_byte_data(init_data, final_data, total_time)
    net.stop()

if __name__ == "__main__":
    simulateAttack()
