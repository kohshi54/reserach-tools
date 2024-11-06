'''
input: serverasnrtt.csv
output: routing_matrix.csv

x.x.x.x : [[59103, 59103], [59103, 2907], [2907, 2907], [2907, 20940], [20940, x.x.x.x]] 

'''

import pandas as pd
import pytricia

iprange2path = pytricia.PyTricia()

"""
reduce AS path prepending
"""
def remove_dup(aspath):
	uniqpath = []
	for i,asn in enumerate(aspath):
		if (i == 0):
			uniqpath.append(asn)
			continue
		if (aspath[i - 1] != aspath[i]):
			uniqpath.append(asn)
	return uniqpath

def make_edge(aspath):
	edges = []
	for i,asn in enumerate(aspath):
		if (i != 0):
			edges.append((aspath[i - 1], asn))
		edges.append((asn, asn))
	return edges

'''
iprangeとパスの対応を作る
'''
fullroute_ipv4_df = pd.read_csv('./fullroute_ipv4.csv', skiprows=5)
for i,col in fullroute_ipv4_df.iterrows():
	iprange = col['#NetworkAddress']
	subnet = col['SubnetLength']
	aspath = col['AS_PATH'].split()
	cidr = iprange + "/" + str(subnet)
	# print(cidr)
	uniqpath = remove_dup(aspath)
	# iprange2path[cidr] = uniqpath
	iprange2path[cidr] = make_edge(aspath)

def get_path(ipaddr):
	try:
		#return iprange2path[row['ipaddr']] # +(dstasn,ipaddr) or (s/(dstasn,dstasn)/(dstasn,ipaddr)/) 
		edges = iprange2path[ipaddr].copy()
		print(ipaddr)
		print(f"bef {edges}")
		edges[-1] = (edges[-1][0], ipaddr) # s/(dstasn,dstasn)/(dstasn,ipaddr)/ <-これはAS内での個別のサブネット内で同一のipaddr毎に別になっちゃうのでよくない？あと検索しづらい
		print(f"aft {edges}")
		return tuple(edges)
	except KeyError:
		return None

#serverasnrtt_df = pd.read_csv('serverasnrtt.csv')
serverasnrtt_df = pd.read_csv('clientasnrtt.csv')
# 重複を削除
od_df = serverasnrtt_df['ipaddr'].drop_duplicates()

# DataFrame に戻して path 列を作成
od_df = pd.DataFrame(od_df)
od_df['path'] = od_df['ipaddr'].apply(get_path)

# path 列が None でない行のみを抽出
od_df = od_df.dropna(subset=['path'])


exploded_df = od_df.explode('path')
# 各エッジごとにワンホットエンコーディング
encoded_df = pd.get_dummies(exploded_df['path'])
# 元のインデックスで集約し、エッジの存在を 0/1 で表現
expanded_df = exploded_df[['ipaddr']].join(encoded_df).groupby(level=0).max()

#expanded_df = expanded_df.astype(int)
print(expanded_df)

expanded_df.to_csv('routing_matrix3.csv', index=False)
