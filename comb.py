import sys
import networkx as nx
#import numpy as np
import cupy as np
import multiprocessing as mp
from enum import Enum
#from memory_profiler import profile

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

#@profile
def calculate_avg_path_length(G, userasns, serverasns, gravity, comb):
	print(comb)
	if comb:
		hopmx = calculate_hops_with_vpns(G, userasns, serverasns, comb)
	else:
		return (0,0)
		hopmx = calculate_direct_path_length(G, userasns, serverasns)
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

	unique_pathlength, counts = np.unique(valid_hopmx, return_counts=True)
	print(f"path length")
	for length, count in zip(unique_pathlength, counts):
		print(f"{length}:{count} ({(count/valid_hopmx.size):.20f})")
	return (hopsumvpn/valid_elemnum, gravitycostvpn)

def write_file(comb, node_rank, length, weighted_length, outfilename):
	with open(outfilename, 'a') as outfile:
		nodes = ','.join(map(str, comb))
		ranks = ','.join(map(str, node_rank))
		outfile.write(f"relay({nodes}) relay({ranks}) {length} {weighted_length}\n")

#@profile
def cal_hop(userasn, G, serverasn):
	if userasn in G and serverasn in G:
		try:
			return (userasn, serverasn, nx.shortest_path_length(G, source=userasn, target=serverasn))
		except nx.NetworkXNoPath:
			return (userasn, serverasn, None)
	else:
		return (userasn, serverasn, None)

#@profile
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

#@profile
def cal_relay_nodes(userasn, G, serverasn):
	if userasn in G and serverasn in G:
		try:
			return (userasn, serverasn, nx.shortest_path(G, source=userasn, target=serverasn))
		except nx.NetworkXNoPath:
			return (userasn, serverasn, [])
	else:
		return (userasn, serverasn, [])

class weightFlg(Enum):
	noweighted = 1
	pktsbased = 2
	connbased = 3

def parallel_shortest_path_relay_nodes(userasns, G, serverasns, gravity, weightF=weightFlg.noweighted):
	with mp.Pool(int(mp.cpu_count()/2)) as pool:
		tasks = []
		for userasn in userasns:
			for serverasn in serverasns:
				tasks.append((userasn, G, serverasn))
		results = pool.starmap(cal_relay_nodes, tasks)

	relay_nodes = {}
	for result in results:
		userasn,serverasn,node_list = result
		for node in node_list:
			if node in relay_nodes:
				if weightF == weightFlg.noweighted:
					relay_nodes[node] += 1
				elif weightF == weightFlg.pktsbased:
					relay_nodes[node] += gravity[userasn][serverasn] # not working userasn/serverasn should be index
				elif weightF == weightFlg.connbased:
					relay_nodes[node] += gravity[userasn][serverasn] # not working userasn/serverasn should be index
			else:
				if weightF == weightFlg.noweighted:
					relay_nodes[node] = 1
				elif weightF == weightFlg.pktsbased:
					relay_nodes[node] = gravity[userasn][serverasn] # not working userasn/serverasn should be index
				elif weightF == weightFlg.connbased:
					relay_nodes[node] = gravity[userasn][serverasn] # not working userasn/serverasn should be index

	return relay_nodes

#@profile
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

#@profile
def create_graph(as_paths):
	G = nx.Graph()
	for path in as_paths:
		for i in range(len(path) - 1):
			prev = path[i]
			cur = path[i + 1]
			G.add_edge(prev, cur)
	return G

#@profile
def load_user_data(userfile, weightF=weightFlg.pktsbased):
	# user asn list
	userasns = []
	userrates = []
	with open(userfile, 'r') as users:
		for line in users:
			userasn,pktsnum,pktsrate,connnum,connrate = line.strip().split()
			#userasn,cnt = line.strip().split()
			userasns.append(int(userasn))
			if weightF == weightFlg.pktsbased:
				userrates.append(float(pktsrate))
			elif weightF == weightFlg.connbased:
				userrates.append(float(connrate))
	return userasns, userrates

