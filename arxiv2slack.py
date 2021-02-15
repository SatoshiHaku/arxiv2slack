from datetime import datetime
from time import sleep
import json
import re
import sys
import urllib.parse
import urllib.request
import requests
import pickle
import os
import datetime
from gummy.cli import translate_journal
import passes


DELETE_URL = "https://slack.com/api/chat.delete"
HISTORY_URL = "https://slack.com/api/conversations.history"


#TERM = 60 * 60 * 24 * 7  # 1 week
TERM = 60 * 60 * 24 * 2   # 2 day 

def clean_old_message(channel_id):
    print('Start cleaning message at channel "{}".'.format(channel_id))
    current_ts = int(datetime.now().strftime('%s'))
    messages = get_message_history(channel_id)
    print(messages)
    for message in messages:
        if current_ts - int(re.sub(r'\.\d+$', '', message['ts'])) > TERM:
            delete_message(channel_id, message['ts'])
            sleep(1)


def get_message_history(channel_id, count=800):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {
        'token': passes.API_TOKEN, #save in passes.py
        'channel': channel_id,
        'count': str(count)
    }

    req_url = '{}?{}'.format(HISTORY_URL, urllib.parse.urlencode(params))
    req = urllib.request.Request(req_url, headers=headers)

    message_history = []
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode("utf-8"))
        if 'messages' in data:
            message_history = data['messages']

    return message_history


def delete_message(channel_id, message_ts):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {
        'token': passes.API_TOKEN, #save in passes.py
        'channel': channel_id,
        'ts': message_ts
    }

    req_url = '{}?{}'.format(DELETE_URL, urllib.parse.urlencode(params))
    req = urllib.request.Request(req_url, headers=headers)
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode("utf-8"))
        if 'ok' not in data or data['ok'] is not True:
            print('Failed to delete message. ts: {}'.format(message_ts))


def parse(data, tag):
    # parse atom file
    # e.g. Input :<tag>XYZ </tag> -> Output: XYZ

    pattern = "<" + tag + ">([\s\S]*?)<\/" + tag + ">"
    if all:
        obj = re.findall(pattern, data)
    return obj




def search_and_send(query, start, ids, api_url):
    while True:
        counter = 0
        # url of arXiv API
        # If you want to customize, please change here.
        # detail is shown here, https://arxiv.org/help/api/user-manual
        url = 'http://export.arxiv.org/api/query?search_query=submittedDate:[' + previousdate.strftime(
            '%Y%m%d') + '0000+TO+' + basedate.strftime('%Y%m%d') + '0000]+AND+' + query
        # Get returned value from arXiv API
        data = requests.get(url).text
        # Parse the returned value
        entries = parse(data, "entry")
        for entry in entries:
            # Parse each entry
            url = parse(entry, "id")[0]
            #print(url)
            
            if not(url in ids):
                title = parse(entry, "title")[0]
                # abstract = parse(entry, "summary")[0]
                date = parse(entry, "published")[0]
                #post to slack
                message = "\n".join(["=" * 10, "No." + str(counter + 1), "Title:  " + title, "URL: " + url, "Published: " + date])
                requests.post(api_url, json={"text": message})
                #translation by gummy
                translate_journal([str(url), '-pdf',passes.savefolder+title +'.pdf']) #save in passes.py
            
                
                ids.append(url)
                counter = counter + 1
                #if counter == 10:
                if counter == 10: # 10 articles a day
                    return 0
        if counter == 0 and len(entries) < 100:
            requests.post(api_url, json={"text": "Currently, there is no available papers"})
            return 0
        elif counter == 0 and len(entries) == 100:
            # When there is no available paper and full query
            start = start + 100


if __name__ == "__main__":
    basedate = datetime.date.today()
    previousdate = basedate + datetime.timedelta(days=-5)
    print("Publish")
    # Set URL of API
    # Please change here
    api_url = passes.api_url_slack #save in passes.py
    # Load log of published data
    if os.path.exists("published.pkl"):
        ids = pickle.load(open("published.pkl",'rb'))
    else:
        ids = []
    # Query for arXiv API
    # Please change here
    query = "((abs:spin-orbit torque)+OR+(abs:spin-torque)" + \
           "+OR+(abs:orbital Hall)+ OR + (abs:spintronics)+ OR + (abs:Rashba-Edelstein)" \
            "+ OR + (abs:spin Hall)+ OR + (abs:Rashba))"    
    #query = "(abs:spin-orbit torque)"
    start = 0
    # Post greeting to your Slack
    requests.post(api_url, json={"text": "Hello!!"})
    # Call function
    search_and_send(query, start, ids, api_url)
    # Update log of published data
    pickle.dump(ids, open("published.pkl", "wb"))
    
    clean_old_message(passes.channelid) #delete privious posts  #save in passes.py
