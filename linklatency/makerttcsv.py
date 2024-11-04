"""
params: arvv[1]=iplatency.list, argv[2]=outputfilename
input: ipaddress, latencyのリスト
output: CU,ASN,ASname,ipaddr,server/cli,rttのリスト(ipは重複する)（ゆくゆくはtimestampも追加する）
"""

import pytricia
import sys
import csv
import ipaddress
import pandas as pd

#iprange2pathlength = pytricia.PyTricia()
#iprange2asn = pytricia.PyTricia()
ip2asn = pytricia.PyTricia()
asn2name = {}

# make ip range <-> as map
with open('../ip2asn-v4.tsv', 'r') as file:
	for line in file:
		parts = line.split('\t')
		start_ip, end_ip, asn, country, name = parts
		asn2name[asn] = (name.strip().replace(",", "").replace(" ", "-"), country.strip())
		# make cidr(pytricia only accepts cidr desc)
		start_ipx = ipaddress.IPv4Address(start_ip)
		end_ipx = ipaddress.IPv4Address(end_ip)
		cidr_blocks = list(ipaddress.summarize_address_range(start_ipx, end_ipx))
		for cidr in cidr_blocks:
			ip2asn[cidr] = asn
			#print(f"Added CIDR: {cidr} with ASN: {asn}")p

"""
reduce AS path prepending
"""
# def remove_dup(paths):
# 	uniqpaths = []
# 	for i,path in enumerate(paths):
# 		if (i == 0):
# 			uniqpaths.append(path)
# 			continue
# 		if (paths[i - 1] != paths[i]):
# 			uniqpaths.append(path)
# 	return uniqpaths

# with open('fullroute_ipv4.csv', 'r') as fullf:
# 	lines = csv.reader(fullf)
# 	for line in lines:
# 		iprange,subnet,asn,path = line
# 		#print(f"{iprange=} {subnet=} {asn=} {path=}")
# 		cidr = iprange + "/" + subnet
# 		#print(f"{cidr=}")
# 		paths = path.split()
# 		#print(max(len(paths) - 1, 0))
# 		#ASPP kami sinai
# 		#iprange2pathlength[cidr] = max(len(paths) - 1, 0)
# 		#ASPP wo kouryo
# 		print(f"bef = {paths}")
# 		uniqpaths = remove_dup(paths)
# 		print(f"aft = {uniqpaths}")
# 		#iprange2pathlength[cidr] = max(len(uniqpaths) - 1, 0)
# 		iprange2asn[cidr] = asn
#"""
input_csv = sys.argv[1]
output_csv = sys.argv[2]

latency_df = pd.read_csv(input_csv)
output_data = []
err_count = 0
for index,row in latency_df.iterrows():
	ipaddr = row['ipaddr']
	rtt = row['rtt']
	syntime = row['syntime(ms)']
	synacktime = row['synacktime(ms)']
	try:
		curasn = ip2asn[ipaddr]
		curname = asn2name[curasn][0]
		curcu = asn2name[curasn][1]
		output_data.append([curcu, curasn, curname, ipaddr, 'client', syntime, synacktime, rtt])
	except KeyError:
		err_count += 1

output_df = pd.DataFrame(output_data, columns=['country', 'asn', 'asname', 'ipaddr', 's/c', 'syntime(ms)', 'synacktime(ms)', 'rtt'])
output_df.to_csv(output_csv, index=False)
#"""
"""
with open(sys.argv[1], 'r') as iplatencyf:
	with open(sys.argv[2], 'w') as outfile:
		outfile.write("cu,asn,name,ipaddr,s/c,rtt\n")
		for line in iplatencyf:
			ipaddr,rtt= line.split()
			#print(f"{ip=} {latency=}")
			try:
				#curpathlength = iprange2pathlength[ip]
				curasn = ip2asn[ipaddr]
				curname = asn2name[curasn][0]
				curcu = asn2name[curasn][1]
				outfile.write(f"{curcu},{curasn},{curname},{ipaddr},{'server'},{rtt}\n")
				#outfile.write(f"{asn} {curpathlength} {latency}\n")
			except KeyError:
				print(f"ip range not found for {ip}")
"""
