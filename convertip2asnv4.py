import pytricia
import ipaddress
import sys
import statistics

ip2asn = pytricia.PyTricia()

# make ip range <-> as map
with open('ip2asn-v4.tsv', 'r') as file:
	for line in file:
		parts = line.split('\t')
		start_ip, end_ip, asn, country, name = parts
		#print(start_ip, end_ip, asn, country, name)
		# make cidr(pytricia only accepts cidr desc)
		start_ipx = ipaddress.IPv4Address(start_ip)
		end_ipx = ipaddress.IPv4Address(end_ip)
		cidr_blocks = list(ipaddress.summarize_address_range(start_ipx, end_ipx))
		for cidr in cidr_blocks:
			ip2asn[cidr] = asn
			#print(f"Added CIDR: {cidr} with ASN: {asn}")

d = {}
f = {}
# map ip to AS and write to file
#with open('asn.list', 'w') as outfile:
with open(sys.argv[1], 'r') as infile:
	for line in infile:
		try:
			ip,ttl = line.split()
			#print('a', ip.strip(), 'a')
			#print('a', ip, 'a')
			#try:
			asn = ip2asn[ip]
			if asn in d:
				#d[asn] += float(rtt)
				#f[asn] += 1;
				d[asn].append(float(ttl))
			else:
				#d[asn] = float(rtt)
				#f[asn] = 1;
				d[asn] = [float(ttl)]
			#except ValueError as e:
			#	print(f"Error for IP: {ip}")
			#	print(f"ValueError: {e}")
			#	asn = 0
			#	continue
			#print(f"IP={ip}:ASN={asn}")
			#outfile.write(f"{asn}\n");
			#print(f"{asn} {cnt}");
		except KeyError:
			print(f"ASN not found for {ip}")
			#outfile.write(f"0\n");

def convert_ttl_to_hops(ttllist):
	for i,ttl in enumerate(ttllist):
		if 128 < ttl and ttl <= 255:
			ttllist[i] = 255 - ttl
		elif 64 < ttl and ttl <= 128:
			ttllist[i] = 128 - ttl
		elif ttl <= 64:
			ttllist[i] = 64 - ttl
	return ttllist

with open ('asnttl.list', 'w') as outfile:
	#for asn,rttsum in d.items():
	for asn,ttllist in d.items():
		#print(f"{asn} {num}")
		#avg_rtt = rttsum / f[asn];
		hoplist = convert_ttl_to_hops(ttllist)
		median_ttl = statistics.median(hoplist)
		#if median_ttl < 30:
		outfile.write(f"{asn} {median_ttl}\n");

