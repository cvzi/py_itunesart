#! python3
import os
import subprocess
import urllib.request
import argparse
import time

from pprint import pprint

from fileutils import asciiString, getStuff, setStuff, getAlbumInfoString, getSongInfoString, getTrackInfoString
from itunesapi import iTunesGetTracks, iTunesFindSong, iTunesFindAlbum

__version__ = "1.2"


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
            if name.lower().endswith(('.mp3', '.m4a')):
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

    # Compare tracks with itunes
    for i, name in enumerate(mp3s[0:min(len(mp3s), len(selectedTracks))]):
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
                except BaseException:
                    try:
                        subprocess.check_call(
                            ["attrib", "-H", "-R", 'folder.jpg'])
                        os.remove('folder.jpg')
                    except BaseException:
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
            "date": selectedAlbum["date"],
            "genre": selectedAlbum["genre"]
        }
        stuff = setStuff(
            filename=filename,
            artwork=artwork,
            write=args.write,
            clean=args.clean,
            **trackdata)
        metadata.update(stuff)

        if 'TIT2' in stuff:
            tracks.append([filename,
                           "%02d - %s - %s" % (int(str(stuff['TRCK']).split("/")[0]) if 'TRCK' in stuff else "",
                                               stuff['TPE1'] if 'TPE1' in stuff else '',
                                               stuff['TIT2'] if 'TIT2' in stuff else '')])
        else:
            tracks.append(
                [
                    filename,
                    "%02d - %s - %s" %
                    (int(
                        stuff['trkn'][0][0]) if 'trkn' in stuff and stuff['trkn'] else "",
                        stuff['\xa9ART'][0] if '\xa9ART' in stuff else '',
                        stuff['\xa9nam'][0] if '\xa9nam' in stuff else '')])

    # Report
    print("")
    print("++++Report++++")
    for attr in metadata:
        try:
            print("$" + attr + "$\t",
                  str(metadata[attr])[:50],
                  "... ... ..." if len(str(metadata[attr])) > 49 else "")
        except BaseException:
            print("$" + asciiString(attr) + "$\t",
                  asciiString(str(metadata[attr])[:50],
                              "... ... ..." if len(str(metadata[attr])) > 49 else ""))

    # Batch file
    if args.batchmove:
        print("++++Batch File++++")
        with open('rename.bat', 'w') as fs:
            for t in tracks:
                _, ext = os.path.splitext(t[0])
                s = 'mv "%s" "%s%s"\r\n' % (
                    t[0], asciiString(t[1][0:120]), ext.lower())
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
