from helper import *
import plot_defaults

from matplotlib.ticker import MaxNLocator
from pylab import figure
import os, re, string
import collections
import ast
import operator
import numpy as np

attackdir = '5-2-1'
noattackdir = '5-2-1_2'



data = []
rtts = [20, 43, 66, 89, 112, 135, 158, 182, 205, 228, 251, 274, 297, 321, 344, 367, 390, 413 , 436, 460]

    
def get_results(datadir):
    testd = [f for f in os.listdir(datadir)]
    aggregate_results = collections.defaultdict(float)
    for test in testd:
        file_path = os.path.join(datadir, test, "result.txt")
        with open(file_path, 'r') as result_file:
            results = ast.literal_eval(result_file.readlines()[0])
            for r in results:
                aggregate_results[rtts[int(r[0][6:])-3]] +=  r[1]/5.0/10.0
    aggregate_results = dict(aggregate_results).items()
    aggregate_results.sort(key = operator.itemgetter(0))
    return [ar[0] for ar in aggregate_results], [ar[1] for ar in aggregate_results]

attack_rtt, attack_throughput = get_results(attackdir)
noattack_rtt, noattack_throughput = get_results(noattackdir)

#print attack_rtt, attack_throughput
#print noattack_rtt, noattack_throughput

m.rc('figure')
fig = figure()
ax = fig.add_subplot(111)

#anomaly = np.argmax(attack_throughput)
#scale_factor = np.sum(attack_throughput)/(np.sum(attack_throughput) - np.max(attack_throughput))
#print scale_factor
#attack_throughput = np.array(attack_throughput)*scale_factor
#attack_throughput[anomaly] = 0;

#ax.plot(noattack_rtt, np.array(attack_throughput)/np.array(noattack_throughput))
ax.plot(noattack_rtt, noattack_throughput, lw=2, label="no DOS")
ax.plot(attack_rtt, attack_throughput, lw=2, label="DOS")
plt.ylabel("Normalized Throughput")
plt.xlabel("RTT")
plt.grid(True)
plt.legend()
plt.tight_layout()
#plt.show()
plt.savefig("5-2-1.png")
fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(noattack_rtt, np.array(attack_throughput)/np.array(noattack_throughput))
plt.ylabel("Dos/No Dos Throghput Ratio")
plt.xlabel("RTT")
plt.ylim([0,0.4])
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("5-2-1_2.png")
