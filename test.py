import datetime
import ftplib
import json
import os
import sys
import getopt
import logging

config_file = "./config.json"
verbose = False
file_to_uload = "d:/10000000_572165052985141_4136437991520337920_n.mp4"

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


def modify_stamp_to_unixtimestamp(date_stamp):
    dt = datetime.datetime(int(date_stamp), format('%Y%m%d%H%M%S'))
    return dt

#2020 09 16 07 06 38


def ftp_clear_old_files(ftp_session):
    for name, facts in ftp_session.mlsd():
        print(modify_stamp_to_unixtimestamp(facts['modify']))


def ftp_upload(file_to_upload):
    check_flag = False
    for ftp_server in config_data['ftp_hosts']:
        session = ftplib.FTP(ftp_server, config_data['ftp_user'], config_data['ftp_pass'])
        ftp_clear_old_files(session)
        file = open(file_to_upload, 'rb')  # file to send
        session.storbinary('STOR ' + os.path.basename(file_to_upload), file)  # send the file
        file.close()  # close file and FTP
        session.quit()
        check_flag = True

    return check_flag


if ftp_upload(file_to_uload):
    print("OK")
else:
    print("Error")
