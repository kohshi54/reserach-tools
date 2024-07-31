import pytricia
import ipaddress
import sys
from collections import defaultdict

ip2asn = pytricia.PyTricia()

# make ip range <-> as map
with open('../ip2asn-v4.tsv', 'r') as file:
	for line in file:
		parts = line.split('\t')
		start_ip, end_ip, asn, country, name = parts
		# make cidr(pytricia only accepts cidr desc)
		start_ipx = ipaddress.IPv4Address(start_ip)
		end_ipx = ipaddress.IPv4Address(end_ip)
		cidr_blocks = list(ipaddress.summarize_address_range(start_ipx, end_ipx))
		for cidr in cidr_blocks:
			ip2asn[cidr] = asn
			#print(f"Added CIDR: {cidr} with ASN: {asn}")

# map ip to AS and write to file
unitpkts = defaultdict(int)
unitconn = defaultdict(int)
unitipcnt = defaultdict(int)
errorcnt = 0
with open(sys.argv[1], 'r') as infile:
	for line in infile:
		ip,pkts,conn = line.split()
		try:
			if asn := ip2asn.get(ip):
				unitpkts[asn] += int(pkts)
				unitconn[asn] += int(conn)
				unitipcnt[asn] += 1
		except KeyError:
			print(f"ASN not found for {ip}")
			errorcnt += 1

totalpkts = sum(unitpkts.values())
totalconn = sum(unitconn.values())
totalipcnt = sum(unitipcnt.values())

print(f"{totalipcnt=} {errorcnt=}")
with open (sys.argv[2], 'w') as outfile:
	for asn in unitpkts.keys():
		pktsnum = unitpkts[asn]
		connnum = unitconn[asn]
		ipnum = unitipcnt[asn]
		outfile.write(f"{asn} {pktsnum} {(pktsnum / totalpkts):.20f} {connnum} {(connnum / totalconn):.20f} {ipnum} {(ipnum / totalipcnt):.20f}\n");

