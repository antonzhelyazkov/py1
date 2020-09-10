import ftplib
import getopt
import json
import os
import sys
import re

import mysql.connector
import requests

config_file = "./config.json"

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


#############


def parse_log_file(log_file):
    string_to_search = '[Output file information #1]'
    data_string = open(log_file, encoding='utf16').read()
    if string_to_search in data_string:
        return True
    else:
        return False


def logfile_to_name(log_filename):
    pattern = "\[(.*)\]"
    matches = re.findall(pattern, log_filename)
    return matches[0]


def update_status(issue_id_local, status):
    vod_conn = mysql.connector.connect(
        host=config_data['mysql_host'],
        user=config_data['mysql_user'],
        password=config_data['mysql_pass'],
        database=config_data['mysql_db']
    )
    sql = "update video_prod set status = %s where id = %s"
    val = (status, issue_id_local)
    update = vod_conn.cursor()
    update.execute(sql, val)
    vod_conn.commit()
    vod_conn.close()


def check_status(file_to_check):
    vod_conn = mysql.connector.connect(
        host=config_data['mysql_host'],
        user=config_data['mysql_user'],
        password=config_data['mysql_pass'],
        database=config_data['mysql_db']
    )

    cursor = vod_conn.cursor()
    cursor.execute("SELECT sql_no_cache id from video_prod where status = "
                   "\"ready_for_cut\" and ts_file_name = \"" + file_to_check + "\"")
    result = cursor.fetchone()

    if result:
        return True, result[0]
    else:
        return False, result


def ftp_check():
    ftp_path = "log/"
    ftp_map = {}
    for ftp_server in config_data['ftp_hosts']:
        tmp_arr = []
        session = ftplib.FTP(ftp_server)
        session.login(user=config_data['out_ftp_user'], passwd=config_data['out_ftp_pass'])

        for name, facts in session.mlsd(ftp_path):
            filename = config_data['dst_dir'] + name
            localfile = open(filename, 'wb')
            session.retrbinary('RETR ' + ftp_path + name, localfile.write, 1024)
            localfile.close()
            if parse_log_file(filename):
                tmp_arr.append(logfile_to_name(name))
            os.remove(filename)
        session.close()
        ftp_map[ftp_server] = tmp_arr
    return ftp_map


def ftp_get_file(ftp_server, file_to_get, issue_id_local):
    local_mp4 = open(config_data['tmp_dir'] + "/" + file_to_get, 'wb')
    remote_mp4 = ftp_check_join(file_to_get, ftp_server)
    session = ftplib.FTP(ftp_server)
    session.login(user=config_data['out_ftp_user'], passwd=config_data['out_ftp_pass'])
    update_status(issue_id_local, "download_started")
    session.retrbinary('RETR ' + remote_mp4, local_mp4.write, 2048)
    update_status(issue_id_local, "download_finished")
    session.close()


def ftp_remove_files(file_to_get, ftp_server):
    ftp_path = "log/"
    session = ftplib.FTP(ftp_server)
    session.login(user=config_data['out_ftp_user'], passwd=config_data['out_ftp_pass'])

    for name, facts in session.mlsd(ftp_path):
        if file_to_get in name:
            print(ftp_path + name)
            session.delete(ftp_path + name)
    session.delete(ftp_check_join(file_to_get, ftp_server))
    session.close()


def ftp_check_join(file_to_get, ftp_server):
    files_arr = []
    session = ftplib.FTP(ftp_server)
    session.login(user=config_data['out_ftp_user'], passwd=config_data['out_ftp_pass'])

    for name, facts in session.mlsd():
        if facts['type'] == "file":
            files_arr.append(name)
    session.close()

    if file_to_get in files_arr:
        return file_to_get
    elif file_to_get.replace('.mp4', ' - Join.mp4') in files_arr:
        return file_to_get.replace('.mp4', ' - Join.mp4')
    else:
        return None


def encode_files_qm2(file_to_encode, issue_id_local):
    input_file = config_data['tmp_dir'] + "/" + file_to_encode
    file_qm2 = config_data['out_dir'] + "/" + file_to_encode.replace('.mp4', '_qm2.mp4')

    if verbose:
        ffmpeg_bin = config_data['ffmpeg_bin']
    else:
        ffmpeg_bin = config_data['ffmpeg_bin'] + " -hide_banner -loglevel quiet"

    ffmpeg_command = "{} -y -hwaccel cuvid -deint 1 -vsync 1 -drop_second_field 1 " \
                     "-c:v h264_cuvid -i {} " \
                     "-c:v h264_nvenc -filter:v scale_npp=w=640:h=360 -profile:v high -g:v 80 -b:v 600000 " \
                     "-maxrate:v 1000000 -bufsize:v 1000000 -preset:v slow -c:a libfdk_aac -b:a 48000 -ac 2 -ar 48k " \
                     "-f mp4 {}" \
        .format(ffmpeg_bin, input_file, file_qm2)

    update_status(issue_id_local, "encoding_qm2_started")
    os.system(ffmpeg_command)
    update_status(issue_id_local, "encoding_qm2_finished")

    return os.path.basename(file_qm2)


