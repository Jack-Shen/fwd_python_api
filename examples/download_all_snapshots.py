import requests
import setup
fwd = setup.fwd

all_networks = fwd.get_all_networks().json()

for n in all_networks: 
    print(n)
    name = n['name']
    n_id = n['id']
    print("Downloading network {} {}".format(name, n_id))
    all_snapshots = fwd.get_snapshot_all(n_id).json()['snapshots']
    print(all_snapshots)
    for i in all_snapshots:
        print("downloading snapshot {}".format(i['id']))
        fwd.download_snapshot(i['id'], "./test/{}_{}.zip".format(n_id, i['id']))




