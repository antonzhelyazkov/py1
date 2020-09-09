import ftplib
import getopt
import json
import os
import sys
import re

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


#############


def parse_log_file(log_file):
    string_to_search = '[Output file information #1]'
    datastring = open(log_file, encoding='utf16').read()
    if string_to_search in datastring:
        return True
    else:
        return False


def logfile_to_name(log_filename):
    pattern = "\[(.*)\]"
    matches = re.findall(pattern, log_filename)
    for i in matches:
        return i


def ftp_check():
    ftp_path = "log/"
    ftp_map = {}
    for ftp_server in config_data['ftp_hosts']:
        tmp_arr = []
        session = ftplib.FTP(ftp_server)
        session.login(user=config_data['out_ftp_user'], passwd=config_data['out_ftp_pass'])
        for name, facts in session.mlsd(ftp_path):
            filename = 'd:/' + name
            localfile = open(filename, 'wb')
            session.retrbinary('RETR ' + ftp_path + name, localfile.write, 1024)
            localfile.close()
            if parse_log_file(filename):
                tmp_arr.append(logfile_to_name(name))
            os.remove(filename)
        session.close()
        ftp_map[ftp_server] = tmp_arr
    return ftp_map


#############

config_open = open(config_file, encoding='utf-8')
config_data = json.load(config_open)

pid_file_path = config_data['pid_file_path']

file_name = os.path.basename(sys.argv[0]).split(".")
pid_file = pid_file_path.rstrip('/') + "/" + file_name[0] + ".pid"
print(pid_file)

isPID = os.path.isfile(pid_file)
if isPID:
    print("PID file exists " + pid_file)
    sys.exit()
else:
    f = open(pid_file, "w")
    f.write(str(os.getpid()))
    f.close()

for key, value in ftp_check().items():
    for val in value:
        print(key, val)

os.remove(pid_file)
