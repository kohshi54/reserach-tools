import pytricia
import ipaddress

ip2asn = pytricia.PyTricia()

# IP範囲とASNのマッピングデータをロード
with open('ip2asn-v4.tsv', 'r') as file:
	for line in file:
		parts = line.split('\t')
		start_ip, end_ip, asn, country, name = parts
		#print(start_ip, end_ip, asn, country, name)
		# CIDR表記を作成
		start_ipx = ipaddress.IPv4Address(start_ip)
		end_ipx = ipaddress.IPv4Address(end_ip)
		cidr_blocks = list(ipaddress.summarize_address_range(start_ipx, end_ipx))
		for cidr in cidr_blocks:
			ip2asn[cidr] = asn
			#print(f"Added CIDR: {cidr} with ASN: {asn}")

# テストするIPアドレスのリスト
test_ips = ["1.0.0.1", "1.0.1.1", "1.0.4.1", "1.0.16.1", "1.0.17.1"]

# 各IPアドレスに対してASNを取得
for ip in test_ips:
    try:
        asn = ip2asn[ip]
        print(f"The AS number for IP {ip} is {asn}")
    except KeyError:
        print(f"The AS number for IP {ip} is Not found")

