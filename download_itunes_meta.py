#! python3
import os
import subprocess
import urllib.request
import urllib.parse
import argparse
import json
import time

from pprint import pprint

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TPE2, TPOS, TRCK, APIC, TDRC, TIT2, TCON, TALB

__version__ = "1.1"


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


def iTunesFindAlbum(search, dimensions=(600, 600, 'bb')):
    data = __getArt(search, "album", "us")

    results = []

    for item in data['results']:
        result = {
            "collectionId": item['collectionId'],
            "artist": item['artistName'],
            "name": item['collectionName'],
            "genre": item['primaryGenreName'],
            "date": item['releaseDate'],
            "totalTracks": item['trackCount'],
            "image": item['artworkUrl100'].replace("100x100bb.jpg", "%dx%d%s.jpg" % dimensions)
        }
        results.append(result)

    return results

def iTunesFindSong(search, dimensions=(600, 600, 'bb')):
    data = __getArt(search, "song", "us")

    results = []

    for item in data['results']:
        result = {
            "trackId" : item['trackId'],
            "collectionId": item['collectionId'],
            "name" : item['trackName'],
            "artist": item['artistName'],
            "album": item['collectionName'],
            "albumArtist": item['collectionArtistName'] if 'collectionArtistName' in item else None,
            "genre": item['primaryGenreName'],
            "date": item['releaseDate'],
            "track" : item['trackNumber'],
            "totalTracks": item['trackCount'],
            "image": item['artworkUrl100'].replace("100x100bb.jpg", "%dx%d%s.jpg" % dimensions)
        }
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


def ascii(s):
    return filter(lambda x: x in string.printable, s)


def getStuff(filename, loud=True):
    audio = MP3(filename)
    d = dict()
    for attr in audio:
        d[attr] = str(audio[attr])[:50] + \
            ("... ... ..." if len(str(audio[attr])) > 49 else "")
        if loud:
            try:
                print("$" + attr + "$\t",
                      str(audio[attr])[:50],
                      "... ... ..." if len(str(audio[attr])) > 49 else "")
            except:
                pass
    return d


def setStuff(filename, title=None, artist=None, albumArtist=None, album=None, track=None,
             totalTracks=None, year=None, genre=None, artwork=False, write=False, clean=False):
    try:
        audio = MP3(filename)
    except:
        print(" - Failed.")
        return False

    if clean:
        # Delete all tags
        audio.clear()
        audio["TPOS"] = TPOS(encoding=3, text=u"1/1")

    if title is not None:
        audio["TIT2"] = TIT2(encoding=3, text=title)

    if artist is not None:
        audio["TPE1"] = TPE1(encoding=3, text=artist)
        if albumArtist is None:
            audio["TPE2"] = TPE2(encoding=3, text=artist)

    if albumArtist is not None:
        audio["TPE2"] = TPE2(encoding=3, text=albumArtist)
        if artist is None:
            audio["TPE1"] = TPE1(encoding=3, text=albumArtist)

    if album is not None:
        audio["TALB"] = TALB(encoding=3, text=album)

    if track is not None and totalTracks is not None:
        if totalTracks > 99:
            audio["TRCK"] = TRCK(
                encoding=3, text="%03d/%03d" %
                (int(track), int(totalTracks)))
        elif totalTracks > 9:
            audio["TRCK"] = TRCK(
                encoding=3, text="%02d/%02d" %
                (int(track), int(totalTracks)))
        else:
            audio["TRCK"] = TRCK(
                encoding=3, text="%d/%d" %
                (int(track), int(totalTracks)))

    elif track is not None:
        audio["TRCK"] = TRCK(encoding=3, text="%02d" % int(track))

    if year is not None:
        audio["TDRC"] = TDRC(encoding=3, text=str(year))

    if genre is not None:
        audio["TCON"] = TCON(encoding=3, text=genre)

    if artwork:
        # Add artwork
        audio.tags.add(
            APIC(
                encoding=3,  # 3 is for utf-8
                mime='image/jpeg',  # image/jpeg or image/png
                type=3,  # 3 is for the cover image
                desc=u'',
                data=artwork
            )
        )

    if write:
        audio.save()
        print(" - Done.")
    else:
        print("")
    return audio


