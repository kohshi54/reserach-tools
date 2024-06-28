import networkx as nx

with open('aspath.list', 'r') as file:
	lines = file.readlines()

def print_path(path):
	for asn in path:
		print(asn, end=" ")
	print()

def print_matrix(mx):
	for row in mx:
		for elem in row:
			print(elem, end=" ")
		print()

def sum_matrix(mx):
	sum = 0
	for row in mx:
		for elem in row:
			sum += elem
	return sum

def hop_avg(mx, mxvpn):
    gapsum = 0
    hopsum = 0
    hopsumvpn = 0
    for i in range(len(mx)):
        for j in range(len(mxvpn)):
            gap = mxvpn[i][j] - mx[i][j]
            print(gap, end=" ")
            gapsum += gap
            hopsum += mx[i][j]
            hopsumvpn += mxvpn[i][j]
        print()
    elemnum = len(mx) * len(mxvpn)
    print(f"hopavg: {hopsum / elemnum}")
    print(f"hopavgvpn: {hopsumvpn / elemnum}")
    print(f"gapavg: {gapsum / elemnum}")

print("extracte aspath")
as_paths = []
for line in lines:
	if line.startswith("ASPATH:"):
		path = line[len("ASPATH:"):].strip().split()
		base_path = []
		has_branch = False;
		prev_asn = None
		for asn in path:
			if '{' in asn and '}' in asn:
				has_branch = True
				asn_set = asn.strip('{}').split(',')
				for aa in asn_set:
					expanded_path = base_path + [int(aa)]
					as_paths.append(expanded_path)
					#print_path(expanded_path)
			else:
				asn_int = int(asn)
				if asn_int != prev_asn:
					base_path.append(asn_int)
					prev_asn = asn_int
		if not has_branch:
			as_paths.append(base_path)
			#print_path(base_path)

print("grpah")
G = nx.Graph()
for path in as_paths:
	for i in range(len(path) - 1):
		prev = path[i]
		cur = path[i + 1]
		G.add_edge(prev, cur)

print("user")
# user asn list
userasns = []
with open('userasn.list', 'r') as users:
	for line in users:
		#userasn,cnt,rate = line.strip().split()
		userasn,cnt = line.strip().split()
		userasns.append(int(userasn))

print("server")
# server asn list
serverasns = []
with open('serverasn.list', 'r') as servers:
	for line in servers:
		#serverasn,cnt,rate = line.strip().split()
		serverasn,cnt = line.strip().split()
		serverasns.append(int(serverasn))

print("hops")
"""
# get hops
if nx.has_path(G, 1234, 5678):
	hops = nx.shortest_path_length(G, srouce=1234, target=5678)
"""
# get hops
# no vpn
hopmx = [[0 for _ in range(len(serverasns))] for _ in range(len(userasns))]
for i in range(len(userasns)):
	for j in range(len(serverasns)):
		if userasns[i] in G and serverasns[j] in G:
			if nx.has_path(G, userasns[i], serverasns[j]):
				hops = nx.shortest_path_length(G, source=userasns[i], target=serverasns[j])
				hopmx[i][j] = hops
				#hopmx[i][j] = hops * rate

#print_matrix(hopmx)
print(f"hopsum: {sum_matrix(hopmx)}")

# with vpn
hopmxvpn = [[0 for _ in range(len(serverasns))] for _ in range(len(userasns))]
for i in range(len(userasns)):
	if userasns[i] in G:
		c2vpn = nx.shortest_path_length(G, source=userasns[i], target=59103)
		for j in range(len(serverasns)):
			if serverasns[j] in G:
				if nx.has_path(G, userasns[i], serverasns[j]):
					vpn2s = nx.shortest_path_length(G, source=59103, target=serverasns[j])
					hopmxvpn[i][j] = c2vpn + vpn2s
					#hopmxvpn[i][j] = (c2vpn + vpn2s) * rate

#print_matrix(hopmxvpn)
print(f"hopsumvpn: {sum_matrix(hopmxvpn)}")

hop_avg(hopmx, hopmxvpn)

