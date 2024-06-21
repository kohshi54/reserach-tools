#!/bin/bash

set -e

if [ "$1" = "" ]; then
	echo "input file name to process"
	exit
fi

input_file=$1
echo $input_file

echo "retx/all_pkts for each flow and all"
if [ "$2" == debug ]; then
	echo "c_ip,c_pkts_all,c_pkts_retx,s_ip,s_pkts_all,s_pkts_retx"
	echo "-------"
fi

awk -v debug="$2" '
BEGIN {
	total_c_pkts_all = 0
	total_c_pkts_retx = 0
	total_s_pkts_all = 0
	total_s_pkts_retx = 0
}
{
	c_pkts_all=$3
	c_pkts_retx=$10
	s_pkts_all=$17
	s_pkts_retx=$24

#	print "Processing line: " NR
#	print "c_ip: " $1
#	print "c_pkts_all: " c_pkts_all
#	print "c_pkts_retx: " c_pkts_retx
#	print "c_pkts_ooo: " c_pkts_ooo
#	print "s_ip: " $15
#	print "s_pkts_all: " s_pkts_all
#	print "s_pkts_retx: " s_pkts_retx
#	print "s_pkts_ooo: " s_pkts_ooo

	total_c_pkts_all += c_pkts_all
	total_c_pkts_retx += c_pkts_retx
	total_s_pkts_all += s_pkts_all
	total_s_pkts_retx += s_pkts_retx

	c_result = c_pkts_retx / c_pkts_all
	if (s_pkts_retx == 0) {
		s_result = 0.00
	} else {
		s_result = s_pkts_retx / s_pkts_all
	}

	if (c_result != 0.00 || s_result != 0.00) {
		if (debug == "debug") {
			print $1,c_pkts_all,c_pkts_retx,$15,s_pkts_all,s_pkts_retx
			printf "%d=Client: %.2f, Server: %.2f\n", NR, c_result, s_result
		}
	}
}
END {
	if ($2 == "debug") {
		printf "-------\n"
	}
	c_result = total_c_pkts_retx / total_c_pkts_all
	s_result = total_s_pkts_retx / total_s_pkts_all
	printf "Total Client: %.2f, Total Server: %.2f\n", c_result, s_result
} ' $input_file

