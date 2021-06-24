#set up network 
network =  137407
#define network here
###########################
import logging
import sys
sys.path.append("..")
import fwd_json
from fwd_json import fwdApi

logging.basicConfig(level=logging.DEBUG)

import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

#set up forward
try: 
    username = os.environ['fwd_saas_user']
    token = os.environ['fwd_saas_token']

    fwd = fwdApi("https://fwd.app/api", username, token,network, {})
    print("getting latest snapshot")
    latest_snap = fwd.get_snapshot_latest(network).json()['id']
except KeyError:
    print("issue with tokens")
    pass


# Install the Slack app and get xoxb- token in advance
app = App(token=os.environ['SLACK_BOT_TOKEN'])


@app.command("/hello-socket-mode")
def hello_command(ack, body):
    user_id = body["user_id"]
    ack(f"Hi <@{user_id}>! this bot is working!")

@app.command("/path")
def path_command(ack,say, body): 
    say("user `{}`".format(body['user_name']))
    srcIP = body['text'].split(' ')[0]
    dstIP = body['text'].split(' ')[1]
    data = fwd.get_path_search(latest_snap,srcIP, dstIP).json()
    blocks=gen_block(srcIP, dstIP, data)
    say(blocks=gen_block(srcIP, dstIP, data), text="block test")
    ack()

@app.command("/checkconfig")
def device_config(ack, say, body): 
    queryId = "Q_b7ed24370895b73d6ddbef0b81cffe04d22ae6f5"
    say("user `{}`".format(body['user_name']))
    device_name = body['text'].split(' ')[0]
    device_config = body['text'].split(' ', 1)[1]
    payload = {"deviceList": ["{}".format(device_name)], "config": "{}".format(device_config)}
    response = fwd.post_nqe_para_check(queryId, payload)
    say("check `{}` for `{}`".format(device_name, device_config))
    say("{}".format(response))
    say("{}".format(payload))
    
    ack()

@app.command("/checkbgp")
def check_bgp(ack, say, body):

    queryId = "Q_8178355cfc658ab46cac0f07f2b033f68fa92c80"
    device_name = body['text']
    payload = {"deviceList": ["{}".format(body['text'])]}
    response = fwd.post_nqe_para_check(queryId, payload)
    say("user `{}`".format(body['user_name']))
    say("check `{}` for bgp neighbor".format(device_name))
    say("{}".format(response))
    ack()
@app.command("/getdevice")
def get_device(ack, say, body): 

    queryId = "Q_15e99a7cc9ba42cfd65b03237523e6ef29f7c60a"
    device_name = body['text']
    payload = {"deviceList": ["{}".format(body['text'])]}
    response = fwd.post_nqe_para_check(queryId, payload)
    print(response)
    say("user `{}`".format(body['user_name']))
    say("get `{}` information".format(device_name))
    say("{}".format(response))
    ack()
   
@app.command("/help")
def help(ack, say, body): 
   say("Hi `{}`".format(body['user_name']))
   say("This is the help page for Forward Api Bot v0.1")
   say("/checkconfig <device_name> <config>")
   say("/path <src> <dst>")
   say("/checkbgp <device_name>")
   say("/getdevice <device_name>")
   say("/help")
   ack()

@app.event("app_mention")
def event_test(event, say):
    say(f"Hi there, <@{event['user']}>!")


def ack_shortcut(ack):
    ack()


@app.view("socket_modal_submission")
def submission(ack):
    ack()

def gen_block(src, dst, path_data):
    path_info = path_data['info']['paths'][0]
    block= [
	{
		"type": "header",
		"text": {
			"type": "plain_text",
			"text": f'src: {src} dst: {dst}'
		}
	}]
    for index, i in enumerate(path_info['hops']):
        deviceName = i['deviceName']
        egressInt= i['egressInterface']
        ingressInt = i['ingressInterface']
        block.append({"type": "section", "text":{ "type": "mrkdwn", "text": f'*HOP{index}*--> {deviceName}'}})
        block.append({"type": "section", "text":{ "type": "mrkdwn", "text": f'IN: {ingressInt}'}})
        block.append({"type": "section", "text":{ "type": "mrkdwn", "text": f'OUT: {egressInt}'}})
    block.append({
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Path result in fwd.app", 
			},
			"accessory": {
				"type": "button",
				"text": {
					"type": "plain_text",
					"text": "Link",
					"emoji": True
				},
				"value": "click_me_123",
				"url": path_data['queryUrl'],
				"action_id": "button-action"
			}})
    block.append({
			"type": "divider"
		}) 
    return block
if __name__ == "__main__":
    # export SLACK_APP_TOKEN=xapp-***
    # export SLACK_BOT_TOKEN=xoxb-***
    SocketModeHandler(app, os.environ['SLACK_APP_TOKEN']).start()
