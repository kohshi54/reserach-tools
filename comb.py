import sys
import networkx as nx
#import numpy as np
import cupy as np
import multiprocessing as mp

""" 2^50 oom """
def create_all_combination(nodes):
	n = len(nodes)
	all_comb = []
	for i in range(1 << n):
		comb = []
		for j in range(n):
			if (i & (1 << j)):
				comb.append(nodes[j])
		all_comb.append(comb)
	return all_comb

def calculate_avg_path_length(G, userasns, serverasns, gravity, comb):
	print(comb)
	if comb:
		hopmx = calculate_hops_with_vpns(G, userasns, serverasns, comb)
	else:
		return (0,0)
		#hopmx = calculate_direct_path_length(G, userasns, serverasns)
	costmxvpn = hopmx * gravity
	"""
	hopsumvpn = np.sum(hopmx)
	elemnum = hopmx.size
	print(f"hopavgvpn: {hopsumvpn / elemnum}")
	print(f"gravitycostvpn: {np.sum(costmxvpn)}")
	return (hopsumvpn/elemnum,np.sum(costmxvpn))
	"""
	valid_hopmx = hopmx[(hopmx != 0)]
	valid_costmxvpn = costmxvpn[(costmxvpn != 0)]
	hopsumvpn = np.sum(valid_hopmx)
	valid_elemnum = valid_hopmx.size
	gravitycostvpn = np.sum(valid_costmxvpn)
	print(f"hopavgvpn: {hopsumvpn / valid_elemnum}")
	#print(f"hopavgvpn: {valid_hopmx.mean()}")
	print(f"gravitycostvpn: {gravitycostvpn}")
	print(f"validpathrate: {valid_hopmx.size/hopmx.size} (allpath:{hopmx.size},validpath:{valid_hopmx.size})")
	return (hopsumvpn/valid_elemnum, gravitycostvpn)

def write_file(comb, node_rank, length, weighted_length, outfilename):
	with open(outfilename, 'a') as outfile:
		nodes = ','.join(map(str, comb))
		ranks = ','.join(map(str, node_rank))
		outfile.write(f"relay({nodes}) relay({ranks}) {length} {weighted_length}\n")

def cal_hop(userasn, G, serverasn):
	if userasn in G and serverasn in G:
		try:
			return (userasn, serverasn, nx.shortest_path_length(G, source=userasn, target=serverasn))
		except nx.NetworkXNoPath:
			return (userasn, serverasn, None)
	else:
		return (userasn, serverasn, None)

def parallel_shortest_path_length(userasns, G, serverasns):
	with mp.Pool(int(mp.cpu_count()/2)) as pool:
		tasks = []
		for userasn in userasns:
			for serverasn in serverasns:
				tasks.append((userasn, G, serverasn))
		results = pool.starmap(cal_hop, tasks)
	
	#results_dict = {}
	results_dict = {userasn: {serverasn: 0 for serverasn in serverasns} for userasn in userasns}
	for result in results:
		userasn, serverasn, hops = result
		results_dict[userasn][serverasn] = hops
	
	return results_dict

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

def load_relay_nodes(vpnfile):
	relay_nodes = []
	with open(vpnfile, 'r') as nodes:
		for line in nodes:
			node = line.strip()
			relay_nodes.append(int(node))
	return relay_nodes

def calculate_direct_path_length(G, userasns, serverasns):
	"""
	hopmxvpn = np.zeros((len(userasns), len(serverasns)))
	for i,userasn in enumerate(userasns):
		if userasn in G:
			for j,serverasn in enumerate(serverasns):
				if serverasn in G:
					hopmx[i][j] = nx.shortest_path_length(G, source=userasn, target=serverasn)	
	"""

	hopmxvpn = np.zeros((len(userasns), len(serverasns)))
	c2shops = parallel_shortest_path_length(userasns, G, serverasns)
	hopmxvpn = np.array([
		[
			(c2shops[userasn][serverasn]) if userasn in G and serverasn in G else 0
			for serverasn in serverasns
		]
		for userasn in userasns
	])
	return hopmxvpn

