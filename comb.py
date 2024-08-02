import sys
import networkx as nx
#import numpy as np
import cupy as np
import multiprocessing as mp
from enum import Enum
#from memory_profiler import profile
import os
import json

alldetails = []

#@profile
def create_all_combination(nodes):
	n = len(nodes)
	for i in range(1 << n):
		comb = []
		node_rank = []
		for j in range(n):
			if (i & (1 << j)):
				comb.append(nodes[j])
				node_rank.append(j+1)
		yield comb, node_rank

#@profile
def calculate_avg_path_length(G, userasns, serverasns, gravity, comb):
	print(comb)
	if comb:
		hopmx = calculate_hops_with_vpns(G, userasns, serverasns, comb)
	else:
		#return (0,0)
		hopmx = calculate_direct_path_length(G, userasns, serverasns)
	costmxvpn = hopmx * gravity

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

	def outjson():
		pathdata = {}
		pathdata["relayset"] = list(comb)
		pathdata["hopavg"] = float(hopsumvpn/valid_elemnum)
		pathdata["weightedavg"] = float(gravitycostvpn)
		pathdata["pathinfo"] = {
			"validpathrate": float(valid_hopmx.size/hopmx.size),
			"allpath": int(hopmx.size),
			"validpath": int(valid_hopmx.size)
		}
		pathdata["pathlength"] = {}
		for length, count in zip(unique_pathlength, counts):
			pathdata["pathlength"][float(length)] = {"cnt": int(count), "rate": f"{float(count/valid_hopmx.size):.6f}"}
		alldetails.append(pathdata)

	outjson()

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
	ipcntbased = 4

def parallel_shortest_path_relay_nodes(userasns, G, serverasns, gravity, weightF=weightFlg.noweighted):
	with mp.Pool(int(mp.cpu_count()/2)) as pool:
		tasks = []
		for userasn in userasns:
			for serverasn in serverasns:
				tasks.append((userasn, G, serverasn))
		results = pool.starmap(cal_relay_nodes, tasks)

	uidxmp = {userasn: i for i,userasn in enumerate(userasns)}
	sidxmp = {serverasn: i for i,serverasn in enumerate(serverasns)}

	relay_nodes = {}
	for result in results:
		userasn,serverasn,node_list = result
		for node in node_list:
			if node == userasn or node == serverasn:
				continue
			if weightF == weightFlg.noweighted:
				relay_nodes[node] = relay_nodes.get(node, 0) + 1
			elif weightF in {weightFlg.pktsbased, weightFlg.pktsbased, weightFlg.pktsbased}:
				relay_nodes[node] = relay_nodes.get(node, 0.0) + gravity[uidxmp[userasn]][sidxmp[serverasn]]

	return relay_nodes

def readvpdata(vpdir):
	#vpfilelist = ['./vp/aspath.oregon.list', './vp/aspath.dixie.list', '/vp/aspath.amsix.list']
	vpfilelist = os.listdir(vpdir)
	print(vpfilelist)
#	for i in range(len(vpfilelist)):
#		vpfilelist[i] = os.path.join(vpdir, vpfilelist[i])
	vpfilelist = [os.path.join(vpdir, vpfname) for vpfname in vpfilelist]
	for aspathfile in vpfilelist:
		with open(aspathfile, 'r') as f:
			for line in f:
				yield line

def aspath_parser(line):
	if line.startswith("ASPATH:"):
		path = line[len("ASPATH:"):].strip().split()
		base_path = []
		prev_asn = None
		for asn in path:
			if '{' in asn and '}' in asn:
				asn_set = asn.strip('{}').split(',')
				for aa in asn_set:
					expanded_path = base_path + [int(aa)]
					yield expanded_path # expand ASPATH: 123 124 {125,126} -> (123 124 125), (123 124 126)
				return # stop iteration
			else:
				asn_int = int(asn)
				if asn_int != prev_asn:
					base_path.append(asn_int)
					prev_asn = asn_int
		yield base_path
	return # stop iteration

def add_path_to_graph(G, pathlist):
	for i in range(len(pathlist) - 1):
		prev = pathlist[i]
		cur = pathlist[i + 1]
		G.add_edge(prev, cur)

#@profile
def load_user_data(userfile, weightF=weightFlg.pktsbased):
	# user asn list
	userasns = []
	userrates = []
	with open(userfile, 'r') as users:
		for line in users:
			userasn,pktsnum,pktsrate,connnum,connrate,ipcntnum,ipcntrate = line.strip().split()
			userasns.append(int(userasn))
			if weightF == weightFlg.pktsbased:
				userrates.append(float(pktsrate))
			elif weightF == weightFlg.connbased:
				userrates.append(float(connrate))
			elif weightF == weightFlg.ipcntbased:
				userrates.append(float(ipcntrate))
	return userasns, userrates

#@profile
def load_server_data(serverfile, weightF=weightFlg.pktsbased):
	# server asn list
	serverasns = []
	serverrates = []
	with open(serverfile, 'r') as servers:
		for line in servers:
			serverasn,pktsnum,pktsrate,connnum,connrate,ipcntnum,ipcntrate = line.strip().split()
			serverasns.append(int(serverasn))
			if weightF == weightFlg.pktsbased:
				serverrates.append(float(pktsrate))
			elif weightF == weightFlg.connbased:
				serverrates.append(float(connrate))
			elif weightF == weightFlg.ipcntbased:
				serverrates.append(float(ipcntrate))
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

	#hopmxvpn = np.zeros((len(userasns), len(serverasns)))
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
	G = nx.Graph()
	for line in readvpdata('./../latest/vp/'): # uses yiled for lower memory usage (not loading all paths at once)
		for pathlist in aspath_parser(line):
			add_path_to_graph(G, pathlist)
	#print(f"{G.number_of_nodes()} {G.number_of_edges()}")

	weightF = weightFlg.pktsbased
	userasns, userrates = load_user_data('./userasn.pkts.conn.ipcnt.list', weightF)
	serverasns, serverrates = load_server_data('./serverasn.pkts.conn.ipcnt.list', weightF)
	gravity = np.outer(np.array(userrates), np.array(serverrates))

	#"""
	nodes = parallel_shortest_path_relay_nodes(userasns, G, serverasns, gravity, weightF)
	total = sum(nodes.values())
	top50_relay_nodes = sorted(nodes.items(), key = lambda x: x[1], reverse = True)[:50] # memory utility... use iter?
	with open('relay_nodes.pktsbased.list', 'w') as outfile:
		for node,cnt in top50_relay_nodes:
			outfile.write(f"{node} {cnt} {(cnt/total)*100}%\n")
	top5_relay_node_keys = [node for node,_ in top50_relay_nodes[:5]]
	#"""

	nodes = top5_relay_node_keys
	#nodes = load_relay_nodes('../top5withgravity/top5.txt')

	#"""
	for comb,node_rank in create_all_combination(nodes): # generator in use to avoid oom even when 2^50
		length,weighted_length = calculate_avg_path_length(G, userasns, serverasns, gravity, comb)
		write_file(comb, node_rank, length, weighted_length, 'allvp.outfile')
	#"""

	realvpnasn = 59103
	length,weighted_length = calculate_avg_path_length(G, userasns, serverasns, gravity, [realvpnasn])
	write_file([realvpnasn], [0], length, weighted_length, 'allvp.outfile')

	with open('./allvp.detail.json', 'w') as outf:
		#jsondata = json.dumps(alldetails)
		#print(jsondata)
		json.dump(alldetails, outf)

if __name__ == '__main__':
	main()
