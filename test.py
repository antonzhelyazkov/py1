import json
import os
import sys
import getopt
import logging

config_file = "./config.json"
verbose = False

argv = sys.argv[1:]

try:
    opts, argv = getopt.getopt(argv, "c:v", ["config=", "verbose"])
except getopt.GetoptError as err:
    print(err)
    opts = []

for opt, arg in opts:
    if opt in ['-c', '--config']:
        config_file = arg
    if opt in ['-v', '--verbose']:
        verbose = True
    else:
        print("HELP")

config_open = open(config_file, encoding='utf-8')
config_data = json.load(config_open)

file_name = os.path.basename(sys.argv[0]).split(".")
log_file = config_data['log_dir'] + "/" + file_name[0] + ".log"

logger = logging.getLogger(__name__)
# create handlers
stream_h = logging.StreamHandler()
file_h = logging.FileHandler(log_file)

stream_h.setLevel(logging.INFO)
file_h.setLevel(logging.INFO)

formatter_stream = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
formatter_file = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if verbose:
    stream_h.setFormatter(formatter_stream)

file_h.setFormatter(formatter_file)

logger.addHandler(stream_h)
logger.addHandler(file_h)

for item in config_data['channels']:
    logger.warning(f"{item} {config_data['channels'][item]}")
