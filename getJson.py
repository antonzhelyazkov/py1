#!/usr/bin/python3

import datetime
import json
import os.path
import sys
from datetime import datetime
import dateutil.parser
import pytz
import requests
import tzlocal
import time
import getopt


currentDate = datetime.today().strftime('%Y-%m-%d')
config_file = "./config.json"

argv = sys.argv[1:]

try:
    opts, argv = getopt.getopt(argv, "c:", ["config="])
except getopt.GetoptError as err:
    print(err)
    opts = []

for opt, arg in opts:
    if opt in ['-c', '--config']:
        config_file = arg
    else:
        print("HELP")


def utc_to_local(utcTime):
    utctime = dateutil.parser.parse(utcTime)
    local_timezone = str(tzlocal.get_localzone())
    localtime = utctime.astimezone(pytz.timezone(local_timezone))
    localtime = str(datetime.strptime(datetime.strftime(localtime, "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))
    timestamp = time.strptime(localtime, "%Y-%m-%d %H:%M:%S")
    unix_time_local = str(time.mktime(timestamp))
    return unix_time_local.replace('.0', '')


def get_key(val):
    for key, value in config_data['media'].items():
        if val == value:
            return key

    return "key doesn't exist"


# checks

is_config = os.path.isfile(config_file)
if is_config:
    print("json config exists " + config_file)
else:
    print("json config not found " + config_file)
    sys.exit()

config_open = open(config_file, encoding='utf-8')
config_data = json.load(config_open)

dst_dir = config_data['dst_dir'].rstrip('/')
map_file = config_data['map_file']

isdir = os.path.isdir(dst_dir)
if isdir:
    print("json directory exists " + dst_dir)
else:
    print("json directory does not exist " + dst_dir + " Try mkdir.")
    sys.exit()

isMapFile = os.path.isfile(map_file)
if isMapFile:
    print("json file " + map_file + " found")
else:
    print("json file " + map_file + " NOT found")
    sys.exit()

header = {
    'X-Api-Key': config_data['api_key']
}

json_open = open(map_file, encoding='utf-8')
data = json.load(json_open)

# main

for media in config_data['media'].values():
    collect_data = []
    currentUrl = config_data['api_url'] + media + "/" + currentDate
    response = requests.get(currentUrl, headers=header)
    result = response.json()
    for items in result['bc']:
        startTime = items['Event']['StartTime']
        endTime = items['Event']['EndTime']

        for title in items['Content']['Title']:
            issueName = title["Value"]

            if issueName in data:
                issueInfo = {"name": data[issueName],
                             "start": utc_to_local(startTime),
                             "end": utc_to_local(endTime),
                             "processed": "false"
                             }
                collect_data.append(issueInfo)

    with open(dst_dir + "/" + get_key(media) + ".json", 'w') as json_file:
        json.dump(collect_data, json_file)
        json_file.close()
