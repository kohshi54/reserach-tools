"""
params:	arvv[1]=serverrtt.csv, argv[2]=serverasnrtt.csv
input:	ipaddr,rtt,syntime(ms),synacktime(ms),rtt2のリスト
output:	CU,ASN,ASname,ipaddr,server/cli,syntime(ms),synacktime(ms),rttのリスト(ipは重複する)
"""

import pytricia
import sys
import csv
import ipaddress
import pandas as pd

ip2asn = pytricia.PyTricia()
asn2name = {}

# make ip range <-> as map
with open('./data/ip2asn-v4.tsv', 'r') as file:
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