def getAlbumInfoString(metadata, mp3s):
    guess = ""
    albuminfo = ""
    if "TPE2" in metadata and metadata["TPE2"]:
        guess = metadata["TPE2"]
        albuminfo = metadata["TPE2"]
    elif "TPE1" in metadata and metadata["TPE1"]:
        guess = metadata["TPE1"]
        albuminfo = metadata["TPE1"]

    if "TALB" in metadata and metadata["TALB"]:
        guess += " - %s" % metadata["TALB"]
        albuminfo += " - %s" % metadata["TALB"]

    if "TRCK" in metadata and metadata["TRCK"] and "/" in metadata["TRCK"]:
        trck = metadata["TRCK"].split("/")[1]
        try:
            trck = int(trck)
        except:
            albuminfo += " (%d files)" % len(mp3s)
        if trck == len(mp3s):
            albuminfo += " (%d tracks)" % len(mp3s)
        else:
            albuminfo += " (%d tracks, %d files)" % (trck, len(mp3s))
    else:
        albuminfo += " (%d files)" % len(mp3s)
    return albuminfo, guess

def getSongInfoString(metadata):
    guess = ""
    albuminfo = ""
    if "TPE1" in metadata and metadata["TPE1"]:
        guess = metadata["TPE1"]
        albuminfo = metadata["TPE1"]
    elif "TPE2" in metadata and metadata["TPE2"]:
        guess = metadata["TPE2"]
        albuminfo = metadata["TPE2"]

    if "TIT2" in metadata and metadata["TIT2"]:
        guess += " - %s" % metadata["TIT2"]
        albuminfo += " - %s" % metadata["TIT2"]
    elif "TALB" in metadata and metadata["TALB"]:
        guess += " - %s" % metadata["TALB"]
        albuminfo += " - %s" % metadata["TALB"]

    if "TRCK" in metadata and metadata["TRCK"]:
        trck = metadata["TRCK"].split("/")[1]
        albuminfo += " (#%s)" % str(metadata["TRCK"])

    return albuminfo, guess

def getTrackInfoString(metadata):
    trackinfo = ""
    if "TRCK" in metadata and metadata["TRCK"]:
        if "/" in metadata["TRCK"]:
            trackinfo += "(%2s/%2s) " % tuple(metadata["TRCK"].split("/"))
        else:
            trackinfo += "(%2s/ ?) " % metadata["TRCK"]
    else:
        trackinfo += "( ?/? ) "

    if "TPE1" in metadata and metadata["TPE1"]:
        trackinfo += metadata["TPE1"]
    elif "TPE2" in metadata and metadata["TPE2"]:
        trackinfo += metadata["TPE2"]
    else:
        trackinfo += "  "

    if "TIT2" in metadata and metadata["TIT2"]:
        trackinfo += " - %s" % metadata["TIT2"]

    if trackinfo.strip() == '( ?/? )':
        # empty data
        trackinfo = ""

    return trackinfo


