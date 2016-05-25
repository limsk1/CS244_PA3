#!/bin/bash

config_file='5-2-1_config'
bwhost=1000
bwbottle=10
time=1000
blen=200
plen=1100

rootdir='5-2-1'
for i in 1 2 3 4 5; do
    subdir=t-$i
    python shrew_attack.py -f $config_file -B $bwhost -b $bwbottle -d $rootdir/$dir/$subdir -t $time --blen $blen --plen $plen
    mn -c
done

rootdir2='5-2-1_2'
for i in 1 2 3 4 5; do
    subdir=t-$i
    python shrew_attack.py --no-attacker -f $config_file -B $bwhost -b $bwbottle -d $rootdir/$dir/$subdir -t $time --blen $blen --plen $plen
    mn -c
done

#python plot_figure_5_1.py -d $rootdir 
