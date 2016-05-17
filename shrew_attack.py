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

# Expt parameters
args = parser.parse_args()
num_hosts = 0
iperf_subproc = []

class AttackTopo(Topo):
    "Simple topology for low-rate DoS experiment."

    def build(self):
        server = self.addHost('server')
        attacker = self.addHost('attacker')

        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')

        self.addLink(s0, s1, bw=args.bw_bottle, max_queue_size=args.maxq)
        self.addLink(attacker, s0, bw=args.bw_host)
        self.addLink(server, s1, bw=args.bw_host)

        config_file = open(args.config_file, 'r')
        global num_hosts
        try:
            num_hosts = int(config_file.readline())
        except:
            print "Host configuration file should start with number of hosts"
            sys.exit(1)

        rtt_list = config_file.readline().split(' ')
        if len(rtt_list) != num_hosts:
            print "Wrong number of hosts specified"
            sys.exit(1)

        for i in range(0, num_hosts):
            try:
                h = self.addHost('h{}'.format(i))
                delay = int(rtt_list[i])
                self.addLink(h, s0, bw=args.bw_host, delay = str(delay) + 'ms')
            except:
                print "Wrong configuration file"
                sys.exit(1) 
        return

def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_iperf(net):
    server = net.get('server')
    print "Starting iperf server..."
    # For those who are curious about the -w 16m parameter, it ensures
    # that the TCP flow is not receiver window limited.  If it is,
    # there is a chance that the router buffer may not get filled up.
    server.popen("iperf3 -s -p 5000 > server.txt", shell=True)

    global iperf_subproc
    for i in range(0, num_hosts):
        h = net.get('h{}'.format(i))
        server.popen("iperf3 -s -p {}".format(5001 + i), shell=True)
        p = h.popen("iperf3 -c {} -i 0 -f m -p {} -t {} > h{}.txt".format(server.IP(), 5001 + i, args.time, i), shell=True)
        iperf_subproc.append(p)

#ping = h1.popen("ping %s -i 0.1 > %s/%s" %(h2.IP(), args.dir, "ping.txt") , shell=True)

def configure_rto(net):
    rto_config = []
    server = net.get('server')
    p = server.popen("ip route change 10.0.0.0/8 dev server-eth0 rto_min 1000 scope link src {} proto kernel".format(server.IP()), shell = True)
    rto_config.append(p)
    for i in range(0, num_hosts):
        h = net.get('h{}'.format(str(i)))
        p = h.popen("ip route change 10.0.0.0/8 dev h{}-eth0 rto_min 1000 scope link src {} proto kernel".format(i, h.IP()), shell = True)
        rto_config.append(p)

    done = False
    while not done:
       done = True
       for p in rto_config:
           if p.poll() is None:
               done = False
               break


def start_attack(net):
    attacker = net.get('attacker')
    server = net.get('server')

    attacker.popen("python attacker.py -T %s -P %s" % (server.IP(), 5000), shell=True)

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
    # This performs a basic all pairs ping test.
    net.pingAll()

    qmon = start_qmon(iface='s0-eth1',
                      outfile='%s/q.txt' % (args.dir))

    configure_rto(net)
    start_iperf(net)
    sleep(1)
    start_attack(net)

    sleep(args.time)
    done = False
    while not done:
       done = True
       for p in iperf_subproc:
           if p.poll() is None:
               done = False
               break

    qmon.terminate()
    net.stop()

if __name__ == "__main__":
    simulateAttack()
