import logging
import os.path
import sys
import json
from datetime import datetime, timedelta
import time
import getopt
import shutil
import ffmpeg
import ftplib
import mysql.connector

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

currentTS = int(time.time())


def create_chlist(start_time, end_time, chunk_list, media_name):
    ts_arr = []
    chunks = os.listdir(path_chunks)
    for chunk in chunks:
        if chunk.endswith(config_data['chunk_extension']):
            ts_chunk = chunk.replace(config_data['chunk_extension'], '')
            if end_time >= int(ts_chunk) >= start_time:
                ts_arr.append(int(ts_chunk))

    ts_arr.sort()

    for ts_item in ts_arr:
        chunk_name = str(ts_item) + ".mp4"
        path_chunk_name = path_chunks + "/" + chunk_name
        if os.path.isfile(path_chunk_name):
            fh = open(chunk_list, "a")
            fh.write("file '" + path_chunks + "/" + chunk_name + "'\n")
            fh.close()


def join_files(chunk_list, dst_file):
    ffmpeg_command = config_data['ffmpeg_bin'] + " -hide_banner -loglevel quiet -safe 0 -f concat -i " + chunk_list + \
                     " -c copy " + dst_file
    print(ffmpeg_command)
    os.system(ffmpeg_command)


def check_duration(dst_file, start_time, end_time):
    stream = ffmpeg.probe(dst_file, cmd=config_data['ffprobe_bin'])
    duration = float(stream['format']['duration'])
    file_duration = int(round(duration))
    expected_file_duration = end_time - start_time
    print(file_duration, expected_file_duration)
    if abs(expected_file_duration - file_duration) < config_data['difference']:
        return True
    else:
        return False


def modify_stamp_to_unix_timestamp(date_stamp):
    year = int(date_stamp[0] + date_stamp[1] + date_stamp[2] + date_stamp[3])
    month = int(date_stamp[4] + date_stamp[5])
    day = int(date_stamp[6] + date_stamp[7])
    hour = int(date_stamp[8] + date_stamp[9])
    minutes = int(date_stamp[10] + date_stamp[11])
    seconds = int(date_stamp[12] + date_stamp[13])
    issue_datestamp = datetime(year, month, day, hour, minutes, seconds)
    return round(datetime.timestamp(issue_datestamp))


def ftp_clear_old_files(ftp_session):
    yesterday = datetime.today() - timedelta(days=1)
    time_yesterday = round(datetime.timestamp(yesterday))
    for name, facts in ftp_session.mlsd():
        issue_time = int(modify_stamp_to_unix_timestamp(facts['modify']))
        logger.warning(f"INFO {time_yesterday} {issue_time}")
        if int(time_yesterday) > issue_time:
            logger.warning(f"DELETE {name} {time_yesterday} {issue_time}")
            ftp_session.delete(name)


def ftp_upload(file_to_upload):
    check_flag = False
    for ftp_server in config_data['ftp_hosts']:
        session = ftplib.FTP(ftp_server, config_data['ftp_user'], config_data['ftp_pass'])
        file = open(file_to_upload, 'rb')  # file to send
        session.storbinary('STOR ' + os.path.basename(file_to_upload), file)  # send the file
        file.close()  # close file and FTP
        ftp_clear_old_files(session)
        session.quit()
        check_flag = True

    return check_flag


def insert_mysql(media_name, issue):
    vod_conn = mysql.connector.connect(
        host=config_data['mysql_host'],
        user=config_data['mysql_user'],
        password=config_data['mysql_pass'],
        database=config_data['mysql_db']
    )

    sql = "INSERT INTO video_prod (media_tag, issue_name, ts_file_name, status) VALUES (%s, %s, %s, %s)"
    val = (media_name, issue, issue + '.mp4', "ready_for_cut")
    curs = vod_conn.cursor()
    curs.execute(sql, val)
    vod_conn.commit()
    vod_conn.close()


# checks

is_config = os.path.isfile(config_file)
if is_config:
    print("json config exists " + config_file)
else:
    print("json config not found " + config_file)
    sys.exit()

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


dst_root = config_data['tmp_dir'].rstrip('/')
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

isFFMPEG = os.path.isfile(config_data['ffmpeg_bin'])
if isFFMPEG:
    print("ffmpeg file " + config_data['ffmpeg_bin'] + " found")
else:
    print("ffmpeg file " + config_data['ffmpeg_bin'] + " NOT found")
    sys.exit()

isFFPROBE = os.path.isfile(config_data['ffprobe_bin'])
if isFFPROBE:
    print("ffprobe file " + config_data['ffprobe_bin'] + " found")
else:
    print("ffprobe file " + config_data['ffprobe_bin'] + " NOT found")
    sys.exit()

for media in config_data['media']:
    path_json = config_data['dst_dir'].rstrip('/') + '/' + media + '.json'
    path_chunks = config_data['path_chunks'].rstrip('/') + '/' + media

    isdir = os.path.isdir(path_chunks)
    if isdir:
        print("json directory exists " + path_chunks)
    else:
        print("json directory does not exist " + path_chunks + " Try mkdir.")
        break

    isJsonFile = os.path.isfile(path_json)
    if isJsonFile:
        print("json file " + path_json + " found")
    else:
        print("json file " + path_json + " NOT found")
        break

    json_open = open(path_json, encoding='utf-8')
    data = json.load(json_open)
    json_open.close()

    for item in data:
        expected_start = int(item['start']) - int(config_data['seconds_before_start'])
        expected_end = int(item['end']) + int(config_data['seconds_after_end'])
        issue_name = media + "_" + item['name'] + "_" + datetime.fromtimestamp(int(item['start'])).strftime(
            "%d-%m-%Y_%H-%M")
        if expected_end < currentTS and item['processed'] == 'false':
            dst_dir = dst_root + "/" + issue_name
            print(dst_dir)
            debug_file = dst_root + "/" + issue_name + ".list"
            if os.path.exists(dst_dir):
                shutil.rmtree(dst_dir)
                os.makedirs(dst_dir)
            else:
                os.makedirs(dst_dir)
            chunk_list_file = dst_dir + "/chunks.txt"
#            ffmpeg_output_file = dst_dir + "/output.txt"
            destination_file = dst_dir + "/" + issue_name + ".mp4"
            create_chlist(expected_start, expected_end, chunk_list_file, media)
            print(f"cp {chunk_list_file} {debug_file}")
            shutil.copyfile(chunk_list_file, debug_file)
            join_files(chunk_list_file, destination_file)
            if check_duration(destination_file, expected_start, expected_end):
                print("OK", issue_name)
                if ftp_upload(destination_file):
                    item['processed'] = 'true'
                    with open(path_json, 'w') as json_file:
                        json.dump(data, json_file)
                    json_file.close()
                    shutil.rmtree(dst_dir)
                    insert_mysql(media, issue_name)
                else:
                    print("ERR problem in FTP upload", item['name'])
            else:
                print("ERR", issue_name)
                item['processed'] = 'err'
                with open(path_json, 'w') as json_file:
                    json.dump(data, json_file)
                json_file.close()
                shutil.rmtree(dst_dir)
        elif expected_end < currentTS and item['processed'] == 'true':
            print(f"DONE {issue_name}, {time.ctime(expected_start)} {time.ctime(expected_end)}")
        elif item['processed'] == 'err':
            print(f"ERR {issue_name}, {time.ctime(expected_start)} {time.ctime(expected_end)}")
        else:
            print(f"Not READY {issue_name}, {time.ctime(expected_start)} {time.ctime(expected_end)}")

os.remove(pid_file)
