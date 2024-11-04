"""
odroute = 23363, linklist = 2267
[[0. 0. 0. ... 0. 0. 0.]
 [0. 0. 0. ... 0. 0. 0.]
  [0. 0. 0. ... 0. 0. 0.]
   ...
    [0. 0. 0. ... 0. 0. 0.]
	 [0. 0. 0. ... 0. 0. 0.]
	  [0. 0. 0. ... 0. 0. 0.]]
	  row=23363 col=2267
"""

import numpy as np
#import networkx as nx
from scipy.optimize import nnls
from sklearn.linear_model import Lasso
import networkx as nx
import os
import pytricia
import ipaddress
import sys
from scipy.optimize import minimize
from sklearn.linear_model import Ridge
import pandas as pd
import csv

ip2asn = pytricia.PyTricia()

# make ip range <-> as map
with open('../ip2asn-v4.tsv', 'r') as file:
	for line in file:
		parts = line.split('\t')
		start_ip, end_ip, asn, country, name = parts
		# make cidr(pytricia only accepts cidr desc)
		start_ipx = ipaddress.IPv4Address(start_ip)
		end_ipx = ipaddress.IPv4Address(end_ip)
		cidr_blocks = list(ipaddress.summarize_address_range(start_ipx, end_ipx))
		for cidr in cidr_blocks:
			ip2asn[cidr] = asn
			#print(f"Added CIDR: {cidr} with ASN: {asn}")

odlatency = [] #o2dlatencyのりすと
#odlatency = {}
odidx = {} #od(ipaddr)のレイテンシのodlatency内のインデックス
# def load_odlatency():
# 	with open("../serverminrtt.csv") as f:
# 		lines = f.readlines()
# 		for i,line in enumerate(lines):
# 			od,latency = line.split()
# 			print(f"{od=}, {latency=}")
# 			odlatency.append(latency)
# 			#odlatency[od] = latency
# 			odidx[od] = i

def load_odlatency():
	with open("./serverminrtt.csv", newline='') as f:
		reader = csv.reader(f)
		for i, row in enumerate(reader):
			od, latency = row
			print(f"{od=}, {latency=}")
			odlatency.append(latency)
			odidx[od] = i


load_odlatency()

"""test
"""
test_paths = {'a': [('a','b'), ('b', 'c'), ('c', 'd')],
				'b': [('b', 'c'), ('c', 'd')],
				'c': [('c', 'd')],
				'e': [('e', 'd')]}

test_paths2 = {'a': ['a', 'b', 'c', 'd'],
				'b': ['b','c','d'],
				'c': ['c', 'd'],
				'e': ['e', 'd']}

odpathlist = {}
def load_odpathlist():
	with open("../latest4/odpathlist.real.od-ip.nodup.list", 'r') as f:
		lines = f.readlines()
		for line in lines:
			od, *path = line.split()
			print(f"{od=}, {path=}")
			odpathlist[od] = path

load_odpathlist()

G = nx.Graph()
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

def aspath_parser2(line):
	path = line.strip().split()
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

def add_path_to_graph(G, pathlist):
	for i in range(len(pathlist) - 1):
		prev = pathlist[i]
		cur = pathlist[i + 1]
		G.add_edge(prev, cur)

for line in readvpdata('../latest3/vp/'): # only oregon
	for pathlist in aspath_parser(line):
		add_path_to_graph(G, pathlist)
#for line in readvpdata('../../latest3/softethervp'):
#	for pathlist in aspath_parser2(line):
#		add_path_to_graph(G, pathlist)

