from zotify.const import ITEMS, ARTISTS, NAME, ID
from zotify.termoutput import Printer
from zotify.track import download_track
from zotify.utils import fix_filename
from zotify.zotify import Zotify

ALBUM_URL = 'https://api.spotify.com/v1/albums'
ARTIST_URL = 'https://api.spotify.com/v1/artists'


def get_album_tracks(album_id):
    """ Returns album tracklist """
    songs = []
    offset = 0
    limit = 50

    while True:
        resp = Zotify.invoke_url_with_params(f'{ALBUM_URL}/{album_id}/tracks', limit=limit, offset=offset)
        offset += limit
        songs.extend(resp[ITEMS])
        if len(resp[ITEMS]) < limit:
            break

    return songs


def get_album_name(album_id):
    """ Returns album name """
    (raw, resp) = Zotify.invoke_url(f'{ALBUM_URL}/{album_id}')
    return resp[ARTISTS][0][NAME], fix_filename(resp[NAME])


def get_artist_albums(artist_id):
    """ Returns artist's albums """
    (raw, resp) = Zotify.invoke_url(f'{ARTIST_URL}/{artist_id}/albums?include_groups=album%2Csingle')
    # Return a list each album's id
    album_ids = [resp[ITEMS][i][ID] for i in range(len(resp[ITEMS]))]
    # Recursive requests to get all albums including singles an EPs
    while resp['next'] is not None:
        (raw, resp) = Zotify.invoke_url(resp['next'])
        album_ids.extend([resp[ITEMS][i][ID] for i in range(len(resp[ITEMS]))])

    return album_ids


def download_album(album, wrapper_p_bars: list | None = None):
    """ Downloads songs from an album """
    artist, album_name = get_album_name(album)
    tracks = get_album_tracks(album)
    char_num = max({len(str(len(tracks))), 2})
    
    pos = 3
    if wrapper_p_bars is not None:
        pos = wrapper_p_bars[-1] if type(wrapper_p_bars[-1]) is int else -(wrapper_p_bars[-1].pos + 2)
        for bar in wrapper_p_bars:
            if type(bar) != int: bar.refresh()
    else:
        wrapper_p_bars = []
    p_bar = Printer.progress(enumerate(tracks, start=1), unit_scale=True, unit='songs', total=len(tracks), 
                             disable=not Zotify.CONFIG.get_show_album_pbar(), pos=pos)        
    wrapper_p_bars.append(p_bar if Zotify.CONFIG.get_show_album_pbar() else pos)
    
    for n, track in p_bar:
        download_track('album', track[ID], extra_keys={'album_num': str(n).zfill(char_num), 'artist': artist, 'album': album_name, 'album_id': album},
                       wrapper_p_bars=wrapper_p_bars)
        p_bar.set_description(track[NAME])
        for bar in wrapper_p_bars:
            if type(bar) != int: bar.refresh()


def download_artist_albums(artist, wrapper_p_bars: list | None = None):
    """ Downloads albums of an artist """
    albums = get_artist_albums(artist)
    
    pos = 5
    if wrapper_p_bars is not None:
        pos = wrapper_p_bars[-1] if type(wrapper_p_bars[-1]) is int else -(wrapper_p_bars[-1].pos + 2)
        for bar in wrapper_p_bars:
            if type(bar) != int: bar.refresh()
    else:
        wrapper_p_bars = []
    p_bar = Printer.progress(albums, unit_scale=True, unit='albums', total=len(albums), 
                             disable=not Zotify.CONFIG.get_show_artist_pbar(), pos=pos)        
    wrapper_p_bars.append(p_bar if Zotify.CONFIG.get_show_artist_pbar() else pos)
    
    for album_id in p_bar:
        download_album(album_id, wrapper_p_bars)
        p_bar.set_description(get_album_name(album_id))
        for bar in wrapper_p_bars:
            if type(bar) != int: bar.refresh()
