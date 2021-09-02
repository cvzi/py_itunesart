#! python3
import os
import argparse
import time
import urllib.request

from fileutils import asciiString, getStuff, setStuff, getSongInfoString, getBasicTrackData
from itunesapi import iTunesFindSong
from download_itunes_meta import initColor, colorize, cprint, Color, highlightMatch, try_countries, country_default

__version__ = "1.8"


def main(args):
    initColor(args.color)

    if args.write:
        cprint("++++Writing Mode++++", Color.red, args.color)
    else:
        print("++++Read-only Mode++++")

    country = country_default

    # Walk files
    mp3 = os.path.abspath(args.filename)

    # Walk mp3s
    oldmetadata = getStuff(mp3)  # output first file for debug
    print(" * ", os.path.basename(mp3))

    # Search on iTunes
    songinfo, guess = getSongInfoString(oldmetadata)
    if not songinfo.strip():
        songinfo = os.path.basename(mp3)
    trackdata = getBasicTrackData(oldmetadata)

    selectedSong = None
    print("")
    print(
        'Search song on iTunes        [q] to exit, [L] to change country (%s)' % country)
    while selectedSong is None:
        guess = guess.strip()
        if not guess:
            guess = os.path.splitext(os.path.basename(mp3))[0]

        query = input("['%s']=" % guess)
        if not query:
            query = guess
        query = query.replace("-", " ").replace("  ", " ").strip()
        if not query or query == 'q':
            print("No search string provided")
            return
        if query == 'L' or query == 'l':
            val = input('Type two-letter code: (e.g. US) ')
            if len(val) != 2:
                print("Invalid code, using default: US")
                country = 'us'
            else:
                print("Country changed. Search again:")
                country = val
            continue

        songs = iTunesFindSong(query, country=country)
        if len(songs) == 0:
            countries = try_countries[:]
            print("Trying stores in other countries...", end=" ")
            while len(songs) == 0 and len(countries):
                cc = countries.pop()
                print("[%s]" % cc, end=" ")
                songs = iTunesFindSong(query, country=country)
            print("")
            if len(songs) > 0:
                print(colorize("Found %d results in [%s] store" % (
                    len(songs), cc), color=Color.yellowBG, enabled=args.color))
                country = cc
            else:
                print("No results, try again or quit with [q]")
                continue

        print('')
        print('[q]/[0] to exit [L] to change country (%s)' % country)
        print('')

        print('Current metadata:\n  \t%s' % colorize(
            songinfo, color=Color.green, enabled=args.color))
        print('Search results (%d results):\n' % len(songs))
        for i, song in enumerate(songs):
            trackColored = colorize("%d" % song['track'], color=Color.greenBG,
                                    enabled=args.color) if song['track'] == trackdata['track'] else "%d" % song['track']
            totalTracksColored = colorize("%d" % song['totalTracks'], color=Color.greenBG,
                                          enabled=args.color) if song['totalTracks'] == trackdata['totalTracks'] else "%d" % song['totalTracks']
            print(
                "%02d\t%s - %s\n  \t(%s%s) (%s/%s)\n" %
                (i + 1,
                 highlightMatch(trackdata['artist'],
                                song['artist'], enabled=args.color),
                 highlightMatch(trackdata['title'],
                                song['name'], enabled=args.color),
                 (highlightMatch(trackdata['albumArtist'], song['albumArtist'],
                                 enabled=args.color) + ' - ') if song['albumArtist'] else '',
                 highlightMatch(trackdata['album'],
                                song['album'], enabled=args.color),
                 trackColored,
                 totalTracksColored))

        while True:
            val = input('Select your song: ')
            if val == 'q' or val == '0':
                return

            elif val == 'L' or val == 'l':
                val = input('Type two-letter code: (e.g. US) ')
                if len(val) != 2:
                    print("Invalid code, using default: US")
                    country = 'us'
                else:
                    print("Country changed. Search again:")
                    country = val
                break
            else:
                try:
                    val = int(val)
                    assert val > 0
                    assert val <= len(songs)
                    selectedSong = songs[val - 1]
                    break
                except ValueError:
                    print("Sorry, wrong Number!")
                except AssertionError:
                    print("Wtf?!")

    artwork = False
    if args.write:
        artwork = urllib.request.urlopen(selectedSong['image']).read()

    # Set metadata
    if args.write:
        print("Writing new metadata to file...")

    trackdata = {
        "title": selectedSong['name'],
        "artist": selectedSong['artist'],
        "albumArtist": selectedSong['albumArtist'],
        "album": selectedSong['album'],
        "track": selectedSong['track'],
        "totalTracks": selectedSong['totalTracks'],
        "date": selectedSong["date"],
        "genre": selectedSong["genre"]
    }
    metadata = setStuff(
        filename=mp3,
        artwork=artwork,
        write=args.write,
        clean=args.clean,
        **trackdata)

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

    if args.sleep:
        if not args.write:
            time.sleep(15)
        else:
            time.sleep(5)


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(
        description='Add id3 metadata from iTunes Store to a single file')
    parser.add_argument(
        '-w',
        dest='write',
        action='store_const',
        const=True,
        default=False,
        help='Write to file.')
    parser.add_argument(
        '-c',
        dest='clean',
        action='store_const',
        const=True,
        default=False,
        help='Delete all existing metadata before adding new metadata')
    parser.add_argument(
        '-s',
        dest='sleep',
        action='store_const',
        const=True,
        default=False,
        help='Sleep 5 seconds at the end of the script to keep the console window open on Windows')
    parser.add_argument(
        '--no-color',
        dest='color',
        action='store_const',
        const=False,
        default=True,
        help='Do not use colored text in output')
    parser.add_argument('filename', help='A mp3 file')
    args = parser.parse_args()

    main(args)
