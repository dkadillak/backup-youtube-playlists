import json
import sys
from shlex import split
from os import getcwd, path, remove
from subprocess import run
from typing import Dict, Tuple, TextIO


def get_playlist_title(playlist_url:str) -> str:
    '''
    gets the title of the playlist were backing up
    :param playlist_url: the url to the given playlist, of form https://www.youtube.com/playlist?list=<your playlist id>
    :return: the name of the playlist as it appears on YouTube
    '''

    command = f'youtube-dl --get-filename -o "%(playlist_title)s" {playlist_url}'
    completed_process = run(split(command), capture_output=True)

    output = completed_process.stdout.decode().encode('utf-16', 'surrogatepass').decode('utf-16')

    return output.split('\n')[0]  # sometimes the subprocess command will return the title multiple times, make sure to grab just the title and not the title repeated


def get_length_of_playlist(playlist_url:str) -> int:
    '''
    returns the number of videos in a given playlist
    :param playlist_url: the url to the given playlist, of form https://www.youtube.com/playlist?list=<your playlist id>
    :return: the number of videos in the given playlist
    '''

    fetch_json_command = f"youtube-dl -j --flat-playlist {playlist_url}"
    fetch_json_process = run(split(fetch_json_command), capture_output=True)

    wc_command = "wc -l"
    wc_process = run(split(wc_command), input=fetch_json_process.stdout, capture_output=True)

    return int(wc_process.stdout.decode())


def build_playlist_path(playlist_title:str) -> Tuple[str, str]:
    '''
    util function to do some common string building for you
    :param playlist_title: the name of the playlist
    :return: a tuple containing the location of the folder that a playlist is backed up in (index 0) and the location of the master playlist file (index 1)
    '''
    master_playlist_file = path.join(getcwd(), 'saved-playlists', playlist_title, f'{playlist_title}_MASTER.txt')
    backed_up_path = path.join('saved-playlists', playlist_title)

    return (backed_up_path, master_playlist_file)


def get_current_playlist(playlist_title:str, playlist_url:str) -> str:
    '''
    gets all the videos currently existing in a given playlist. data retrieved for each video is a json blob.
    this function puts all json blobs in a .txt file and returns the path to that .txt file
    :param playlist_title: the title of the playlist whose videos we want to enumerate
    :param playlist_url: the url of the playlist whose videos we want to enumerate
    :return: path to file containing data on each video currently in the playlist denoted by playlist_url and playlist_title
    '''
    fetch_json_command = f"youtube-dl -j --flat-playlist {playlist_url}"
    fetch_json_process = run(split(fetch_json_command), capture_output=True)

    backed_up_path, _ = build_playlist_path(playlist_title)

    current_playlist_path = path.join(backed_up_path, "current_playlist.txt")

    with open(current_playlist_path, 'w+') as cur:
        for line in fetch_json_process.stdout.decode().encode('utf-16', 'surrogatepass').decode('utf-16'):
            cur.write(line)

    return current_playlist_path


def initial_backup_procedure(playlist_title:str, playlist_url: str) -> None:
    '''
    function used to backup a playlist that has not been backed up before
    - saves all videos of a playlist in the form ./saved-videos/<playlist title>/<video title>
        - each <video title> folder contains 3 items
            1. an info.json file containing all details of the video like channel, description, duration, e.t.c
            2. an image file (generally .jpg or .webp) which is the thumbnail of the video as it appears on YouTube
            3. the video itself (generally a .mp4)
    - saves a <playlist title>_MASTER.txt which contains the json blob for every video that is in the playlist (this is updated when the playlist changes and you run the program)
    :param playlist_title: the title of the playlist we want to backup
    :param playlist_url: the url of the playlist we want to backup
    :return:
    '''
    back_up_command = f'youtube-dl --write-thumbnail --write-info-json -w -o "./saved-playlists/%(playlist_title)s/%(title)s/%(title)s.%(ext)s" {playlist_url}'
    run(split(back_up_command), capture_output=True)  # could possibly be doing something with this output to update user on progress in GUI

    fetch_master_list_command = f'youtube-dl -j --flat-playlist {playlist_url}'
    fetch_master_list_process = run(split(fetch_master_list_command), capture_output=True)

    _, master_playlist_path = build_playlist_path(playlist_title)

    if path.exists(master_playlist_path):
        print(f'{playlist_title} master list already exists')
        return

    with open(master_playlist_path, 'w+') as master:
        for line in fetch_master_list_process.stdout.decode().encode('utf-16', 'surrogatepass').decode('utf-16'):
            master.write(line)


def need_to_update(playlist_title:str, playlist_url:str = None) -> bool:
    '''
    gets a snapshot of the all the videos currently in a playlist and compares it to the videos we have backed up
    :param playlist_title: title of playlist we have backed up
    :param playlist_url: url of playlist we have backed up
    :return: True if the current playlist has more videos than what we have backed up, False otherwise
    '''
    if playlist_url is not None:
        playlist_title = get_playlist_title(playlist_url)
    current_playlist_length = get_length_of_playlist(playlist_url)

    _, master_playlist_path = build_playlist_path(playlist_title)
    master_playlist_length = sum(1 for _ in open(master_playlist_path, 'r'))

    return current_playlist_length > master_playlist_length


