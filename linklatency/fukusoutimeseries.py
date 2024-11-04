import pandas as pd
import numpy as np
from sklearn.linear_model import Lasso

routemx = pd.read_csv('routing_matrix.csv', index_col='ipaddr')
#odlatency = pd.read_csv('odpair-timeseries-rtt.csv', index_col=['ipaddr', 'asn', 'asname'])
odlatency = pd.read_csv('odpair-timeseries-rtt.csv', index_col=0, usecols=lambda column: column not in ['asn', 'asname'])

# 共通の ipaddr を取得して順番を一致させる
common_ipaddr = routemx.index.intersection(odlatency.index)
routemx_common = routemx.loc[common_ipaddr]
odlatency_common = odlatency.loc[common_ipaddr]

#odlatency_common = odlatency_common.apply(pd.to_numeric, errors='coerce')

# 各ipaddrの60分間の最小RTTを計算
min_rtt_by_ipaddr = odlatency_common.min(axis=1)

# RTTから60分間の最小RTTを引く(QLが出てくる）
odlatency_adjusted = odlatency_common.subtract(min_rtt_by_ipaddr, axis=0)

#odlatency_adjusted = odlatency_adjusted.apply(lambda row: row.fillna(min_rtt_by_ipaddr[row.name]), axis=1)

## 補完後にまだNaNが残っていないか確認
#if odlatency_adjusted.isna().sum().sum() > 0:
#    print("NaN values still present after filling.")
#else:
#    print("No NaN values remain.")

print(routemx_common.shape, odlatency_adjusted.shape)

lasso = Lasso(alpha=0.1, positive=True)

link_latencies = []
intercepts = []

# 各tにおいて輻輳ポイント探す
for col in odlatency_adjusted.columns:
    print(routemx_common.shape, odlatency_adjusted[col].shape)
    lasso.fit(routemx_common, odlatency_adjusted[col])
    
    link_latency = lasso.coef_
    intercept = lasso.intercept_
    
    link_latencies.append(link_latency)
    intercepts.append(intercept)

# リンクレイテンシをDataFrameとして格納
link_latencies_df = pd.DataFrame(link_latencies, columns=routemx_common.columns, index=odlatency_common.columns)
link_latencies_df.to_csv('link_latencies.csv')

# インターセプト（切片）も
intercepts_df = pd.DataFrame(intercepts, index=odlatency_common.columns, columns=['Intercept'])
intercepts_df.to_csv('intercepts.csv')

