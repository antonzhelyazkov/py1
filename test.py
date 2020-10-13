import json
import os
import sys
import getopt
import logging
import re

config_file = "./config.json"
verbose = False
file_to_upload = "d:/application_security_verification_report_2019_04_03.pdf"


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


def try_files(file):
    if os.path.isfile(file):
        return True
        print_log(verbose, f"file exists {file}")
    else:
        return True
        print_log(verbose, f"file DOES NOT exist {file}")