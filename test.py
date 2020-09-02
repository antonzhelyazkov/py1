# import datetime
import json
import os.path
import sys
from datetime import datetime
# import dateutil.parser
# import pytz
# import requests
# import tzlocal
# import time
import getopt

currentDate = datetime.today().strftime('%Y-%m-%d')
map_file = "./map.json"
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

is_config = os.path.isfile(config_file)
if is_config:
    print("json config exists " + config_file)
else:
    print("json config not found " + config_file)
    sys.exit()

config_open = open(config_file, encoding='utf-8')
config_data = json.load(config_open)
dst_dir = config_data['dst_dir'].rstrip('/')

header = {
    'X-Api-Key': config_data['api_key']
}

json_open = open(map_file, encoding='utf-8')
data = json.load(json_open)


def get_key(val):
    for key, value in config_data['media'].items():
        if val == value:
            return key

    return "key doesn't exist"


for media in config_data['media'].values():
    print(media)
    print(get_key(media))

for host in config_data['ftp_hosts']:
    print(host)

for media in config_data['media']:
    path_json = config_data['dst_dir'].rstrip('/') + '/' + media + '.json'
    print(path_json)
    isJsonFile = os.path.isfile(path_json)
    if isJsonFile:
        print("json file " + path_json + " found")
    else:
        print("json file " + path_json + " NOT found")