def encode_files_sd2(file_to_encode, issue_id_local):
    input_file = config_data['tmp_dir'] + "/" + file_to_encode
    file_sd2 = config_data['out_dir'] + "/" + file_to_encode.replace('.mp4', '_sd2.mp4')

    if verbose:
        ffmpeg_bin = config_data['ffmpeg_bin']
    else:
        ffmpeg_bin = config_data['ffmpeg_bin'] + " -hide_banner -loglevel quiet"

    ffmpeg_command = "{} -y -hwaccel cuvid -deint 1 -vsync 1 -drop_second_field 1 " \
                     "-c:v h264_cuvid -i {} " \
                     "-c:v h264_nvenc -filter:v scale_npp=w=854:h=480 -profile:v high -g:v 80 -b:v 1600000 " \
                     "-maxrate:v 2000000 -bufsize:v 2000000 -preset:v slow -c:a libfdk_aac -b:a 96000 -ac 2 -ar 48k " \
                     "-f mp4 {}" \
        .format(ffmpeg_bin, input_file, file_sd2)

    update_status(issue_id_local, "encoding_qm2_started")
    os.system(ffmpeg_command)
    update_status(issue_id_local, "encoding_qm2_finished")

    return os.path.basename(file_sd2)


def encode_files_fhd(file_to_encode, issue_id_local):
    input_file = config_data['tmp_dir'] + "/" + file_to_encode
    file_fhd = config_data['out_dir'] + "/" + file_to_encode.replace('.mp4', '_fhd.mp4')

    if verbose:
        ffmpeg_bin = config_data['ffmpeg_bin']
    else:
        ffmpeg_bin = config_data['ffmpeg_bin'] + " -hide_banner -loglevel quiet"

    ffmpeg_command = "{} -y -hwaccel cuvid -deint 1 -vsync 1 -drop_second_field 1 " \
                     "-c:v h264_cuvid -i {} " \
                     "-c:v h264_nvenc -filter:v scale_npp=w=1920:h=1080 -profile:v high -g:v 80 -b:v 3600000 " \
                     "-maxrate:v 4000000 -bufsize:v 4000000 -preset:v slow -c:a libfdk_aac -b:a 128000 -ac 2 -ar 48k " \
                     "-f mp4 {}" \
        .format(ffmpeg_bin, input_file, file_fhd)

    update_status(issue_id_local, "encoding_fhd_started")
    os.system(ffmpeg_command)
    update_status(issue_id_local, "encoding_fhd_finished")

    return os.path.basename(file_fhd)


def insert_upload(file_to_register):
    ip = requests.get('https://checkip.amazonaws.com').text.strip()
    split_file_name = file_to_register.split("_")
    quality_suffix = split_file_name[4].split(".")
    vod_conn = mysql.connector.connect(
        host=config_data['mysql_host'],
        user=config_data['mysql_user'],
        password=config_data['mysql_pass'],
        database=config_data['mysql_db']
    )
    sql = "INSERT INTO upload_mp4(enc_ip, mtag, issue_name, quality) VALUES(%s, %s, %s, %s)"
    val = (ip, split_file_name[0], file_to_register, quality_suffix[0])
    curs = vod_conn.cursor()
    curs.execute(sql, val)
    vod_conn.commit()
    vod_conn.close()


#############

config_open = open(config_file, encoding='utf-8')
config_data = json.load(config_open)

pid_file_path = config_data['pid_file_path']

file_name = os.path.basename(sys.argv[0]).split(".")
pid_file = pid_file_path.rstrip('/') + "/" + file_name[0] + ".pid"
# print(pid_file)

isPID = os.path.isfile(pid_file)
if isPID:
    print("PID file exists " + pid_file)
    sys.exit()
else:
    f = open(pid_file, "w")
    f.write(str(os.getpid()))
    f.close()

for server_ip, issue_arr in ftp_check().items():
    print(server_ip, issue_arr)
    for issue in issue_arr:
        # print(issue)
        issue_status, issue_id = check_status(issue)
        print(issue_status, issue_id)
        if issue_status:
            print(server_ip, issue, issue_id)
            print(f"join {ftp_check_join(issue, server_ip)}")
            ftp_get_file(server_ip, issue, issue_id)
            qm2 = encode_files_qm2(issue, issue_id)
            insert_upload(qm2)
            sd2 = encode_files_sd2(issue, issue_id)
            insert_upload(sd2)
            fhd = encode_files_fhd(issue, issue_id)
            insert_upload(fhd)
            ftp_remove_files(issue, server_ip)
            print(qm2, sd2, fhd)
os.remove(pid_file)
