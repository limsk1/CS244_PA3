#!/usr/bin/python
"CS244 Spring 2015 Assignment 1: Bufferbloat"

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

parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-net', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    default = 1.5)

parser.add_argument('--delay',
                    type=float,
                    help="Link propagation delay (ms)",
                    default = 25)

parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    default = '.')

parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=10)

parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)

# Linux uses CUBIC-TCP by default that doesn't have the usual sawtooth
# behaviour.  For those who are curious, invoke this script with
# --cong cubic and see what happens...
# sysctl -a | grep cong should list some interesting parameters.
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="reno")

# Expt parameters
args = parser.parse_args()

class BBTopo(Topo):
    "Simple topology for bufferbloat experiment."

    def build(self, n=2):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        switch = self.addSwitch('s0')

        self.addLink(h1, switch, bw=args.bw_host)
        self.addLink(switch, h2, bw=args.bw_net, delay=str(float(args.delay)/2)+'ms', max_queue_size=args.maxq)
        return

# Simple wrappers around monitoring utilities.  You are welcome to
# contribute neatly written (using classes) monitoring scripts for
# Mininet!
def start_tcpprobe(outfile="cwnd.txt"):
    os.system("rmmod tcp_probe; modprobe tcp_probe full=1;")
    Popen("cat /proc/net/tcpprobe > %s/%s" % (args.dir, outfile),
          shell=True)

def stop_tcpprobe():
    Popen("killall -9 cat", shell=True).wait()

def start_qmon(iface, interval_sec=0.1, outfile="q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_iperf(net):
    h2 = net.get('h2')
    print "Starting iperf server..."
    # For those who are curious about the -w 16m parameter, it ensures
    # that the TCP flow is not receiver window limited.  If it is,
    # there is a chance that the router buffer may not get filled up.
    server = h2.popen("iperf -s -p %s -w 16m" % (str(5001)))

def start_webserver(net):
    h1 = net.get('h1')
    proc = h1.popen("python http/webserver.py", shell=True)
    sleep(1)
    return [proc]

def start_ping(net):
    # Hint: Use host.popen(cmd, shell=True).  If you pass shell=True
    # to popen, you can redirect cmd's output using shell syntax.
    # i.e. ping ... > /path/to/ping.
    h1 = net.get('h1')
    h2 = net.get('h2')
    print "Start pinning from h1 to h2"
    ping = h1.popen("ping %s -i 0.1 > %s/%s" %(h2.IP(), args.dir, "ping.txt") , shell=True)

def fetch_webpage(net, times): 
    h1 = net.get('h1')
    h2 = net.get('h2')
    for i in range(0, 3):
        start_request = time()
    	fetch = h2.popen("curl -o /dev/null -s -w %%{time_total} %s/http/index.html" % h1.IP())
    	fetch.wait()
        end_request = time()
	times.append(end_request - start_request)

def start_attack(net):
    h1 = net.get('h1')
    h2 = net.get('h2')
    print h2.IP()
    h1.popen("python attacker.py -T %s -P %s > 1.txt" % (h2.IP(), 5001), shell=True)

def bufferbloat():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    topo = BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)
    # This performs a basic all pairs ping test.
    net.pingAll()

    # Start all the monitoring processes
    #start_tcpprobe("cwnd.txt")

    qmon = start_qmon(iface='s0-eth2',
                      outfile='%s/q.txt' % (args.dir))

    start_iperf(net)
    '''
    start_ping(net)
    start_webserver(net)

    # Hint: have a separate function to do this and you may find the
    # loop below useful.
    start_time = time()
    times = []
    while True:
        fetch_webpage(net, times)
	sleep(5)
        now = time()
        total_time = now - start_time
        if total_time > args.time:
            break
        print "%.1fs left..." % (args.time - total_time)

    print "Mean: " + str(avg(times))
    print "Stdev: " + str(stdev(times))

    stop_tcpprobe()
    qmon.terminate()
    '''

    start_attack(net)

    sleep(30)
    qmon.terminate()
    net.stop()
    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    Popen("pgrep -f attacker.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    bufferbloat()