def main(args):
    if args.write:
        print("++++Writing Mode++++")
    else:
        print("++++Read-only Mode++++")

    # Walk files
    mp3s = []
    walk = os.walk(os.getcwd())
    for root, dirs, files in walk:
        for name in files:
            if name.lower().endswith('.mp3'):
                mp3s.append(os.path.join(root, name))

    # Walk mp3s
    i = 1
    for name in mp3s:
        if 1 == i:
            oldmetadata = getStuff(mp3s[0])  # output first file for debug
        print(" * ", os.path.basename(name))
        i += 1

    # Search on iTunes
    albuminfo, guess = getAlbumInfoString(oldmetadata, mp3s)

    selectedAlbum = None
    print("")
    print("Search album on iTunes        [q] to exit")
    while selectedAlbum is None:
        guess = guess.strip()
        if not guess:
            guess = os.path.basename(os.path.dirname(mp3s[0]))

        query = input("['%s']=" % guess)
        if not query:
            query = guess
        query = query.replace("-", " ").replace("  ", " ").strip()
        if not query or query == 'q':
            print("No search string provided")
            return

        albums = iTunesFindAlbum(query)
        if len(albums) == 0:
            print("No results, try again or quit with [q]")
            continue

        print('')
        print('[q]/[0] to exit')
        print('')
        print('Current metadata:\t%s' % albuminfo)
        for i, album in enumerate(albums):
            print(
                "\t%d\t\t%s - %s (%d tracks)" %
                (i + 1, album['artist'], album['name'], album['totalTracks']))

        while True:
            val = input('Select your album: ')
            if val == 'q' or val == '0':
                return
            try:
                val = int(val)
                assert val > 0
                assert val <= len(albums)
                break
            except ValueError:
                print("Sorry, wrong Number!")
            except AssertionError:
                print("Wtf?!")

        selectedAlbum = albums[val - 1]

    print("Downloading data...")
    # Download selected album data from itunes
    selectedTracks = iTunesGetTracks(selectedAlbum["collectionId"])
    print("")
    if len(selectedTracks) != len(mp3s):
        print("!!! Found %d files and %d tracks" %
              (len(mp3s), len(selectedTracks)))
    else:
        # Compare tracks with itunes
        for i, name in enumerate(mp3s):
            trackinfo = getTrackInfoString(getStuff(name, loud=False))
            if not trackinfo:
                trackinfo = os.path.basename(name)
            print("File:   %s" % trackinfo)
            print(
                "iTunes: (%02d/%02d) %s - %s" %
                (selectedTracks[i]['track'],
                 selectedAlbum['totalTracks'],
                 selectedTracks[i]['artist'],
                 selectedTracks[i]['name']))
            print("")

    # Try to read folder.jpg
    if args.write:
        val = input('Accept [Enter] or [q] to exit: ')
        if val:
            print("Canceled!")
            return

        print("Downloading folder.jpg")

    artwork = False
    if os.path.exists('folder.jpg'):
        if args.write:
                # Replace folder.jpg
            urllib.request.urlretrieve(
                selectedAlbum['image'], '_newfolder.jpg')
            if os.path.exists('_newfolder.jpg'):
                try:
                    os.remove('folder.jpg')
                except:
                    try:
                        subprocess.check_call(
                            ["attrib", "-H", "-R", 'folder.jpg'])
                        os.remove('folder.jpg')
                    except:
                        os.remove('_newfolder.jpg')
                if not os.path.exists('folder.jpg'):
                    os.rename('_newfolder.jpg', 'folder.jpg')
                    subprocess.check_call(["attrib", "+H", "+R", 'folder.jpg'])

    elif args.write:
        urllib.request.urlretrieve(selectedAlbum['image'], 'folder.jpg')

    if os.path.exists('folder.jpg'):
        artwork = open('folder.jpg', 'rb').read()

    # Walk mp3s and set metadata
    if args.write:
        print("Writing new metadata to files...")

    metadata = {}
    tracks = []  # For batch file
    for i, filename in enumerate(mp3s):
        print(" * ", filename)

        trackdata = {
            "title": selectedTracks[i]['name'],
            "artist": selectedTracks[i]['artist'],
            "albumArtist": selectedAlbum['artist'],
            "album": selectedAlbum['name'],
            "track": selectedTracks[i]['track'],
            "totalTracks": selectedAlbum['totalTracks'],
            "year": selectedAlbum["date"][0:4],
            "genre": selectedAlbum["genre"]
        }
        stuff = setStuff(
            filename=filename,
            artwork=artwork,
            write=args.write,
            clean=args.clean,
            **trackdata)
        metadata.update(stuff)
        tracks.append([name,
                       "%02d - %s - %s" % (int(str(stuff['TRCK']).split("/")[0]) if 'TRCK' in stuff else "",
                                           stuff['TPE1'] if 'TPE1' in stuff else '',
                                           stuff['TIT2'] if 'TIT2' in stuff else '')])

    # Report
    print("")
    print("++++Report++++")
    for attr in metadata:
        try:
            print("$" + attr + "$\t",
                  str(metadata[attr])[:50],
                  "... ... ..." if len(str(metadata[attr])) > 49 else "")
        except:
            print("$" + ascii(attr) + "$\t",
                  ascii(str(metadata[attr])[:50],
                        "... ... ..." if len(str(metadata[attr])) > 49 else ""))

    # Batch file
    if args.batchmove:
        print("++++Batch File++++")
        with open('rename.bat', 'w') as fs:
            for t in tracks:
                s = 'mv "%s" "%s.mp3"\r\n' % (t[0], ascii(t[1][0:120]))
                print(s)
                fs.write(s)

    if not args.write:
        time.sleep(15)
    else:
        time.sleep(5)


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(
        description='Add id3 metadata from iTunes Store to an album')
    parser.add_argument(
        '-w',
        dest='write',
        action='store_const',
        const=True,
        default=False,
        help='Write to files.')
    parser.add_argument(
        '-m',
        dest='batchmove',
        action='store_const',
        const=True,
        default=False,
        help='Create batch file for rename.')
    parser.add_argument(
        '-c',
        dest='clean',
        action='store_const',
        const=True,
        default=False,
        help='Delete all existing metadata before adding new metadata')

    args = parser.parse_args()

    main(args)
