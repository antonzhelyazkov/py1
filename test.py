import json
import os
import sys
import getopt
import logging
import re

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

string_parse = ['bnt1_sto-procenta-budni_16-09-2020_09-10 - 1of4.mp4',
                'bnt1_sto-procenta-budni_16-09-2020_09-10 - 2of4.mp4',
                'bnt1_sto-procenta-budni_16-09-2020_09-10 - 3of4.mp4',
                'bnt1_sto-procenta-budni_16-09-2020_09-10 - 4of4 - Copy.mp4',
                'bnt1_sto-procenta-budni_16-09-2020_09-10 - 4of4.mp4']

pattern = '\d+of\d+\.mp4'
for item in string_parse:
    print(item)
    curr_match = re.search(pattern, item)
    print(curr_match)
    if curr_match:
        print("sadasda")
    else:
        print("adasdas")