def has_playlist_been_backed_up(playlist_title:str, playlist_url:str = None) -> bool:
    '''
    checks for existence of a <playlist_title> folder in ./saved-playlists
    :param playlist_title: title of playlist we want to see is backed up
    :param playlist_url: url of playlist we want to see is backed up
    :return: True if a <playlist_title> folder exists in ./saved-playlists, false otherwise
    '''
    if playlist_url is not None:
        playlist_title = get_playlist_title(playlist_url)

    backed_up_path, _ = build_playlist_path(playlist_title)

    return path.exists(backed_up_path)


def extract_titles_from_txt(path: str) -> Dict[str, Tuple[str, str]]:
    '''
    takes all titles from a txt file full of json blobs that represent videos in a playlist generated
    from the following command:
    youtube-dl -j --flat-playlist <playlist url>  > <playlist name>.txt
    :param path: the path to the given json file you want read
    :return: a dict containing the titles of all videos in a given mapped a tuple, tuple[0] = video url, tuple[1] = raw json blob string
    '''
    title_set = dict()
    with open(path, 'r') as j:
        for line in j:
            line_json = json.loads(line)
            encoded_title = line_json['title'].encode('utf-16', 'surrogatepass').decode('utf-16')
            video_url = f'https://www.youtube.com/watch?v={line_json["id"]}'
            data_tup = (video_url, line)
            title_set[encoded_title] = data_tup

    return title_set


def add_videos_to_master_playlist(playlist_title:str, temp_file:TextIO) -> None:
    '''
    This function reads from a temp file generated by update_master_playlist() to backup newly added videos of a playlist
    :param playlist_title: title of playlist we have backed up
    :param temp_file: the file pointer generated by update_master_playlist()
    :return:
    '''
    back_up_command = f'youtube-dl --write-thumbnail --write-info-json -w -o "./saved-playlists/{playlist_title}/%(title)s/%(title)s.%(ext)s" -a {temp_file.name}'
    run(split(back_up_command), capture_output=True)  # could possibly be doing something with this output to update user on progress in GUI

    remove(temp_file.name)


def update_master_playlist(playlist_title:str, playlist_url:str) -> TextIO:
    '''
    takes the master playlist txt, the new version of the playlist txt and diffs them
    the diff videos are then downloaded and stored in the appropriate saved-playlists folder
    the master playlist txt is updated as well

    :param master_vers_path: the string path to the <playlist name>_MASTER.txt
    :param new_vers_path: the string path to the current state of <playlist name> captured in <playlist name>.txt
    :return: File pointer to file containing YouTube links that need to be downloaded
    '''

    _, master_playlist_path = build_playlist_path(playlist_title)
    current_playlist_path = get_current_playlist(playlist_title, playlist_url)

    current_playlist_dict = extract_titles_from_txt(current_playlist_path)
    master_playlist_dict = extract_titles_from_txt(master_playlist_path)

    remove(current_playlist_path)

    diff_set = current_playlist_dict.keys() - master_playlist_dict.keys()

    temp_file = open(path.join(getcwd(), 'tempLinks.txt'), 'w+')

    # append new json blobs to master list of videos for the given playlist
    with open(master_playlist_path, 'a') as master:
        for title in diff_set:
            master.write(current_playlist_dict[title][1])
            temp_file.write(f'{current_playlist_dict[title][0]}\n')

    temp_file.close()

    add_videos_to_master_playlist(playlist_title, temp_file)


def back_up_playlist(playlist_url:str) -> None:
    '''
    Main flow of program, in charge of backing up a playlist/updating a backed up playlist
    :param playlist_url: the url of the YouTube playlist we want to backup
    :return:
    '''
    # Step 1 get title of playlist
    print("fetching playlist title")
    playlist_title = get_playlist_title(playlist_url)

    print(f"\tplaylist title found: {playlist_title}\n")

    print('checking if playlist has been backed up before....')
    # Step 2 check if playlist name exists in the 'saved-playlists' folder
    if has_playlist_been_backed_up(playlist_title):

        print("\tplaylist has been backed up, checking if we need to update....")
        # yes -> step 3a compare length of new playlist vs what we have stored
        if need_to_update(playlist_title, playlist_url):

            print(f'\t\tdetected new videos in {playlist_title}, updating.....')

            update_master_playlist(playlist_title, playlist_url)

            print('UPDATE COMPLETE')

        else:
            print('\tbacked up playlist is up to date! no need to update\n\n')
    else:

        print('\tplaylist has not been backed up, fetching files for initial backup procedure...')
        # no -> step 3b initial backup procedure
        initial_backup_procedure(playlist_title, playlist_url)

        print('INITIAL BACKUP COMPLETE\n\n')


if __name__=='__main__':
    if len(sys.argv) != 2:
        sys.exit("Please provide a .txt file where each line is a playlist you want to backup")
    else:
        with open(sys.argv[1], 'r') as links:
            for link in links:
                back_up_playlist(link.strip())



