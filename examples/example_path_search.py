#!/usr/bin/env python
# coding: utf-8

# ### 1 - SET UP THE API

import requests
import sys
import os
import json
sys.path.append("..")
import fwd_json
from fwd_json import fwdApi
import setup
username = setup.username
token = setup.token
network = setup.network 
fwd = setup.fwd
nqeUrl = setup.nqeUrl



#get latest snapshot
latest_snap = fwd.get_snapshot_latest(network).json()['id']
print("latest snapshot id is : {}".format(latest_snap))

#simple path search api
srcIP = "192.168.100.1"
dstIP = "192.168.100.4"
result = fwd.get_path_search(latest_snap,srcIP, dstIP).json()

print(json.dumps(result, indent=4, sort_keys=True))

