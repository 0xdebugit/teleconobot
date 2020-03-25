import requests
import json
import os

from secret import tokens

apiUrl = tokens.TELEGRAM_API_URL
testgroup = tokens.TELEGRAM_TEST_GROUP
prodgroup = tokens.TELEGRAM_COVID_GROUP
bot_id = tokens.TELEGRAM_BOT_ID


def pushMessage(text,parseMode,grp):
	msgLogPath = 'temp/lastUpdate.json'
	group = testgroup
	if(grp == 'prod'):
		group = prodgroup
	payload = {
		'chat_id' : group,
		'text' : text,
		'parse_mode' : parseMode
	}
	res = requests.post(apiUrl+'sendMessage',data=payload)
	# print(type(json.loads(res.content)))
	with open(msgLogPath,'w') as f:
		data = res.content.decode('utf-8')
		json.dump(json.loads(data),f)
	return res.content

def editMessage(text,parseMode,grp):
	msgLogPath = 'temp/lastUpdate.json'
	group = testgroup
	if(grp == 'prod'):
		group = prodgroup	
	if(not os.path.exists(msgLogPath)):
		return pushMessage(text,parseMode)
	with open(msgLogPath,'r') as f:
		data = json.load(f)
		message_id = data['result']['message_id']
		print(message_id)
	payload = {
		'chat_id' : group,
		'text' : text,
		'message_id' : message_id,
		'parse_mode' : parseMode
	}
	res = requests.post(apiUrl+'editMessageText',data=payload)
	return res.content

def uploadPic():
	res = requests.post(apiUrl+'editMessageText',data=payload)

def getChat():
	res = requests.get(apiUrl+'getChat?chat_id='+group)
	print(res.content)