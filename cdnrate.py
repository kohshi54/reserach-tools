import sys

asnnamemp = {}
with open('ip2asn-v4.tsv', 'r') as file:
	for line in file:
		start_ip,end_ip,asn,country,name = line.split('\t')
		asnnamemp[asn] = name

nameratemp = {}
with open(sys.argv[1], 'r') as infile:
	for line in infile:
		asn,count,rate = line.split()
		try:
			nameratemp[asnnamemp[asn]] = float(rate)
			#print(f"{rate},{asnnamemp[asn]}", end='')
		except KeyError:
			continue
			#print(f"ASname not found for {asn}")

cdns = ("akamai", "cloudflare", "fastly", "amazon", "google", "microsoft", "tatacomm", "cdn77", "verizon", "gcore", "dataweb")
hosting = ("24shells")
content = ("bytedance", "facebook", "netflix", "telegram", "roblox")

#cdns += content

cdnratesum=0.0
for name,rate in nameratemp.items():
	for cdn in cdns:
		#print(f"{cdn}, {name.lower()}")
		if cdn in name.lower():
			print(name,end='')
			cdnratesum += rate
			break

print(f"cdnrate: {cdnratesum}")

