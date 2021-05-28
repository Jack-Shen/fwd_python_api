#!/usr/bin/env python
# coding: utf-8

# ### 1 - SET UP THE API

# In[1]:


import requests
import sys
import os
sys.path.insert(0, "/home/admin/ansible/fwd_python_api")
import fwd_json
from fwd_json import fwdApi
username = os.environ['fwd_saas_user']
token = os.environ['fwd_saas_token']
network = 137407
fwd = fwdApi("https://fwd.app/api", username, token,network, {}, verify=True)
nqeUrl = "https://fwd.app/api/nqe?networkId={}".format(network)


# In[2]:
print(fwd.get_all_networks)

#start collection
fwd.start_collection(network).text


# In[3]:


#get the latest snapshot id 
latest_snap = fwd.get_snapshot_latest(network).json()['id']
print(latest_snap)


# In[4]:


#basic NQE to get a report of the network
query = '''
foreach d in network.devices
select {
  name: d.name, 
  mgmtIP: d.platform.managementIps,
  model: d.platform.model,
  osType: d.platform.os,
  osVersion: d.platform.osVersion,
  serial: (foreach c in d.platform.components
           where isPresent(c.serialNumber) select c.serialNumber)
}'''


# In[5]:


fwd.post_nqe_check(query)


# ### 2 -  METHOD 1 OF RUNNING NQE: define the query as a string

# In[20]:



#define a block 
blockConfig='''
block=```
ip access-list standard BASELINE_ACL
  10   permit 192.168.252.94/31
  20   {"permit" | "deny"} host 192.168.252.220

```;
foreach d in network.devices
where isPresent(d.platform.osVersion)
where d.platform.os == OS.ARISTA_EOS
let diff = blockDiff_alpha1(d.files.config, block)
//where diff.diffCount != 0
select {
  name: d.name, 
  model: d.platform.model,
  missing_config: diff.blocks
}
'''


# In[21]:


fwd.post_nqe_check(blockConfig)


# ### 3 -  METHOD 2 OF RUNNING NQE: define the API within NQE

# In[22]:


#check baseline CONFIG for all devices 
config = open('baseline_acl.txt', 'r').read()
config = "test"
queryId = "Q_e6ec1965d99271ce3e3a7223897469efc253468f"
payload = {"config": config}
    
response = fwd.post_nqe_para_check(queryId, payload)
missingConfig = response
print(missingConfig)


# In[23]:


#check BASELINE CONFIG for subset of devices 
config = open('baseline_acl.txt', 'r').read()
config = "test"
queryId = "Q_b7ed24370895b73d6ddbef0b81cffe04d22ae6f5"
#define which device to check
inputDevice = ["leaf1"]
payload = {"config": config, "deviceList": inputDevice}
response = fwd.post_nqe_para_check(queryId, payload)
missingConfig = response
print(missingConfig)


# In[26]:


#parameterized NQE for BGP neighbor 
queryId = "Q_8178355cfc658ab46cac0f07f2b033f68fa92c80"
payload = {"deviceList": ["leaf4", "leaf2"]}
response = fwd.post_nqe_para_check(queryId, payload)
print(response)


# In[27]:


#parameterized NQE for interfaces that are down 
queryId = "Q_37cac69e9e54556d97b175d8392fa307d7a7afc8"
payload = {"deviceList": ["leaf4"]}
response = fwd.post_nqe_para_check(queryId, payload)
print(response)


# ### 4 - PATH SEARCH API

# In[28]:


#simple path search api 
srcIP = "192.168.100.1"
dstIP = "192.168.100.4"
fwd.get_path_search(latest_snap,srcIP, dstIP).json()


# In[29]:


#advanced use - define a path search and add as "Existential" intent check

sourceIp = fwd_json.gen_location(SubnetLocationFilter="192.168.100.1/32")
destIp = fwd_json.gen_location(SubnetLocationFilter="192.168.100.4/32")
fwd.post_existance_check(snapshotID=latest_snap, FROM=(sourceIp), TO=(destIp))


# In[30]:


#get results for all "Existential" intent check
result = fwd.get_intent_checks(latest_snap, "Existential").json()
print(result)


# In[ ]:




