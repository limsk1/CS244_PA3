#!/bin/bash

config_file='5-1_config'
bwhost=1000
bwbottle=1.5
time=100
blen=100

rootdir='5-1'
rm -rf $rootdir
for plen in 400 500 600 700 800 900 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 2000 3000 4000 5000; do
    dir=p-$plen

    for i in 1 2 3 4 5; do
        subdir=t-$i
        python shrew_attack.py -f $config_file -B $bwhost -b $bwbottle -d $rootdir/$dir/$subdir -t $time --blen $blen --plen $plen
        mn -c
    done
done

python plot_figure_5_1.py -d $rootdir 
