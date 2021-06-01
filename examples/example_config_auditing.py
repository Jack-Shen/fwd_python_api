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

#get the latest snapshot id 
latest_snap = fwd.get_snapshot_latest(network).json()['id']
print(latest_snap)


#define a block 
blockConfig='''
block=```
ip access-list standard BASELINE_ACL
   10 permit 192.168.252.94/31
   20 permit host 192.168.252.220
   30 permit host 192.168.252.222
```;
foreach d in network.devices
where isPresent(d.platform.osVersion)
where d.platform.os == OS.ARISTA_EOS
let diff = blockDiff_alpha1(d.files.config, block)
where diff.diffCount != 0
select {
  name: d.name, 
  model: d.platform.model,
  missing_config: diff.blocks
}
'''

print(json.dumps(fwd.post_nqe_check(blockConfig), indent=4, sort_keys=True))