def calculate_hops_with_vpns(G, userasns, serverasns, vpnasns):
	hopmxvpn = np.zeros((len(userasns), len(serverasns)))
	for i,userasn in enumerate(userasns):
		if userasn in G:
			for j,serverasn in enumerate(serverasns):
				if serverasn in G:
					min_length = float('inf')
					for node in vpnasns:
						try:
							c2v_length = nx.shortest_path_length(G, source=userasn, target=node)
							v2s_length = nx.shortest_path_length(G, source=node, target=serverasn)
							c2s_length = c2v_length + v2s_length
						except nx.NetworkXNoPath:
							c2s_length = float('inf')
						if c2s_length < min_length:
							min_length = c2s_length
					if min_length != float('inf'):
						hopmxvpn[i][j] = min_length
					else:
						hopmxvpn[i][j] = 0
					
	"""
	c2vpnhops = {}
	for userasn in userasns:
		if userasn in G:
			min_length = float('inf')
			for node in vpnasns:
				try:
					cur_length = nx.shortest_path_length(G, source=userasn, target=node)
				except nx.NetworkXNoPath:
					cur_length = float('inf')
				if (cur_length < min_length):
					min_length = cur_length
			if min_length != float('inf'):
				c2vpnhops[userasn] = min_length
			else:
				c2vpnhops[userasn] = None
	
	vpn2shops = {}
	for serverasn in serverasns:
		if serverasn in G:
			min_length = float('inf')
			for node in vpnasns:
				try:
					cur_length = nx.shortest_path_length(G, source=node, target=serverasn)
				except nx.NetworkXNoPath:
					cur_length = float('inf')
				if (cur_length < min_length):
					min_length = cur_length
			if (min_length != float('inf')):
				vpn2shops[serverasn] = min_length
			else:
				vpn2shops[serverasn] = None
	
	hopmxvpn = np.array([
		[
			(c2vpnhops[userasn] + vpn2shops[serverasn]) if c2vpnhops.get(userasn) and vpn2shops.get(serverasn) else 0
			for serverasn in serverasns
		]
		for userasn in userasns
	])
	"""
	"""
	for i, userasn in enumerate(userasns):
		for j, serverasn in enumerate(serverasns):
			if userasn in c2vpnhops and serverasn in vpn2shops:
				if c2vpnhops[userasn] and vpn2shops[serverasn]:
					hopmxvpn[i][j] = c2vpnhops[userasn] + vpn2shops[serverasn]
	"""

	#print_matrix(hopmxvpn)
	#print(f"hopsumvpn: {sum_matrix(hopmxvpn)}")
	return hopmxvpn

def main():
	aspaths = parse_aspath('../aspath.list')
	G = create_graph(aspaths)
	userasns, userrates = load_user_data('../vv.list.rate')
	serverasns, serverrates = load_server_data('../cc.list.rate')
	userrates = np.array(userrates)
	serverrates = np.array(serverrates)
	gravity = np.outer(userrates, serverrates)

	#length,weighted_length = calculate_avg_path_length(G, userasns, serverasns, gravity, [59103])
	#print(f"{length}, {weighted_length}")

	#"""
	nodes = load_relay_nodes('top1.txt')
	n = len(nodes)
	for i in range(1 << n):
		comb = []
		node_rank = []
		for j in range(n):
			if (i & (1 << j)):
				comb.append(nodes[j])
				node_rank.append(j+1)
		length,weighted_length = calculate_avg_path_length(G, userasns, serverasns, gravity, comb)
		write_file(comb, node_rank, length, weighted_length, 'kk.outfile')
	#"""

	""" oom(2^50 set of list is
	#nodes = (1, 2, 3, 4, 5)
	#nodes = [6939,3356]
	nodes = load_relay_nodes('top50.txt')
	all_comb = create_all_combination(nodes)
	for comb in all_comb:
		length,weighted_length = calculate_avg_path_length(G, userasns, serverasns, gravity, comb)
		write_file(comb, length, weighted_length)
		print(length, weighted_length)
	"""

if __name__ == '__main__':
	main()
