#!/bin/bash

ok=log_tcp_complete
error=log_tcp_nocomplete

show_flow_info()
{
	dir=$1

	# number of tcp flows (header is also counted but can be acceptable..?)
	echo "# total tcp flow"
	echo -n "complete   = " && cat $dir/$ok | wc -l
	echo -n "incomplete = " && cat $dir/$error | wc -l

	# number of uniq ip address in c_ip
	echo "# uniq ip address in c_ip"
	echo -n "complete   = " && 
	cat $dir/$ok | awk '{print $1}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq | wc -l

	echo -n "incomplete = " && 
	cat $dir/$error | awk '{print $1}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq | wc -l

	# number of uniq private ip address in c_ip
	echo "# uniq private ip address in c_ip"
	echo -n "complete   = " &&
	cat $dir/$ok | awk '{print $1}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq | grep -E "^10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | wc -l
	echo -n "incomplete = " &&
	cat $dir/$error | awk '{print $1}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq | grep -E "^10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | wc -l

	# number of uniq ip address in s_ip
	echo "# uniq ip address in s_ip"
	echo -n "complete   = " && 
	cat $dir/$ok | awk '{print $15}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq | wc -l

	echo -n "incomplete = " && 
	cat $dir/$error | awk '{print $15}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq | wc -l

	# number of uniq private ip address in s_ip
	echo "# uniq private ip address in s_ip"
	echo -n "complete   = " &&
	cat $dir/$ok | awk '{print $15}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq | grep -E "^10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | wc -l
	echo -n "incomplete = " &&
	cat $dir/$error | awk '{print $15}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq | grep -E "^10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | wc -l
}

###################
# dump_local_info #
###################
#echo "# dump_local.pcap #"
#show_flow_info "dump_local-20240514-00.pcap.out/2024_05_14_00_00.out"

####################
# dump_global_info #
####################
echo "# dump_global.pcap #"
show_flow_info "dump_global-20240514-00.pcap.out/2024_05_14_00_00.out"

#here
echo "here"

#ここで出てるのは

#c_ip
#これはまあまあ散らばっている
#cat $dir/$ok | awk '{print $1}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq -c | sort -nr -k1,1 | less

#c_ip
#これもそこそこ
#cat $dir/$error | awk '{print $1}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq -c | sort -nr -k1,1 | less

#s_ip
#これも219.????がそこそこ出てくる. ただ130....も出てくる. これは何??
cat $dir/$ok | awk '{print $15}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq -c | sort -nr -k1,1 | less

#s_ip
### これがvpnサーバかもしれない!!! csvリストに出てくるprefixが一致するipアドレがたくさん出てくる, 219.????がたくさん出てくる
#cat $dir/$error | awk '{print $15}' | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n -r | uniq -c | sort -nr -k1,1 | less


########################################
# get list of private ip in dump_local #
########################################
#echo "# extracting local ip address from c_ip #"
#./tool.sh 7 l >/dev/null
#echo -n "number of uniq private ip in local_dump.pcap c_ip = " && 
#cat all_uniq_privip.txt | wc -l
#echo "# local ip written to all_uniq_priv.txt #"

# number based on vlan
#sudo tcpdump -nner dump_local-20240514-00.pcap -c 100000 | awk '{print $10,$11}' | sort -nr | uniq -c | sort -nrk1,1 | less
