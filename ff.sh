#!/bin/bash

set -e
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

target_dir=$1
pcapfiles=$(find "$target_dir" -name "div*.pcap")

tmp_dir="tmp_dir"
mkdir -p $tmp_dir

id=0;

for pcap in $pcapfiles
do
	cur_id=$id
	(
			echo $pcap
			echo $cur_id
			# make ip list from pcap (src only, dst->$18)
			#tcpdump -nnetr $pcapfile | awk '$13 == "ethertype" && $14 == "IPv4" {print $16}' | sed 's/\.[0-9]*$//' > ip.list
			#touch "$tmp_dir/$id.ip"
			tcpdump -nnetr $pcap | awk '$13 == "ethertype" && $14 == "IPv4" {split($16, a, "."); print a[1]"."a[2]"."a[3]"."a[4]}' | tee "$tmp_dir/$cur_id.ip" &>/dev/null
			
			# convert ip to asn
			#touch "$tmp_dir/$cur_id.asn"
			#python3 convertip2asn.py "$tmp_dir/$cur_id.ip" | sort -nr | uniq -c | sort -nrk1,1 | tee "$tmp_dir/$cur_id.asn" &>/dev/null
			python3 convertip2asn.py "$tmp_dir/$cur_id.ip" | sort -nr | tee "$tmp_dir/$cur_id.asn" &>/dev/null
	) &
	((id += 1))
done

wait

# no weight
#cat $tmp_dir/{1..120}.asn | sort -nr | uniq > serverasn.list
#cat $tmp_dir/{1..120}.asn | sort -nr | uniq > userasn.list

# with weight
cat $tmp_dir/{1..120}.asn | sort -nr | uniq -c | sort -nrk1,1 > serverasn_weight.list
#cat $tmp_dir/{1..120}.asn | sort -nr | uniq -c | sort -nrk1,1 > userasn_weight.list

## make ASPATH list from bgp message
#touch aspath.list
#chmod +w aspath.list
#bgpmessages="rib.20240401.0000"
#bgpdump $bgpmessages | grep ASPATH > aspath.list

## map asn appear to asn map (full route)
#python3 7.py

deactivate


