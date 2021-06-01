#!/usr/bin/env python
# coding: utf-8

# ### 1 - SET UP THE API

# In[1]:


import requests
import sys
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

#get the latest snapshot id 
latest_snap = fwd.get_snapshot_latest(network).json()['id']
print(latest_snap)



#check BASELINE CONFIG for subset of devices 
config = open('baseline_acl.txt', 'r').read()
queryId = "Q_b7ed24370895b73d6ddbef0b81cffe04d22ae6f5"
#define which device to check
inputDevice = ["leaf1"]
payload = {"config": config, "deviceList": inputDevice}
response = fwd.post_nqe_para_check(queryId, payload)
print(json.dumps(response, indent=4, sort_keys=True))
