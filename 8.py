import networkx as nx
import numpy as np

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

def sum_matrix_fast(mx):
	return np.sum(mx)

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

def hop_avg_fast(mx, mxvpn):
	gapsum = np.sum(mxvpn - mx)
	hopsum = np.sum(mx)
	hopsumvpn = np.sum(mxvpn)
	elemnum = mx.size
	print(f"hopavg: {hopsum / elemnum}")
	print(f"hopavgvpn: {hopsumvpn / elemnum}")
	print(f"gapavg: {gapsum / elemnum}")


with open('aspath.list', 'r') as file:
	lines = file.readlines()

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

"""
print(G.edges)
pos = nx.spring_layout(G)
nx.draw_networkx(G, pos, with_labels=True, alpha=0.5)
plt.axis("off")
plt.show()
"""

print("user")
# user asn list
userasns = []
userrates = []
with open('userasn.list', 'r') as users:
	for line in users:
		userasn,cnt,rate = line.strip().split()
		#userasn,cnt = line.strip().split()
		userasns.append(int(userasn))
		userrates.append(float(rate))

print("server")
# server asn list
serverasns = []
serverrates = []
with open('serverasn.list', 'r') as servers:
	for line in servers:
		serverasn,cnt,rate = line.strip().split()
		#serverasn,cnt = line.strip().split()
		serverasns.append(int(serverasn))
		serverrates.append(float(rate))

# cal weight user <-> server (gravity model)
# user ndarray for speed
"""
weightmx = [[0 for _ in range(len(serverasns))] for _ in range(len(userasns))]
for i in range(len(userasns)):
	for j in range(len(serverasns)):
		weightmx[i][j] = userrates[i] * serverrates[j]
gravitymx = [[0 for _ in range(len(serverasns))] for _ in range(len(userasns))]
"""
userrates = np.array(userrates)
serverrates = np.array(serverraets)
weightmx = np.outer(userrates, serverrates)
gravitymx = np.zeros_like(weightmx)

print("hops no vpn")
"""
# get hops
if nx.has_path(G, 1234, 5678):
	hops = nx.shortest_path_length(G, srouce=1234, target=5678)
"""
# get hops
# no vpn
"""
hopmx = [[0 for _ in range(len(serverasns))] for _ in range(len(userasns))]
for i in range(len(userasns)):
	for j in range(len(serverasns)):
		if userasns[i] in G and serverasns[j] in G:
			if nx.has_path(G, userasns[i], serverasns[j]):
				hopmx[i][j] = nx.shortest_path_length(G, source=userasns[i], target=serverasns[j])
				gravitymx[i][j] = hopmx[i][j] * weightmx[i][j]
"""
hopmx = np.zeros_like(weightmx)
for i, userasn in enumerate(userasns):
	for j, serverasn in enumerate(serverasns):
		if userasn in G and serverasn in G:
			if nx.has_path(G, userasn, serverasn):
				hopmx[i][j] = nx.shortest_path_length(G, source=userasn, target=serverasn)
				gravitymx[i][j] = hopmx[i][j] * weightmx[i][j]

#print_matrix(hopmx)
#print(f"hopsum: {sum_matrix(hopmx)}")

# with vpn
print("hops with vpn")
"""
hopmxvpn = [[0 for _ in range(len(serverasns))] for _ in range(len(userasns))]
for i in range(len(userasns)):
	if userasns[i] in G:
		c2vpn = nx.shortest_path_length(G, source=userasns[i], target=59103)
		for j in range(len(serverasns)):
			if serverasns[j] in G:
				if nx.has_path(G, userasns[i], serverasns[j]):
					vpn2s = nx.shortest_path_length(G, source=59103, target=serverasns[j])
					hopmxvpn[i][j] = c2vpn + vpn2s
					gravitymx = hopmxvpn[i][j] * weightmx[i][j]
"""
vpnasn = 59103
hopmxvpn = np.zeros_like(weightmx)
for i, userasn in enumerate(userasns):
	if userasn in G:
		if nx.has_path(G, userasn, vpnasn):
			c2vpn = nx.shortest_path_length(G, source=userasn, target=vpnasn)
			for j, serverasn in enumerate(serverasns):
				if serverasn in G:
					if nx.has_path(G, vpnasn, serverasn):
						vpn2s = nx.shortest_path_length(G, source=vpnasn, target=serverasn)
						hopmxvpn[i][j] = c2vpn + vpn2s
						gravitymx = hopmxvpn[i][j] * weightmx[i][j]

#print_matrix(hopmxvpn)
#print(f"hopsumvpn: {sum_matrix(hopmxvpn)}")

print("cal")
hop_avg_fast(hopmx, hopmxvpn)
print(f"gravitycost: {sum_matrix_fast(gravitymx)}")
