#!/bin/bash

config_file='5-2-2_config'
bwhost=1000
bwbottle=10
time=100
plen=1100

rootdir='5-2-2'
rm -rf $rootdir
for blen in 0 50 100 150 200; do
    dir=b-$blen

    for i in 1 2 3 4 5; do
        subdir=t-$i
        python shrew_attack.py -f $config_file -B $bwhost -b $bwbottle -d $rootdir/$dir/$subdir -t $time --blen $blen --plen $plen
        mn -c
    done
done

python plot_figure_5_2_2.py -d $rootdir 
