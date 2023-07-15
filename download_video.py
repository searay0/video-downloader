import os
import shlex
import subprocess
import traceback
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import m3u8

REFERRER = "https://google.com"
PLAYLIST_LIST_FILE = "z_list.txt"
USERAGENT = "Mozilla/5.0"
MAX_WORKERS = 1

playlist = None
playlist_list = []
num_start = 1


def get_playlist(url):
    global playlist
    req = urllib.request.Request(url)
    req.add_header("Referer", REFERRER)
    req.add_header("User-Agent", USERAGENT)
    with urllib.request.urlopen(req) as f:
        response = f.read().decode("utf-8")
        playlist = m3u8.loads(response)


def get_url_prologue(url):
    str = url.split("/")[1:-1]
    str = "https:/" + "/".join(str) + "/"
    return str


def wget_file(link, filename):
    command = shlex.split(
        f'wget -c {link} -O {filename}.ts -U "{USERAGENT}" --header="Referer: {REFERRER}"'
    )
    process = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
    while True:
        output = process.stdout.readline()
        print(output.strip())
        return_code = process.poll()
        if return_code is not None:
            print("RETURN CODE", return_code)
            for output in process.stdout.readlines():
                print(output.strip())
            break


def dl_ts_chunk(task_id, url):
    wget_file(url, task_id)
    return "Task ID: " + task_id


def create_thread_pool(url):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        global playlist
        futures = []
        task_id = 1
        for segment in playlist.segments:
            futures.append(
                executor.submit(
                    dl_ts_chunk,
                    str(task_id).zfill(5),
                    f"{get_url_prologue(url)}{segment.uri}",
                )
            )
            task_id += 1
        for future in as_completed(futures):
            try:
                print(future.result())
            except Exception as e:
                print("ERROR: ", str(e))
                # traceback.print_exc()


def get_playlist_list():
    global playlist_list
    with open(PLAYLIST_LIST_FILE, "r") as file:
        for line in file:
            playlist_list.append(line.strip())


def download_video(url):
    if url == "":
        print("URL is blank.")
        exit()
    get_playlist(url)
    if playlist is None:
        print("Playlist failed to load.")
        exit()
    create_thread_pool(url)


def convert_video(file_name):
    os.system(f"cat *.ts > temp.ts")
    os.system(f"ffmpeg -i temp.ts -acodec copy -vcodec copy {file_name}.mp4")
    os.system(f"rm -fr *.ts")


get_playlist_list()
for playlist in playlist_list:
    download_video(playlist)
    convert_video(str(num_start).zfill(2))
    num_start += 1
