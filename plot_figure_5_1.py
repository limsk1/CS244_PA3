from helper import *
import plot_defaults

from matplotlib.ticker import MaxNLocator
from pylab import figure
import os, re, string

parser = argparse.ArgumentParser()

parser.add_argument('--dir', '-d',
                    help="Directory where data exist",
                    required = True)

args = parser.parse_args()

dirs = [f for f in os.listdir(args.dir)]

data = []

for d in dirs:
    plen = int(re.match('p-([0-9]+)', d).group(1))
    testd = [f for f in os.listdir(os.path.join(args.dir, d))]
    aggregated = 0.0
    for test in testd:
        iperf_results = [f for f in os.listdir(os.path.join(args.dir, d, test)) if f.endswith('.txt')]
        for result in iperf_results:
            file_path = os.path.join(args.dir, d, test, result)
            with open(file_path, 'r') as iperf_result:
                line = iperf_result.readlines()[-4]
                bwtok = line.split()[6]
                aggregated += float(bwtok)

    aggregated /= 5
    data.append([plen, aggregated])

m.rc('figure')
fig = figure()
ax = fig.add_subplot(111)

def getkey(item):
   return item[0]

data_sort = sorted(data, key=getkey)

xaxis = map(float, col(0, data_sort))
yaxis = map(float, col(1, data_sort))

ax.plot(xaxis, yaxis, lw=2)
plt.ylabel("Aggregated Bandwidth (Mb/s)")
plt.grid(True)

plt.savefig("5-1.png")
