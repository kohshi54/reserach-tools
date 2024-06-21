#!/bin/bash

#get rate from num:asn list

#total=$(cat $1 | awk '{sum += $1} END {print sum}')
# user側だとsoftetherのASが59%を占めるので他が全て1%になってしまいよくわからないので除外.
total=$(cat $1 | awk 'NR != 1 {sum += $1} END {print sum}')
#cat $1 | awk -v total=$total '{printf "%d %d (%.0f%%)\n", $1, $2, ($1 /total ) * 100}' | sudo tee $1.rate
cat $1 | awk -v total=$total 'NR != 1 {printf "%d %d (%.0f%%)\n", $1, $2, ($1 /total ) * 100}' | sudo tee $1.rate

