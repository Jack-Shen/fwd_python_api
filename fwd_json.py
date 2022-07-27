import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import sys
import os
import json
#custom headers here. leave empty if not needed. does not need application/json
headers = {}

class _fwdRequest:
    def __init__(self, base_url, **kwargs):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': "application/json"})
        for arg in kwargs:
            if isinstance(kwargs[arg], dict):
                kwargs[arg] = self.__deep_merge(getattr(self.session, arg), kwargs[arg])
            setattr(self.session, arg, kwargs[arg])        
        
    def requests(self, method, url, **kwargs):
        return self.session.request(method, self.base_url+url, **kwargs)

    def get(self, endpoint, **kwargs):
        return self.session.get(self.base_url+endpoint,  **kwargs)

    def post(self, endpoint, **kwargs):
        return self.session.post(self.base_url+endpoint, **kwargs)

    def patch(self, endpoint, **kwargs):
        return self.session.patch(self.base_url+endpoint, **kwargs)

    def put(self, endpoint, **kwargs): 
        return self.session.put(self.base_url+endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self.session.delete(self.base_url+endpoint, **kwargs)

    @staticmethod
    def __deep_merge(source, destination):
        for key, value in source.items():
            if isinstance(value, dict):
                node = destination.setdefault(key, {})
                _fwdRequest.__deep_merge(value, node)
            else:
                destination[key] = value
        return destination

class fwdApi: 
    def __init__(self, base_url, username, token, network, headers, verify=True):
        self.base_url = base_url
        self.network = network
        self.fwdRequest = _fwdRequest(self.base_url, auth=(username, token), headers=headers, verify=verify)
    def get_network_id(self, network_name):
        all_network = self.get_all_networks().json()
        for n in all_network:
            if n['name'] == network_name:
                return n['id']
        return None
    def get(self, snapshot, ip):
        string = "/snapshots/{}/search?q={}&max=1".format(snapshot, ip)
        print (string)
        return self.fwdRequest.get(string)
    
    def request_get(self, endpoint):
        return self.fwdRequest.get(endpoint)
    #networks
    def get_all_networks(self):
        return self.fwdRequest.get("/networks")
    def create_network(self, name):
        return self.fwdRequest.post("/networks?name="+name)
    def rename_network(self, network_id, new_name):
        return self.fwdRequest.patch("/networks/"+str(network_id), json={"name": str(new_name)})
    def delete_network(self, network_id):
        return self.fwdRequest.delete("/networks/"+str(network_id))

    #network setups
    def get_device_credential(self, network_id):
        return self.fwdRequest.get("/networks/"+str(network_id)+"/deviceCredentials")

    #network collection
    def get_collector_status(self, network_id):
        return self.fwdRequest.get("/networks/"+str(network_id)+"/collector/status")
    
    def start_collection(self, network_id):
        return self.fwdRequest.post("/networks/"+str(network_id)+"/startcollection")

    def status_collection(self, network_id):
        return self.fwdRequest.get("/networks/"+str(network_id)+"/collector/status")

    def stop_collection(self, network_id):
        return self.fwdRequest.post("/networks/"+str(network_id)+"/cancelcollection")
    
    def get_snapshot_latest(self, network_id):
        return self.fwdRequest.get("/networks/"+str(network_id)+"/snapshots/latestProcessed")

    
    def _get_devices(self, network_id=None, snapshot=None):
        if network_id:
            return self.fwdRequest.get("/networks/"+str(network_id)+"/deviceSources")
        if snapshot:
            return self.fwdRequest.get("/snapshots/"+str(snapshot)+"/devices")

    def get_device_file(self, device_name, snapshot, filename):
        return self.fwdRequest.get("/snapshots/{}/devices/{}/files/{}".format(
            snapshot, device_name, filename))

    def get_path_search(self, snapshotID, srcIP, dstIp, **kwargs):
        """
        Parameters
        ----------
        snapshotID : string or int
            the snapshot id
        srcIP : string
            source ip or subnet
        dstIp : string
            destination ip or subnet
        **kwargs : optional arguments. Consult api-doc for full list. Examples: 
            intent: string
                SINGLE_BEST | PREFER_VIOLATIONS | PREFER_DELIVERED | VIOLATIONS_ONLY
            ipProto: string
                ip protocol number
            srcPort: string
                the source port number
            dstPort: string
                the destination port number
            icmpType: string
                when ipProto = 1, defines icmpType number
            include NetworkFunctions: string
                true or false
                If true, the response includes detailed forwarding info for each hop.
                Note: Setting this to true increases the API response time.
            maxResults: string 
                [1, 10000]
            maxReturnPathResults: string
                the limit on the number of return path search results. Permitted range = 0 to 10,000. Default 0.
            maxSeconds: string
                the timeout duration. Permitted range = 1 to 600. Default 30.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        
        endpoint = "/snapshots/{}/paths".format(snapshotID)
        url = '?srcIp={}&dstIp={}'.format(srcIP, dstIp)

        for k, v in kwargs.items():
            if v: 
                url+='&{}={}'.format(k, v)
        return self.fwdRequest.get(endpoint+url)        
    
    def _construct_element(self, keywd):
        ''' internal function for construction json location and headers'''
        result = {}
        if type(keywd) == dict: 
            #assumes keywd is location
            result['location'] = keywd
        elif type(keywd) == tuple: 
            if len(keywd) == 1 and type(keywd[0]) == dict: 
                result['location'] = keywd[0]
            
            elif len(keywd) == 2 and type(keywd[0]) == dict and type(keywd[1]) == dict and len(keywd[1]) == 2:
                result['location'] = keywd[0]
                result['headers'] = [keywd[1]]
                
            elif len(keywd) == 2 and type(keywd[0]) == dict and type(keywd[1]) == list:
                result['location'] = keywd[0]
                result['headers'] = keywd[1]
            else: 
                print("ERROR: _construct_element - input is:")
                print(keywd)
                raise ValueError('location or headers is incorrect')

        else: 
            print("ERROR: _construct_element - input is:")
            print(keywd)
            raise ValueError('location or headers is incorrect')

        return result


    def _construct_json(self,check_type, snapshotID, FROM=None, TO=None, THROUGH=None, INGRESS=None, EGRESS=None, flowTypes=None, permitAll=False):
        """
        internal function for function to construct check json
        """
        data = {}
        filters = {}
        chain = []         
        if FROM: 
            filters['from'] = self._construct_element(FROM)
        if TO: 
            filters['to'] = self._construct_element(TO)

        if THROUGH: 
            if type(THROUGH) is tuple: 
                THROUGH = [THROUGH]
            for i in THROUGH: 
                chain_ele = self._construct_element(i)
                chain_ele['transitType'] = 'through'
                chain.append(chain_ele)

        if EGRESS: 
            if type(EGRESS) is tuple: 
                EGRESS = [EGRESS]
            for i in EGRESS: 
                chain_ele = self._construct_element(i)
                chain_ele['transitType'] = 'egress'
                chain.append(chain_ele)

        if INGRESS: 
            if type(INGRESS) is tuple: 
                INGRESS = [INGRESS]
            for i in INGRESS: 
                chain_ele = self._construct_element(i)
                chain_ele['transitType'] = 'ingress'

                chain.append(chain_ele)

        if flowTypes: 
            filters['flowTypes'] = [flowTypes]

        data['checkType'] = check_type
        data['filters'] = filters

        if len(chain) > 0:
            data['filters']['chain'] = chain
        if permitAll: 
            data['filters']['mode'] = "PERMIT_ALL"
        
        print("*************")
        print(data)
        print("*************")

        return data

    def post_nqe_check(self, query, snapshot=None):
        url = "/nqe?networkId={}".format(self.network)
        if snapshot: 
            url = "/nqe?snapshotId={}".format(snapshot)
        
        payload = {"query": query}
        
        result = self.fwdRequest.post(url, json=payload)
        
        return result.json()
        
    def post_nqe_para_check(self, queryId, params, snapshot=None):
        url = "/nqe?networkId={}".format(self.network)
        if snapshot: 
            url = "/nqe?snapshotId={}".format(snapshot)
        payload = {
            "queryId": queryId,
            "parameters": params
            } 
        result = self.fwdRequest.post(url, json=payload)
        return result.json()

    def post_existance_check(self, snapshotID, FROM=None, TO=None, THROUGH=None, INGRESS=None, EGRESS=None, flowTypes=None,  permitAll=True):
        """
        Parameters
        ----------
        snapshotID : string or int
            the snapshot id.
        FROM : tuple, optional
            a tuple of dict in (location, header)
        TO : tuple, optional
            a tuple of dict in (location, header)
        THROUGH : list or tuple, optional
            a tuple in format of (location, header) or (location, [header1, header2...])
        INGRESS : list or tuple, optional
            a tuple in format of (location, header) or (location, [header1, header2...])
        EGRESS : list or tuple, optional
            a tuple in format of (location, header) or (location, [header1, header2...])
        flowTypes : string, optional
            delivered | loop | blackhole | dropped | inadmissible | unreachable | undelivered

        permitAll : boolean, optional
            enables permit all mode

        Returns
        -------
        None.

        """
        data = self._construct_json('Existential', snapshotID, FROM, TO, THROUGH, INGRESS, EGRESS, flowTypes, permitAll)
        print(self.fwdRequest.post("/snapshots/{}/checks".format(snapshotID), json=data).text)

    def post_isolation_check(self, snapshotID, FROM=None, TO=None, THROUGH=None, INGRESS=None, EGRESS=None, flowTypes=None, permitAll=True):
        """
        Parameters
        ----------
        snapshotID : string or int
            the snapshot id.
        FROM : tuple, optional
            a tuple of dict in (location, header)
        TO : tuple, optional
            a tuple of dict in (location, header)
        THROUGH : list or tuple, optional
            a tuple in format of (location, header) or (location, [header1, header2...])
        INGRESS : list or tuple, optional
            a tuple in format of (location, header) or (location, [header1, header2...])
        EGRESS : list or tuple, optional
            a tuple in format of (location, header) or (location, [header1, header2...])
        flowTypes : string, optional
            delivered | loop | blackhole | dropped | inadmissible | unreachable | undelivered

        permitAll : boolean, optional
            enables permit all mode

        Returns
        -------
        None.

        """
        data = self._construct_json('Isolation', snapshotID, FROM, TO, THROUGH, INGRESS, EGRESS, flowTypes, permitAll)
        print(self.fwdRequest.post("/snapshots/{}/checks".format(snapshotID), json=data).text)
        
    def post_reachability_check(self, snapshotID, FROM=None, TO=None, permitAll=False):
        
        """
    
        Parameters
        ----------
        snapshotID : String or int
            the snapshot ID
        FROM : tuple, REQUIRED
            a tuple of dict in (location, header)
        TO : TYPE, optional
            DESCRIPTION. The default is None.
        permitAll : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        result : request
            returns the request object.

        """
        if FROM == None: 
            sys.exit("Reachability check for FROM is required.")
        if type(TO) != tuple and type(TO) != dict: 
            sys.exit("Reachability check for TO is optional. It is either a location dict, or a set (location). "+ str(type(TO))+ " is not supported")
        if type(TO) == tuple and len(TO) != 1: 
            sys.exit("Reachability check for TO cannot have headers.")
        if type(TO) == dict: 
            TO = (TO,)
        
        data = self._construct_json('Reachability', snapshotID, FROM=FROM, TO=TO)
        result = self.fwdRequest.post("/snapshots/{}/checks".format(snapshotID), json=data)
        print(result.text)
        return result
    def get_intent_checks(self, snapshotID, checkType): 
        #get all intent checks
        #checkType: Isolation, Reachability, Existential, QueryStringBased, Predefined, NQE
        
        url = "/snapshots/{}/checks?type={}".format(snapshotID, checkType)
        print(url)
        result = self.fwdRequest.get(url)
        return result

    def get_intranet_nodes(self, snapshotID): 
        url = "/snapshots/{}/intranetNodes".format(snapshotID)
        print(url)
        result = self.fwdRequest.get(url)
        print(result.json())
        return result 

    def add_intranet_node(self, NetworkID, snapshotID, IntranetName, DeviceName, Interface,
            SubnetAutoDiscovery="IP_ROUTES", advertisesDefaultRoute=False, locationId="default"): 
        """
        SubnetAutoDiscovery=[ NONE, IP_ROUTES, BGP_ROUTES ]
        """
        existing_intranet = self.get_intranet_nodes(snapshotID).json()
        existing_name = [ i['name']  for i in
                existing_intranet['intranetNodes'] ]
        url = "/snapshots/{}/intranetNodes/{}".format(snapshotID, IntranetName)
        all_devices = self._get_devices(NetworkID)
        locationId = [ i['locationId'] for i in all_devices.json() if i['name'] ==
                DeviceName and 'locationId' in i ]

        print(locationId)

        if len(locationId) == 0: 
            locationId="default"
        else: 
            locationId = locationId[0]

        print("LOCATION ID IS##### {}".format(locationId))
        data = {
                'name' : IntranetName,
                'locationId' : locationId
                }
        data['connections']=[]
        uplinkPort = {
                'device': DeviceName,
                'port': Interface
                }


        conn = {
                'uplinkPort' : uplinkPort,
                'name' : DeviceName+"_"+Interface,
                'subnetAutoDiscovery' : SubnetAutoDiscovery,
                'advertisesDefaultRoute' : advertisesDefaultRoute
                }

        data['connections'].append(conn)

        payload = {
                'intranetNodes' : [data]
                }
        payload = data
        if IntranetName in existing_name: 
            print("intranet already exist")
            result = self.fwdRequest.post(url+"/connections", json=conn)
        else: 
            print("new intranet node")
            result = self.fwdRequest.put(url, json=payload)
        print(payload)
        print(result.text)
        return result




def gen_headers(value_type, value, header_type="PacketFilter", direction=None, notFilter=False):
    """
    helper function constructs json header format
    value: a STRING corresponding to value_type
    direction: "src" or "dst"
    
    Parameters
    ----------
    value_type : string
        a string of header formats. Most commonly used are: 
            ipv4_src |ipv4_dst ipv6_src | ipv6_dst mac_src | mac_dst tp_src | tp_dst| eth_type| vlan_vid| ip_proto
    value : string
        the value of the corresponding value_type.
    header_type : string, optional
        DESCRIPTION. The default is "PacketFilter". "PacketAliasFilter" needs corresponding alias set
    direction : string, optional
        DESCRIPTION. Either "src" or "dst"
    notFilter : boolean, optional
        DESCRIPTION. The default is False. If set to True negates the header value_type and value. 

    Returns
    -------
    dict
        constructed header dict usable for fwdApi.

    """
    header={}
    header['type'] = header_type
    if header_type == "PacketFilter": 
        header['values'] = {str(value_type): [str(value)]}
    elif header_type == "PacketAliasFilter":
        header['value'] = value
    else: 
        sys.exit("header_type is either 'PacketFilter' or 'PacketAliasFilter'")

    if direction: 
        header['direction'] = direction
    if notFilter == True:
        notHeader ={}
        notHeader['type'] = "NotFilter"
        notHeader['clause'] = header
        return notHeader
    return header

#location = ("SubnetLocationFilter", ipaddr), HostFilter

def gen_location(SubnetLocationFilter=None, HostFilter=None, DeviceFilter=None, InterfaceFilter=None, 
    VrfFilter=None, HostAliasFilter=None, DeviceAliasFilter=None, InterfaceAliasFilter=None):
    """
    helper function constructs json location format
    ONLY ONE input

    Parameters
    ----------
    SubnetLocationFilter : string, optional
        DESCRIPTION. an IP address or subnet
    HostFilter : string, optional
        DESCRIPTION. The default is None.
    DeviceFilter : string, optional
        DESCRIPTION. one host or Edge Node name, IP address, subnet, or MAC address
    InterfaceFilter : string, optional
        DESCRIPTION. one interface name, qualified with its device name
    VrfFilter : string, optional
        DESCRIPTION.  one VRF name, optionally qualified with a device name
    HostAliasFilter : string, optional
        DESCRIPTION. a HOSTS Alias name
    DeviceAliasFilter : string, optional
        DESCRIPTION. a DEVICES Alias name
    InterfaceAliasFilter : string, optional
        DESCRIPTION. an INTERFACES

    Returns
    -------
    dict
        constructed location dict usable for fwdApi.

    """
    if sum(v == None for v in locals().values()) != 7: 
        sys.exit("gen_location() takes only one input")
    #[result['type'] = v if v != None for v in locals().values()]
    for x, y in locals().items():
        if y != None:
            if x == "HostFilter" or x == "DeviceFilter" or x == "InterfaceFilter" or x == "VrfFilter":
                return { 'type': x, 'values': [y]}
            else:
                return { 'type': x, 'value': y}
    

