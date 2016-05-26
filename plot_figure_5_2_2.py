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
    blen = int(re.match('b-([0-9]+)', d).group(1))
    testd = [f for f in os.listdir(os.path.join(args.dir, d))]
    aggregated = 0.0
    for test in testd:
        file_path = os.path.join(args.dir, d, test, "result.txt")
        with open(file_path, 'r') as result_file:
            aggregated += float(result_file.readlines()[1].strip())

    aggregated /= len(testd)
    aggregated /= 10
    data.append([blen, aggregated])

m.rc('figure')
fig = figure()
ax = fig.add_subplot(111)

def getkey(item):
   return item[0]

data_sort = sorted(data, key=getkey)

xaxis = map(float, col(0, data_sort))
yaxis = map(float, col(1, data_sort))

ax.plot(xaxis, yaxis, lw=2)
plt.ylabel("Throughput Normalized")
plt.xlabel("Burst Length(ms)")
plt.grid(True)

plt.savefig("5-2-2.png")
