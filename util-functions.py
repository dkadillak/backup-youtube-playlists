import json
from typing import Set, Dict, Tuple

def get_playlist_title(playlist_url:str) -> str:
   '''
   gets the title of the playlist were backing up
   :param playlist_url: the url to the given playlist, of form https://www.youtube.com/playlist?list=<your playlist id>
   :return: the name of the playlist as it appears on YouTube
   '''
   pass

def get_length_of_playlist(playlist_url:str) -> int:
    '''
    returns the number of videos in a given playlist
    :param playlist_url: the url to the given playlist, of form https://www.youtube.com/playlist?list=<your playlist id>
    :return: the number of videos in the given playlist
    '''
    pass

def initial_backup_procedure():
    # youtube-dl --write-thumbnail --write-info-json -w -o "./saved-playlists/%(playlist_title)s/%(playlist_index)s:%(title)s/%(title)s.%(ext)s" <playlist url>

    #youtube-dl -j --flat-playlist <playlist url> > <playlist name>_MASTER.txt

    pass

def need_to_update(playlist_url:str) -> bool:
    pass

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


def update_master_playlist(master_vers_path:str, new_vers_path:str) -> None:
    '''
    takes the master playlist txt, the new version of the playlist txt and diffs them
    the diff videos are then downloaded and stored in the appropriate saved-playlists folder
    the master playlist txt is updated as well

    :param master_vers_path: the string path to the <playlist name>_MASTER.txt
    :param new_vers_path: the string path to the current state of <playlist name> captured in <playlist name>.txt
    :return: None
    '''
    new_vers_dict = extract_titles_from_txt(new_vers_path)
    master_vers_dict = extract_titles_from_txt(master_vers_path)

    diff_set = new_vers_dict.keys() - master_vers_dict.keys()
    new_vid_urls = set()
    # append new json blobs to master list of videos for the given playlist
    with open(master_vers_path, 'a') as master:
        for title in diff_set:
            master.write(new_vers_dict[title][1])
            new_vid_urls.add(new_vers_dict[title][0])

    return new_vid_urls


if __name__=='__main__':
    pass