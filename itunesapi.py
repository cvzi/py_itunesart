import urllib.request
import urllib.parse
import json

__all__ = [
    "iTunesFindAlbum",
    "iTunesFindSong",
    "iTunesGetTracks",
    "findAlbumArt"]

__version__ = "1.4"


def __getArt(search, entity, country):
    #url = 'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsSearch?term=%s&country=%s&entity=%s' % (urllib.parse.quote(search), urllib.parse.quote(country), urllib.parse.quote(entity))
    url = 'https://itunes.apple.com/search?term=%s&country=%s&entity=%s' % (
        urllib.parse.quote(search), urllib.parse.quote(country), urllib.parse.quote(entity))

    with urllib.request.urlopen(url) as r:
        data = json.loads(
            r.read().decode(
                r.info().get_param('charset') or 'utf-8'))

    return data


def __getTracks(collectionId):
    #url = 'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsLookup?id=%s&entity=song' % (str(collectionId))
    url = 'https://itunes.apple.com/lookup?id=%s&entity=song' % (
        str(collectionId))

    with urllib.request.urlopen(url) as r:
        data = json.loads(
            r.read().decode(
                r.info().get_param('charset') or 'utf-8'))

    return data


def iTunesFindAlbum(search, dimensions=(600, 600, 'bb'), country="us"):
    data = __getArt(search, "album", country)

    results = []

    for item in data['results']:
        result = {
            "collectionId": item['collectionId'],
            "artist": item['artistName'],
            "name": item['collectionName'],
            "genre": item['primaryGenreName'],
            "date": item['releaseDate'],
            "totalTracks": item['trackCount'],
            "image": item['artworkUrl100'].replace(
                "100x100bb.jpg",
                "%dx%d%s.jpg" %
                dimensions)}
        results.append(result)

    return results


def iTunesFindSong(search, dimensions=(600, 600, 'bb'), country="us"):
    data = __getArt(search, "song", country)

    results = []

    for item in data['results']:
        if item['wrapperType'] != 'track':
            continue
        result = {
            "trackId": item['trackId'],
            "collectionId": item['collectionId'],
            "name": item['trackName'],
            "artist": item['artistName'],
            "album": item['collectionName'],
            "albumArtist": item['collectionArtistName'] if 'collectionArtistName' in item else None,
            "genre": item['primaryGenreName'],
            "date": item['releaseDate'],
            "track": item['trackNumber'],
            "totalTracks": item['trackCount'],
            "image": item['artworkUrl100'].replace(
                "100x100bb.jpg",
                "%dx%d%s.jpg" %
                dimensions)}
        results.append(result)

    return results


def iTunesGetTracks(collectionId):
    data = __getTracks(collectionId)

    results = []

    for item in data['results']:
        if item['wrapperType'] == 'track':
            result = {
                "name": item["trackName"],
                "track": item["trackNumber"],
                "artist": item["artistName"]
            }
            results.append(result)

    results.sort(key=lambda v: v["track"])

    return results


def findAlbumArt(search, dimensions=(600, 600, 'bb'), country="us"):
    data = __getArt(search, "album", country)

    results = []

    for item in data['results']:
        result = {}
        result["artist"] = item['artistName']
        result["name"] = item['collectionName']
        result["image"] = item['artworkUrl100'].replace(
            "100x100bb.jpg", "%dx%d%s.jpg" % dimensions)
        results.append(result)

    return results


#
# Below for testing only
#
if __name__ == '__main__':
    from pprint import pprint
    pprint(findAlbumArt("Damian Marley - Stony Hill"))