linkset = set()
linklist = []
linkidx = {}
odroute = {}
def make_linklist():
	for od in odidx.keys():
		#paths = nx.shortest_path(G, 59103, server)
		#paths = test_paths2[server]
		try:
			paths = odpathlist[od]
		except:
			destasn = ip2asn[od]
			paths = nx.shortest_path(G, 59103, destasn )
		#route = test_paths[server]
		route = [] # {(a,b), (b,c), (c,d)}
		# AS間遅延 {(a,b),(b,c),(c,d)}
		#for i in range(len(paths) - 1):
		#	route.append((paths[i], paths[i + 1]))
		# AS内遅延 {(a,a),(b,b),(c,c)}
		for i in range(len(paths)):
			route.append((paths[i], paths[i]))
		# AS間遅延+AS内遅延 {(a,a),(a,b),(b,b),(b,c),(c,c)}
		#print(paths)
		#print(len(paths))
		#for i in range(len(paths)):
		#	route.append((paths[i], paths[i]))
		#	if i != (len(paths) - 1):
		#		route.append((paths[i], paths[i + 1]))

		odroute[od] = route
		#print(route)
		linkset.update(route)

	#print(linkset)
	linklist = list(linkset)
	#print(f"{linklist=}")
	for i,link in enumerate(linklist):
		#print(link, i)
		linkidx[link] = i
	#print(f"linklist = {len(linklist)}")
	return linklist

linklist = make_linklist()
print(f"{odroute=}")
#print(f"\n\n{linklist=}")
print(f"{linkset=}")
routemx = np.zeros((len(odroute), len(linklist)))
print(f"odroute = {len(odroute)}, linklist = {len(linklist)}")
#print(routemx)

odpairs = odroute.keys()

def fill_routemx():
	for od in odpairs:
		route = odroute[od]
		try:
			for link in route:
				routemx[odidx[od]][linkidx[link]] = 1
		except:
			continue

fill_routemx()

df_routing = pd.DataFrame(routemx, index=odpairs, columns=linklist)
print(routemx)

#inv_routemx = np.linalg.pinv(routemx)
#print(inv_routemx)

#np.savetxt('negativecheck.out', inv_routemx, delimiter=',')

#print(odlatency)
#linklatency = np.dot(inv_routemx, np.array(odlatency, dtype='float'))
#such that x > 0
#linklatency, residual = nnls(routemx, np.array(odlatency, dtype='float'))
#print(residual)

row,col = routemx.shape
print(f"{row=} {col=}")

df_routing.to_csv('routing_matrix2.csv')


# #nnls
# #linklatency, residual = nnls(routemx, np.array(odlatency, dtype='float'), maxiter=9*row)
# #print(residual)
# #print(linklatency)

# ##l-bfgs-b
# #odlatency = np.array(odlatency, dtype='float64')
# #def objective(linklatency):
# #    return np.linalg.norm(routemx @ linklatency - odlatency)**2
# #
# ## 初期解を0で設定
# #linklatency_initial = np.zeros(col)
# #
# ## 非負制約を設定（リンク遅延は0以上）
# #bounds = [(0, None)] * col
# #
# ## L-BFGS-B法で最適化を実行
# #result = minimize(objective, linklatency_initial, bounds=bounds, method='L-BFGS-B', options={'maxiter': 9*row})
# #
# ## 結果の出力
# #linklatency = result.x
# #residual = result.fun
# #print(f"Residual: {residual}")
# #print(f"Link Latency: {linklatency}")
# #
# ## 結果をファイルに保存
# #with open('linklatency.real.inas.lbfgsb.list', 'w') as out:
# #    for i, link in enumerate(linklist):
# #	        out.write(f"{link} {linklatency[i]:.8f}\n")
# #

# # リッジ回帰モデルの作成
# odlatency = np.array(odlatency, dtype='float64')
# model = Ridge(alpha=0.1, positive=True)  # alpha=0.1で正則化の強さを設定し、非負制約を有効化
# model.fit(routemx, odlatency)

# # 解（リンク遅延）を取得
# linklatency = model.coef_

# # 結果の保存
# with open('linklatency.real.inas.ridge.list', 'w') as out:
#     for i, link in enumerate(linklist):
# 	        out.write(f"{link} {linklatency[i]:.8f}\n")
