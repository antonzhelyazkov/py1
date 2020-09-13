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

if verbose:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logging.basicConfig(filename=log_file, level=log_level, format='%(asctime)s:%(levelname)s:%(message)s',
                    datefmt="%Y-%m-%d %H-%M-%S")

logging.debug("qweqweqwe")
logging.info("asdasdasd")
