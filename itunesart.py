import urllib.request
import urllib.parse
import json

__all__ = ["findAlbumArt"]

__version__ = "1.0"

def __getArt(search, dimensions, entity, country):
    url = 'http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsSearch?term=%s&country=%s&entity=%s' % (urllib.parse.quote(search), urllib.parse.quote(country), urllib.parse.quote(entity))
    
    with urllib.request.urlopen(url) as r:
        data = json.loads(r.read().decode(r.info().get_param('charset') or 'utf-8'))
    
    return data

def findAlbumArt(search, dimensions=(600,600,'bb')):
    data = __getArt(search, dimensions, "album", "us")
    
    results = []

    for item in data['results']:
        result = {}
        result["artist"] = item['artistName']
        result["name"] = item['collectionName']
        result["image"] = item['artworkUrl100'].replace("100x100bb.jpg", "%dx%d%s.jpg" % dimensions)
        results.append(result)
            
    return results

#
# Below for testing only
#
if __name__ == '__main__':
    findAlbumArt("Damian Marley - Stony Hill")
