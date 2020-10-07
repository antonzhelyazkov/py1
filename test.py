import datetime
import logging
import time
from datetime import datetime, timedelta
import getopt
import json
import os
import sys
import mysql.connector

verbose = False
config_file = "./config.json.json"
log_dir = "."
argv = sys.argv[1:]

try:
    opts, argv = getopt.getopt(argv, "c:d:v", ["config=", "verbose", "db="])
except getopt.GetoptError as err:
    print(err)
    opts = []

for opt, arg in opts:
    if opt in ['-c', '--config']:
        config_file = arg
    if opt in ['-v', '--verbose']:
        verbose = True
    if opt in ['-d', '--db']:
        db_config = arg
    else:
        print("HELP")


def print_log(debug, message):
    try:
        current_log_dir = config_data['log_dir']
    except Exception:
        current_log_dir = log_dir

    if os.path.isdir(current_log_dir):
        log_file_name = os.path.basename(sys.argv[0]).split(".")
        script_log = current_log_dir + "/" + log_file_name[0] + ".log"
        logging.basicConfig(filename=script_log, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
        logging.info(message)
        if debug is True:
            print(message)

    else:
        print(f"log directory does not exist {current_log_dir}")
        exit(1)


try:
    config_open = open(config_file, encoding='utf-8')
except FileNotFoundError as e:
    print_log(verbose, e)
    exit(1)
else:
    config_data = json.load(config_open)
