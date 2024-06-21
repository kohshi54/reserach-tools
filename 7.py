import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

print("get all node from file start")
#with open('aspath.list', 'r') as file:
with open('aspath50.list', 'r') as file:
    lines = file.readlines()
print("get all node from file end")

print("extracting aspath start")
as_paths = []
for line in lines:
    if line.startswith("ASPATH:"):
        path = line[len("ASPATH:"):].strip().split()
        expanded_path = []
        for asn in path:
            if '{' in asn and '}' in asn:
                asn_set = asn.strip('{}').split(',')
                expanded_path.extend(int(asn.strip()) for asn in asn_set)
            else:
                expanded_path.append(int(asn))
        as_paths.append(expanded_path)
print("extracting aspath end")

print("create graph start")
G = nx.Graph()

print("adding node and edge from aspathlist")
for path in as_paths:
    for i in range(len(path) - 1):
        if path[i] != path[i + 1]:  # 自己ループを避ける
            G.add_edge(path[i], path[i + 1])


print("get nodes to highlight in myasn.list")
highlight_asns = []
#with open('userasn.list', 'r') as file:
#with open('serverasn.list', 'r') as file:
with open('serverasn50.list', 'r') as file:
    highlight_asns = [int(line.strip()) for line in file if line.strip().isdigit()]

#print("calculating shortest path from ...")
## 2907から各ハイライトノードへの最短経路を取得
#paths_from_2907 = {}
#for target in highlight_asns:
#    if target != 2907 and target in G.nodes:  # 自分自身および存在しないノードへの経路は無視
#        try:
#            path = nx.shortest_path(G, source=2907, target=target)
#            paths_from_2907[target] = path
#        except nx.NetworkXNoPath:
#            continue
#
## 経路上の中継ノードのホップ数を計算
#relay_hops = {}
#for path in paths_from_2907.values():
#    for node in path[1:-1]:  # 最初と最後のノードは除外
#        if node not in relay_hops:
#            relay_hops[node] = 0
#        relay_hops[node] += 1
#
## ホップ数が最小となる中継ノードを特定
#best_relay_node = min(relay_hops, key=relay_hops.get)
#best_relay_hops = relay_hops[best_relay_node]
#
## 中継ノードを通る場合の経路を計算、ホップ数の増加を記録
#path_lengths_with_relay = {}
#paths_via_relay = {}
#for target in highlight_asns:
#    if target != 2907 and target in G.nodes:
#        try:
#            path_via_relay = nx.shortest_path(G, source=2907, target=best_relay_node) + \
#                             nx.shortest_path(G, source=best_relay_node, target=target)[1:]
#            path_lengths_with_relay[target] = len(path_via_relay) - 1  # ホップ数
#            paths_via_relay[target] = path_via_relay
#        except nx.NetworkXNoPath:
#            path_lengths_with_relay[target] = float('inf')  # 経路が存在しない場合は無限大とする
#
## ノードの色を設定
default_color = 'lightblue'
highlight_color = 'red'
special_color = 'blue'  # 特定のノード(2907)の色
best_relay_color = 'green'  # 最適な中継ノードの色

# ハイライトするノードの色を設定
color_map = []
for node in G.nodes:
    if node == 2907:
        color_map.append(special_color)
    #elif node == best_relay_node:
    #    color_map.append(best_relay_color)
    elif node in highlight_asns:
        color_map.append(highlight_color)
    else:
        color_map.append(default_color)

## 中継ノードを通らない経路のエッジを取得
#highlight_edges_no_relay = set()
#for path in paths_from_2907.values():
#    highlight_edges_no_relay.update((path[i], path[i + 1]) for i in range(len(path) - 1))
#
## 中継ノードを通る経路のエッジを取得
#highlight_edges_with_relay = set()
#for path in paths_via_relay.values():
#    highlight_edges_with_relay.update((path[i], path[i + 1]) for i in range(len(path) - 1))

print("Nodes:", G.number_of_nodes())
print("client:", len(highlight_asns))
print("Edges:", G.number_of_edges())

# グラフの描画
plt.figure(figsize=(12, 12))
pos = nx.spring_layout(G)
# デフォルトのノードの描画
nx.draw(G, pos, node_color=color_map, with_labels=False, node_size=5, font_size=8)
# 中継ノードを通らない経路のエッジを赤色で描画
#nx.draw_networkx_edges(G, pos, edgelist=highlight_edges_no_relay, edge_color='red', width=2)
# 中継ノードを通る経路のエッジを黄色で描画
#nx.draw_networkx_edges(G, pos, edgelist=highlight_edges_with_relay, edge_color='yellow', width=2)
plt.show()

# ホップ数の表示
#print(f"\nBest relay node to minimize hops from 2907 to highlighted nodes: {best_relay_node} (Relay Hops: {best_relay_hops})")
#print("\nPath lengths from 2907 to highlighted nodes without relay node:")
#for target, path in paths_from_2907.items():
#    length = len(path) - 1
#    print(f"2907 -> {target}: {length} hops")
#
#print("\nPath lengths from 2907 to highlighted nodes via relay node:")
#for target, length in path_lengths_with_relay.items():
#    print(f"2907 -> {best_relay_node} -> {target}: {length} hops")
#
## 経路を通った場合のホップ数の増加を表示
#print("\nIncrease in hops by passing through the relay node:")
#for target, length in path_lengths_with_relay.items():
#    if target in paths_from_2907:
#        original_length = len(paths_from_2907[target]) - 1
#        increase = length - original_length
#        print(f"2907 -> {target}: {original_length} -> {length} (Increase: {increase})")
#
