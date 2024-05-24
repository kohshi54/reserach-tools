import pytricia
import ipaddress

ip2asn = pytricia.PyTricia()

# make ip range - as map
with open('ip2asn-v4.tsv', 'r') as file:
	for line in file:
		parts = line.split('\t')
		start_ip, end_ip, asn, country, name = parts
		#print(start_ip, end_ip, asn, country, name)
		# make cidr
		start_ipx = ipaddress.IPv4Address(start_ip)
		end_ipx = ipaddress.IPv4Address(end_ip)
		cidr_blocks = list(ipaddress.summarize_address_range(start_ipx, end_ipx))
		for cidr in cidr_blocks:
			ip2asn[cidr] = asn
			#print(f"Added CIDR: {cidr} with ASN: {asn}")

# map ip to as and write to file
with open('asnlist.txt', 'w') as outfile:
	with open('iplist.txt', 'r') as infile:
		for line in infile:
			try:
				#print('a', line, 'a')
				ip = line.strip()
				#print('a', ip, 'a')
				asn = ip2asn[ip]
				print(f"The AS number for IP {ip} is {asn}")
				outfile.write(f"{asn}\n");
			except KeyError:
				print(f"The AS number for IP {ip} is Not found")
				outfile.write(f"0\n");
			
