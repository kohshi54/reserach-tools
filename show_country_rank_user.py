import sys
import matplotlib.pyplot as plt

# make asn:country map
asncountrymp = {}
with open(sys.argv[1], 'r') as f:
	for line in f:
		_,_,asn,country,name = line.split('\t')
		asncountrymp[asn] = country

def getccpktsconnmp(datafile):
	countrypktsmp = {}
	countryconnmp = {}
	with open(datafile, 'r') as infile:
		for line in infile:
			asn,pktscnt,pktsrate,conncnt,connrate = line.split(' ')		
			cu = asncountrymp[asn]
			if cu in countrypktsmp:
				countrypktsmp[cu] += int(pktscnt)
				countryconnmp[cu] += int(conncnt)
			else:
				countrypktsmp[cu] = int(pktscnt)
				countryconnmp[cu] = int(conncnt)
	return (countrypktsmp, countryconnmp)

def getccpktsconnmprate(datafile):
	countrypktsmp = {}
	countryconnmp = {}
	with open(datafile, 'r') as infile:
		for line in infile:
			asn,pktscnt,pktsrate,conncnt,connrate = line.split(' ')		
			cu = asncountrymp[asn]
			if cu in countrypktsmp:
				countrypktsmp[cu] += float(pktsrate)
				countryconnmp[cu] += float(connrate)
			else:
				countrypktsmp[cu] = float(pktsrate)
				countryconnmp[cu] = float(connrate)
	return (countrypktsmp, countryconnmp)


#accesspktsmp,accessconnmp = getccpktsconnmp(sys.argv[2])
#clientpktsmp,clientconnmp = getccpktsconnmp(sys.argv[3])
accesspktsmp,accessconnmp = getccpktsconnmprate(sys.argv[2])
clientpktsmprate,clientconnmprate = getccpktsconnmprate(sys.argv[3])
clientpktsmpcnt,clientconnmpcnt = getccpktsconnmp(sys.argv[3])
topaccesspkts = dict(sorted(accesspktsmp.items(), key=lambda x:x[1], reverse=True)[:50])
def add_other_field(mp):
	total_ratio = sum(mp.values())
	other_ratio = 1.0 - total_ratio
	if other_ratio > 0:
		mp['Other'] = other_ratio
	return mp
topaccesspkts = add_other_field(topaccesspkts)
topaccessconn = dict(sorted(accessconnmp.items(), key=lambda x:x[1], reverse=True)[:50])
topaccessconn = add_other_field(topaccessconn)

topclientpktsrate = dict(sorted(clientpktsmprate.items(), key=lambda x:x[1], reverse=True)[:50])
topclientpktsrate = add_other_field(topclientpktsrate)
topclientconnrate = dict(sorted(clientconnmprate.items(), key=lambda x:x[1], reverse=True)[:50])
topclientconnrate = add_other_field(topclientconnrate)

topclientpktscnt = dict(sorted(clientpktsmpcnt.items(), key=lambda x:x[1], reverse=True)[:50])
#topclientpktscnt = add_other_field(topclientpktscnt)
topclientconncnt = dict(sorted(clientconnmpcnt.items(), key=lambda x:x[1], reverse=True)[:50])
#topclientpktscnt = add_other_field(topclientpktscnt)
#print(topaccesspkts)
#print(topaccessconn)

print(topclientpktsrate)
print(topclientconnrate)
print(topclientpktscnt)
print(topclientconncnt)

fig, axes = plt.subplots(2, 2)
"""
axes[0,0].bar(topaccesspkts.keys(), topaccesspkts.values())
axes[0,0].set_title('pkts based top access AS')
#axes[0,0].set_xlabel('cc')
#axes[0,0].set_ylabel('pkts')
axes[0,0].set_xticklabels(topaccesspkts.keys(), rotation=90, ha='right')
"""
"""
axes[0,0].pie(topaccesspkts.values(), labels=topaccesspkts.keys(), autopct='%1.1f%%', startangle=140)
axes[0,0].set_title('pkts based top access AS')
"""

"""
axes[0,1].bar(topaccessconn.keys(), topaccessconn.values())
axes[0,1].set_title('conn based top access AS')
#axes[0,1].set_xlabel('cc')
#axes[0,1].set_ylabel('conn')
axes[0,1].set_xticklabels(topaccessconn.keys(), rotation=90, ha='right')
"""
"""
axes[1,0].pie(topaccessconn.values(), labels=topaccessconn.keys(), autopct='%1.1f%%', startangle=140)
axes[1,0].set_title('conn based top access AS')
"""

#"""
axes[0,0].bar(topclientpktscnt.keys(), topclientpktscnt.values())
axes[0,0].set_title('pkts based top client AS')
#axes[0,0].set_xlabel('cc')
#axes[0,0].set_ylabel('pkts')
axes[0,0].set_xticklabels(topclientpktscnt.keys(), rotation=90, ha='right')
#"""

axes[0,1].pie(topclientpktsrate.values(), labels=topclientpktsrate.keys(), autopct='%1.1f%%', startangle=140)
axes[0,1].set_title('pkts based top client AS')

#"""
axes[1,0].bar(topclientconncnt.keys(), topclientconncnt.values())
axes[1,0].set_title('conn based top client AS')
#axes[1,1].set_xlabel('cc')
#axes[1,1].set_ylabel('conn')
axes[1,0].set_xticklabels(topclientconncnt.keys(), rotation=90, ha='right')
#"""

axes[1,1].pie(topclientconnrate.values(), labels=topclientconnrate.keys(), autopct='%1.1f%%', startangle=140)
axes[1,1].set_title('conn based top client AS')

plt.tight_layout()
plt.show()

