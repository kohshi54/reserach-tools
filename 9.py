import networkx as nx
import numpy as np
#import cupy as np

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

def hop_avg_fast(mx, mxvpn):
	gapsum = np.sum(mxvpn - mx)
	hopsum = np.sum(mx)
	hopsumvpn = np.sum(mxvpn)
	elemnum = mx.size
	print(f"hopavg: {hopsum / elemnum}")
	print(f"hopavgvpn: {hopsumvpn / elemnum}")
	print(f"gapavg: {gapsum / elemnum}")

def parse_aspath(aspath_file):
	with open(aspath_file, 'r') as file:
		lines = file.readlines()

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
	return as_paths

def create_graph(as_paths):
	G = nx.Graph()
	for path in as_paths:
		for i in range(len(path) - 1):
			prev = path[i]
			cur = path[i + 1]
			G.add_edge(prev, cur)
	return G

def show_graph(G):
	print(G.edges)
	pos = nx.spring_layout(G)
	nx.draw_networkx(G, pos, with_labels=True, alpha=0.5)
	plt.axis("off")
	plt.show()

def load_user_data(userfile):
	# user asn list
	userasns = []
	userrates = []
	with open(userfile, 'r') as users:
		for line in users:
			userasn,cnt,rate = line.strip().split()
			#userasn,cnt = line.strip().split()
			userasns.append(int(userasn))
			userrates.append(float(rate))
	return userasns, userrates

def load_server_data(serverfile):
	# server asn list
	serverasns = []
	serverrates = []
	with open(serverfile, 'r') as servers:
		for line in servers:
			serverasn,cnt,rate = line.strip().split()
			#serverasn,cnt = line.strip().split()
			serverasns.append(int(serverasn))
			serverrates.append(float(rate))
	return serverasns, serverrates

def calculate_hops_gravity(G, userasns, userrates, serverasns, serverrates, weightmx):
	hopmx = np.zeros_like(weightmx)
	gravitymx = np.zeros_like(weightmx)
	for i, userasn in enumerate(userasns):
		for j, serverasn in enumerate(serverasns):
			if userasn in G and serverasn in G:
				if nx.has_path(G, userasn, serverasn):
					hopmx[i][j] = nx.shortest_path_length(G, source=userasn, target=serverasn)
	
	gravitymx = hopmx * weightmx

	#print_matrix(hopmx)
	#print(f"hopsum: {sum_matrix(hopmx)}")
	return hopmx, gravitymx

# with vpn
# optimized use cache
def calculate_hops_with_vpn_gravity(G, userasns, userrates, serverasns, serverrates, weightmx):
	gravitymxvpn = np.zeros_like(weightmx)
	vpnasn = 59103
	hopmxvpn = np.zeros_like(weightmx)
	c2vpnhops = {}
	for userasn in userasns:
		if userasn in G:
			try:
				c2vpnhops[userasn] = nx.shortest_path_length(G, source=userasn, target=vpnasn)
			except nx.NetworkXNoPath:
				c2vpnhops[userasn] = None
	
	vpn2shops = {}
	for serverasn in serverasns:
		if serverasn in G:
			try:
				vpn2shops[serverasn] = nx.shortest_path_length(G, source=vpnasn, target=serverasn)
			except nx.NetworkXNoPath:
				vpn2shops[serverasn] = None
	
	for i, userasn in enumerate(userasns):
		for j, serverasn in enumerate(serverasns):
			if userasn in c2vpnhops and serverasn in vpn2shops:
				if c2vpnhops[userasn] and vpn2shops[serverasn]:
					hopmxvpn[i][j] = c2vpnhops[userasn] + vpn2shops[serverasn]
	
	gravitymxvpn = hopmxvpn * weightmx

	#print_matrix(hopmxvpn)
	#print(f"hopsumvpn: {sum_matrix(hopmxvpn)}")
	return hopmxvpn, gravitymxvpn

def main():
	print("extracte aspath")
	aspaths = parse_aspath('aspath.list')
	print("grpah")
	G = create_graph(aspaths)
	#show_graph(G)
	print("user")
	userasns, userrates = load_user_data('userasn.list')
	print("server")
	serverasns, serverrates = load_server_data('serverasn.list')

	# cal weight user <-> server (gravity model)
	# use ndarray for speed
	userrates = np.array(userrates)
	serverrates = np.array(serverrates)
	weightmx = np.outer(userrates, serverrates)

	# get hops
	print("hops")
	hopmx, gravitymx = calculate_hops_gravity(G, userasns, userrates, serverasns, serverrates, weightmx)
	print("hops with vpn")
	hopmxvpn, gravitymxvpn = calculate_hops_with_vpn_gravity(G, userasns, userrates, serverasns, serverrates, weightmx)

	print("cal")
	hop_avg_fast(hopmx, hopmxvpn)
	print(f"gravitycost: {sum_matrix_fast(gravitymx)}")
	print(f"gravitycostvpn: {sum_matrix_fast(gravitymxvpn)}")

if __name__ == '__main__':
	main()