#@profile
def load_server_data(serverfile, weightF=weightFlg.pktsbased):
	# server asn list
	serverasns = []
	serverrates = []
	with open(serverfile, 'r') as servers:
		for line in servers:
			serverasn,pktsnum,pktsrate,connnum,connrate = line.strip().split()
			#serverasn,cnt = line.strip().split()
			serverasns.append(int(serverasn))
			if weightF == weightFlg.pktsbased:
				serverrates.append(float(pktsrate))
			elif weightF == weightFlg.connbased:
				userrates.append(float(connrate))
	return serverasns, serverrates

#@profile
def load_relay_nodes(vpnfile):
	relay_nodes = []
	with open(vpnfile, 'r') as nodes:
		for line in nodes:
			node = line.strip()
			relay_nodes.append(int(node))
	return relay_nodes

#@profile
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

#@profile
def calculate_path_length_via_single_vpn(G, userasns, serverasns, vpn):
	c2vpnhops = {}
	for userasn in userasns:
		if userasn in G:
			try:
				c2vpnhops[userasn] = nx.shortest_path_length(G, source=userasn, target=vpn)
			except nx.NetworkXNoPath:
				c2vpnhops[userasn] = None
	
	vpn2shops = {}
	for serverasn in serverasns:
		if serverasn in G:
			try:
				vpn2shops[serverasn] = nx.shortest_path_length(G, source=vpn, target=serverasn)
			except nx.NetworkXNoPath:
				vpn2shops[serverasn] = None

	hopmxvpn = np.array([
		[
			(c2vpnhops[userasn] + vpn2shops[serverasn]) if c2vpnhops.get(userasn) and vpn2shops.get(serverasn) else 0
			for serverasn in serverasns
		]
		for userasn in userasns
	])
	return hopmxvpn

#@profile
def calculate_hops_with_vpns(G, userasns, serverasns, vpnasns):
	hopmxvpn = np.full((len(userasns), len(serverasns)), float('inf'))
	for node in vpnasns:
		node_hopmx = calculate_path_length_via_single_vpn(G, userasns, serverasns, node)
		hopmxvpn = np.minimum(hopmxvpn, node_hopmx)
	hopmxvpn[hopmxvpn == float('inf')] = 0
	return hopmxvpn

#@profile
def main():
	aspaths = parse_aspath('./vp/aspath.allvp.list')
	G = create_graph(aspaths)
	userasns, userrates = load_user_data('./userasn.pkts.conn.list', weightFlg.pktsbased)
	serverasns, serverrates = load_server_data('./serverasn.pkts.conn.list', weightFlg.pktsbased)
	userrates = np.array(userrates)
	serverrates = np.array(serverrates)
	gravity = np.outer(userrates, serverrates)

	"""
	nodes = parallel_shortest_path_relay_nodes(userasns, G, serverasns, gravity, weightFlg.noweighted)
	with open('relay_nodes.noweighted.list', 'a') as outfile:
		for node,cnt in nodes.items():
			outfile.write(f"{node} {cnt}\n")
	"""

	realvpnasn = 59103
	length,weighted_length = calculate_avg_path_length(G, userasns, serverasns, gravity, [realvpnasn])
	write_file([realvpnasn], [0], length, weighted_length, 'test.allvp.outfile')

	#"""
	nodes = load_relay_nodes('../top5withgravity/top5.txt')
	n = len(nodes)
	for i in range(1 << n):
		comb = []
		node_rank = []
		for j in range(n):
			if (i & (1 << j)):
				comb.append(nodes[j])
				node_rank.append(j+1)
		length,weighted_length = calculate_avg_path_length(G, userasns, serverasns, gravity, comb)
		write_file(comb, node_rank, length, weighted_length, 'test.allvp.outfile')
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
