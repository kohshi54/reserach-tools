#!/bin/bash

set -e
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## make ASPATH list from bgp message
#touch aspath.list
#chmod +w aspath.list
bgpmessages="rib.20240401.0000.bz2"
if [ ! -e aspath.list ]; then
	bgpdump $bgpmessages | grep ASPATH > aspath.list
fi

## map asn appear to asn map (full route)
python3 7.py

deactivate

#rm ip.list

