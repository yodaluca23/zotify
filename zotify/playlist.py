from zotify.const import ITEMS, ID, TRACK, NAME, TYPE
from zotify.podcast import download_episode
from zotify.termoutput import Printer, PrintChannel
from zotify.track import download_track
from zotify.utils import split_input
from zotify.zotify import Zotify

MY_PLAYLISTS_URL = 'https://api.spotify.com/v1/me/playlists'
PLAYLISTS_URL = 'https://api.spotify.com/v1/playlists'


def get_all_playlists():
    """ Returns list of users playlists """
    playlists = []
    limit = 50
    offset = 0

    while True:
        resp = Zotify.invoke_url_with_params(MY_PLAYLISTS_URL, limit=limit, offset=offset)
        offset += limit
        playlists.extend(resp[ITEMS])
        if len(resp[ITEMS]) < limit:
            break

    return playlists


def get_playlist_songs(playlist_id):
    """ returns list of songs in a playlist """
    songs = []
    offset = 0
    limit = 100

    while True:
        resp = Zotify.invoke_url_with_params(f'{PLAYLISTS_URL}/{playlist_id}/tracks', limit=limit, offset=offset)
        offset += limit
        songs.extend(resp[ITEMS])
        if len(resp[ITEMS]) < limit:
            break

    return songs


def get_playlist_info(playlist_id) -> tuple[str, str]:
    """ Returns information scraped from playlist """
    (raw, resp) = Zotify.invoke_url(f'{PLAYLISTS_URL}/{playlist_id}?fields=name,owner(display_name)&market=from_token')
    return resp['name'].strip(), resp['owner']['display_name'].strip()


def download_playlist(playlist, wrapper_p_bars: list | None = None):
    """Downloads all the songs from a playlist"""
    playlist_songs = [song for song in get_playlist_songs(playlist[ID]) if song[TRACK][ID]]
    char_num = max({len(str(len(playlist_songs))), 2})
    
    pos = 3
    if wrapper_p_bars is not None:
        pos = wrapper_p_bars[-1] if type(wrapper_p_bars[-1]) is int else -(wrapper_p_bars[-1].pos + 2)
    else:
        wrapper_p_bars = []
    p_bar = Printer.progress(enumerate(playlist_songs, start=1), unit='songs', total=len(playlist_songs), unit_scale=True,
                             disable=not Zotify.CONFIG.get_show_playlist_pbar(), pos=pos)
    wrapper_p_bars.append(p_bar if Zotify.CONFIG.get_show_playlist_pbar() else pos)
    
    for n, song in p_bar:
        if song[TRACK][TYPE] == "episode": # Playlist item is a podcast episode
            download_episode(song[TRACK][ID])
        else:
            download_track('extplaylist', song[TRACK][ID], extra_keys=
                           {'playlist_song_name': song[TRACK][NAME],
                            'playlist': playlist[NAME],
                            'playlist_num': str(n).zfill(char_num),
                            'playlist_id': playlist[ID],
                            'playlist_track_id': song[TRACK][ID]},
                           wrapper_p_bars=wrapper_p_bars)
        p_bar.set_description(song[TRACK][NAME])
        for bar in wrapper_p_bars:
            if type(bar) != int: bar.refresh()


def download_from_user_playlist():
    """ Select which playlist(s) to download """
    playlists = get_all_playlists()
    
    count = 1
    for playlist in playlists:
        print(str(count) + ': ' + playlist[NAME].strip())
        count += 1
    
    selection = ''
    print('\n> SELECT A PLAYLIST BY ID')
    print('> SELECT A RANGE BY ADDING A DASH BETWEEN BOTH ID\'s')
    print('> OR PARTICULAR OPTIONS BY ADDING A COMMA BETWEEN ID\'s\n')
    while len(selection) == 0:
        selection = str(input('ID(s): '))
    playlist_choices = split_input(selection)
    
    pos = 5
    p_bar = Printer.progress(playlist_choices, unit='playlists', total=len(playlist_choices), unit_scale=True, 
                             disable=not Zotify.CONFIG.get_show_url_pbar(), pos=pos)
    wrapper_p_bars = [p_bar if Zotify.CONFIG.get_show_url_pbar() else pos]
    
    for playlist_number in p_bar:
        playlist = playlists[int(playlist_number) - 1]
        download_playlist(playlist, wrapper_p_bars)
        p_bar.set_description(playlist[NAME].strip())
        for bar in wrapper_p_bars:
            if type(bar) != int: bar.refresh()
