"""
input: clientasnrtt.csv
output: ipごとの時系列rttデータのcsv

ipaddr,asn,asname,t1,t2,t3,...,t60
x.x.x.x, 133335, 2ms, 4ms, 2ms,...,5ms

"""
import numpy as np
import pandas as pd
from scipy import stats
from matplotlib import pyplot as plt
import sys

input_csv = sys.argv[1]
output_csv = sys.argv[2]

server_df = pd.read_csv(input_csv) #./data/serverasnrtt.csv
#server_df = pd.read_csv('./data/clientasnrtt.csv')

server_df['syntime(ms)'] = pd.to_datetime(server_df['syntime(ms)'], unit='ms')
server_df.set_index('syntime(ms)', inplace=True)
print(server_df.head().to_string())

# ipaddr, ASN, ASname 毎の最小RTTを計算しておく
min_rtt_by_group = server_df.groupby(['ipaddr', 'asn', 'asname'])['rtt'].min()

# 'ipaddr + ASN + ASname' 毎にデータをグループ化して、1分ごとにリサンプリング
def resample_and_fill(group, min_rtt):
    # 1分ごとにRTTをリサンプリングし、最大値を取得
    rtt_resampled = group['rtt'].resample('1T').max()

    # 15:00 ~ 16:00 の範囲にインデックスを再調整
    full_range = pd.date_range(start='2024-05-14 15:00:00', end='2024-05-14 15:59:00', freq='1T')
    rtt_resampled = rtt_resampled.reindex(full_range)

    # NaNをmin_rttで手動で補完
    rtt_resampled.fillna(min_rtt, inplace=True)

    return rtt_resampled

# ipaddr + ASN + ASname ごとにリサンプリングと補完を実行
df_resampled = server_df.groupby(['ipaddr', 'asn', 'asname']).apply(lambda group: resample_and_fill(group, min_rtt_by_group[group.name]))



#print(df_resampled)

df_resampled.to_csv(output_csv) #./data/odrtt_timeseries_server.csv
