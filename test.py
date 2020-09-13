import json
import os
import sys
import getopt
import logging

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

config_open = open(config_file, encoding='utf-8')
config_data = json.load(config_open)

file_name = os.path.basename(sys.argv[0]).split(".")
log_file = config_data['log_dir'] + "/" + file_name + ".log"

print(log_file)
