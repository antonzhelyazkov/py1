import datetime
import ftplib
import json
import os
import sys
import getopt
import logging
from datetime import datetime, timedelta

config_file = "./config.json"
verbose = False
file_to = "d:/application_security_verification_report_2019_04_03.pdf"

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


def modify_stamp_to_unix_timestamp(date_stamp):
    year = int(date_stamp[0] + date_stamp[1] + date_stamp[2] + date_stamp[3])
    month = int(date_stamp[4] + date_stamp[5])
    day = int(date_stamp[6] + date_stamp[7])
    hour = int(date_stamp[8] + date_stamp[9])
    minutes = int(date_stamp[10] + date_stamp[11])
    seconds = int(date_stamp[12] + date_stamp[13])
    issue_datestamp = datetime(year, month, day, hour, minutes, seconds)
    return round(datetime.timestamp(issue_datestamp))

# 2020 09 16 07 06 38


def ftp_clear_old_files(ftp_session):
    yesterday = datetime.today() - timedelta(days=1)
    time_yesterday = round(datetime.timestamp(yesterday))
    for name, facts in ftp_session.mlsd():
        # logger.warning(f"{time_yesterday} {modify_stamp_to_unix_timestamp(facts['modify'])}")
        if int(time_yesterday) > int(modify_stamp_to_unix_timestamp(facts['modify'])):
            print(f"try to delete {name}")
            # ftp_session.delete(name)


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


if ftp_upload(file_to):
    print("OK")
else:
    print("Error")
