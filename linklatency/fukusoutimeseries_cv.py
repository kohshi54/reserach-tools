"""
input: routing_matrix, ipaddr毎の時系列rtt (両方unique ipaddr)
ouput: 各tにおけるリンク毎のキューイング遅延

	linka, linkb, linkc, ... ,linkn
t1   2ms,   0,     3ms
t2   1ms,   0,     2ms
t3   5ms,   0,     2ms
...
t60

"""

import pandas as pd
import numpy as np
# from sklearn.linear_model import Lasso
from sklearn.linear_model import LassoCV
import sys

rm_csv = sys.argv[1]
odrtt_timeseries_csv = sys.argv[2]
output_csv = sys.argv[3]

#routemx = pd.read_csv('routing_matrix.csv', index_col='ipaddr')
routemx = pd.read_csv(rm_csv, index_col='ipaddr') #server ./data/routing_matrix_server.csv
#routemx = pd.read_csv('./data/routing_matrix3.csv', index_col='ipaddr') #client routeが見つかっていない人がいる場合に削除されているので, odlatencyよりこっちの方がipaddrが少し少ない
#odlatency = pd.read_csv('odpair-timeseries-rtt.csv', index_col=['ipaddr', 'asn', 'asname'])
odlatency = pd.read_csv(odrtt_timeseries_csv, index_col=0, usecols=lambda column: column not in ['asn', 'asname']) #server ./data/odrtt_timeseries_server.csv
#odlatency = pd.read_csv('./data/odrtt_timeseries_client.csv', index_col=0, usecols=lambda column: column not in ['asn', 'asname']) #client

#共通のipaddrを取得して順番を一致させる #routemx作るときにfullroute_ipv4で見つからなかったやつは除外されてるので数と順序合わせる必要あり
common_ipaddr = routemx.index.intersection(odlatency.index)
routemx_common = routemx.loc[common_ipaddr]
odlatency_common = odlatency.loc[common_ipaddr]

#各ipaddrの60mのうちの最小rttを計算
min_rtt_by_ipaddr = odlatency_common.min(axis=1)

#各rttから60mのうち最小rttを引く(QDが出てくる）QD = ODL - PD
odlatency_adjusted = odlatency_common.subtract(min_rtt_by_ipaddr, axis=0)

print(routemx_common.shape, odlatency_adjusted.shape)

# lasso = Lasso(alpha=0.1, positive=True)
# alphas = np.logspace(-4, 1, 50)
# lasso_cv = LassoCV(alphas=alphas, cv=5, positive=True) #normalize=Falseでnormalize引数ないってエラー。無くなった?
lasso_cv = LassoCV(cv=5, positive=True, fit_intercept=False, n_jobs=-1) #係数は遅延なのでnormalizeしない, 係数が全て0なら遅延も0のはずなのでfit_intercept=false, #alphaはとりあえず自動で選んでもらう

link_latencies = []
intercepts = []

#各tにおいて輻輳リンク探す
for col in odlatency_adjusted.columns:
    print(f"t={col}", f"rm.shape={routemx_common.shape}", f"odl.shape={odlatency_adjusted[col].shape}")
    lasso_cv.fit(routemx_common, odlatency_adjusted[col])
    
    link_latency = lasso_cv.coef_
    intercept = lasso_cv.intercept_
    
    link_latencies.append(link_latency)
    intercepts.append(intercept)

optimal_alphas = pd.Series(lasso_cv.alphas_, name="Optimal Alphas")
optimal_alphas.to_csv("optimal_alphas_cv.csv", index=False)
print("Optimal alpha values from cross-validation:", optimal_alphas)

#リンクレイテンシto_csv
link_latencies_df = pd.DataFrame(link_latencies, columns=routemx_common.columns, index=odlatency_common.columns)
link_latencies_df.to_csv(output_csv)

#切片も <- 0に近いはず(説明変数の係数が全て0なら遅延も0になるはず)
intercepts_df = pd.DataFrame(intercepts, index=odlatency_common.columns, columns=['Intercept'])
intercepts_df.to_csv('./output/intercepts_client_cv2.csv')

