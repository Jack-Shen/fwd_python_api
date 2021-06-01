#!/usr/bin/env python
# coding: utf-8

# ### 1 - SET UP THE API

import sys
import os
sys.path.append("..")
import fwd_json
from fwd_json import fwdApi
username = os.environ['fwd_saas_user']
token = os.environ['fwd_saas_token']

network = 137407

fwd = fwdApi("https://fwd.app/api", username, token,network, {}, verify=True)
nqeUrl = "https://fwd.app/api/nqe?networkId={}".format(network)



