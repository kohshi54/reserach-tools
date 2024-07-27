import json

# load asn scope mp
asnscopemp = {}
scopecnt = {}
with open('./peeringdb.json', 'r') as f:
	loaded = json.load(f) 
	alldata = loaded["data"]
	for data in alldata:
		asn = data["asn"]
		scope = data["info_scope"]
		asnscopemp[asn] = scope

		if not scope:
			scope = "Not Disclosed"

		if scope in scopecnt:
			scopecnt[scope] += 1
		else:
			scopecnt[scope] = 1

	#print(len(asnscopemp))
	#print(scopecnt)

globalpktsrate = 0.0
globalconnrate = 0.0
scopemp = {}
with open('./serverasn.pkts.conn.list', 'r') as serverf:
	for line in serverf:
		asn,pktscnt,pktsrate,conncnt,connrate = line.split()
		asn = int(asn)
		pktsrate = float(pktsrate)
		connrate = float(connrate)
		try:
			scope = asnscopemp[asn]
			if scope in scopemp:
				scopemp[scope]["pktsrate"] += pktsrate
				scopemp[scope]["connrate"] += connrate
			else:
				scopemp[scope] = {"pktsrate": pktsrate, "connrate": connrate}

			if scope == "Global":
				globalpktsrate += pktsrate
				globalconnrate += connrate
		except:
			scope = "ASNotFound"
			if scope in scopemp:
				scopemp[scope]["pktsrate"] += pktsrate
				scopemp[scope]["connrate"] += connrate
			else:
				scopemp[scope] = {"pktsrate": pktsrate, "connrate": connrate}

#print(f"globalpktsrate: {globalpktsrate}")
#print(f"globalconnrate: {globalconnrate}")
for scope,cnt in scopemp.items():
	pktsrate = cnt["pktsrate"]
	connrate = cnt["connrate"]
	print(f"{scope}: {pktsrate:.6f} {connrate:.6f}")

