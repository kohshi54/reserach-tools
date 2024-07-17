import sys
import networkx as nx
#import numpy as np
import cupy as np

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
	#if comb:
		#hopmx = calculate_hops_with_vpns(G, userasns, serverasns, comb)
	#else:
	hopmx = calculate_hops_with_vpns(G, userasns, serverasns, comb)
	costmxvpn = hopmx * gravity
	hopsumvpn = np.sum(hopmx)
	elemnum = hopmx.size
	print(f"hopavgvpn: {hopsumvpn / elemnum}")
	print(f"gravitycostvpn: {np.sum(costmxvpn)}")
	return (hopsumvpn/elemnum,np.sum(costmxvpn))

def write_file(comb, length, weighted_length, outfilename):
	with open(outfilename, 'a') as outfile:
		nodes = ','.join(map(str, comb))
		outfile.write(f"relay({nodes}) {length} {weighted_length}\n")

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

def calculate_hops_with_vpns(G, userasns, serverasns, vpnasns):
	hopmxvpn = np.zeros((len(userasns), len(serverasns)))
	c2vpnhops = {}
	for userasn in userasns:
		if userasn in G:
			try:
				min_length = float('inf')
				for node in vpnasns:
					cur_length = nx.shortest_path_length(G, source=userasn, target=node)
					if (cur_length < min_length):
						min_length = cur_length
				c2vpnhops[userasn] = min_length
			except nx.NetworkXNoPath:
				c2vpnhops[userasn] = None
	
	vpn2shops = {}
	for serverasn in serverasns:
		if serverasn in G:
			try:
				min_length = float('inf')
				for node in vpnasns:
					cur_length = nx.shortest_path_length(G, source=node, target=serverasn)
					if (cur_length < min_length):
						min_length = cur_length
				vpn2shops[serverasn] = min_length
			except nx.NetworkXNoPath:
				vpn2shops[serverasn] = None
	
	hopmxvpn = np.array([
		[
			(c2vpnhops[userasn] + vpn2shops[serverasn]) if c2vpnhops.get(userasn) and vpn2shops.get(serverasn) else 0
			for serverasn in serverasns
		]
		for userasn in userasns
	])
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

	nodes = load_relay_nodes('top50.txt')
	n = len(nodes)
	for i in range(1 << n):
		comb = []
		for j in range(n):
			if (i & (1 << j)):
				comb.append(nodes[j])
		length,weighted_length = calculate_avg_path_length(G, userasns, serverasns, gravity, comb)
		write_file(comb, length, weighted_length, 'outfile')

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
