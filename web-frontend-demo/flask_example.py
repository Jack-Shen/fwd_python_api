from flask import Flask, render_template, flash, request
import sys
import json
import os


#set up network 
network =  137407
#define network here
###########################
import logging
import sys
sys.path.append("..")
import fwd_json
from fwd_json import fwdApi 
try: 
    username = os.environ['fwd_saas_user']
    token = os.environ['fwd_saas_token']

    fwd = fwdApi("https://fwd.app/api", username, token,network, {})
    print("getting latest snapshot")
    latest_snap = fwd.get_snapshot_latest(network).json()['id']
except KeyError:
    print("issue with tokens")
    pass

app = Flask(__name__)
@app.route('/form')
def form():
    return render_template("form.html", form=form)

@app.route("/data", methods=['POST', 'GET'])
def data():
    if request.method == 'GET':
        return f"go to / to submit query"
    if request.method == 'POST':
        form_data = request.form
        print(form_data, file=sys.stdout) 
        result = fwd.get_path_search(latest_snap,form_data['src'],form_data['dst']).json()
        print(result, file=sys.stdout)
        return render_template('data.html',form=form_data, result=json.dumps(result, indent=4, sort_keys=True))    

if __name__ == "__main__":
    app.run()
    
