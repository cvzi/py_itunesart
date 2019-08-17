#! python3
import os
import argparse
import time
import urllib.request

from pprint import pprint

from download_itunes_meta import getSongInfoString, iTunesFindSong, setStuff, getStuff, ascii



__version__ = "1.0"

def main(args):
  if args.write:
    print ("++++Writing Mode++++")
  else:
    print ("++++Read-only Mode++++")

  # Walk files
  mp3 = os.path.abspath(args.filename)

  # Walk mp3s
  oldmetadata = getStuff(mp3) # output first file for debug
  print (" * ", os.path.basename(mp3))


  # Search on iTunes
  albuminfo, guess = getSongInfoString(oldmetadata)

  selectedSong = None
  print("")
  print("Search song on iTunes        [q] to exit")
  while selectedSong is None:
    guess = guess.strip()
    query = input("['%s']=" % guess)
    if not query:
        query = guess
    query = query.replace("-"," ").replace("  "," ").strip()
    if not query or query == 'q':
      print("No search string provided")
      return

    songs = iTunesFindSong(query)
    if len(songs) == 0:
      print("No results, try again or quit with [q]")
      continue

    print('')
    print('[q]/[0] to exit')
    print('')
    print('Current metadata:\n  \t%s' % albuminfo)
    for i, song in enumerate(songs):
      print("%02d\t%s - %s\n  \t(%s - %s) (%d/%d)\n" % (i + 1, song['artist'], song['name'], song['albumArtist'], song['album'], song['track'], song['totalTracks']))


    while True:
      val = input('Select your song: ')
      if val == 'q' or val == '0':
        return
      try:
        val = int(val)
        assert val > 0
        assert val <= len(songs)
        break
      except ValueError:
        print ("Sorry, wrong Number!")
      except AssertionError:
        print ("Wtf?!")

    selectedSong = songs[val-1]

  artwork = False
  if args.write:
    artwork = urllib.request.urlopen(selectedSong['image']).read()

  # Set metadata
  if args.write:
    print("Writing new metadata to file...")

  trackdata = {
    "title" : selectedSong['name'],
    "artist" : selectedSong['artist'],
    "albumArtist" : selectedSong['albumArtist'],
    "album" : selectedSong['album'],
    "track" : selectedSong['track'],
    "totalTracks" : selectedSong['totalTracks'],
    "year" : selectedSong["date"][0:4],
    "genre" : selectedSong["genre"]
  }
  metadata = setStuff(filename=mp3, artwork=artwork, write=args.write, clean=args.clean, **trackdata)

  # Report
  print ("")
  print ("++++Report++++")
  for attr in metadata:
    try:
      print ("$"+attr+"$\t",str(metadata[attr])[:50],"... ... ..." if len(str(metadata[attr]))>49 else "")
    except:
      print ("$"+ascii(attr)+"$\t",ascii(str(metadata[attr])[:50],"... ... ..." if len(str(metadata[attr]))>49 else ""))


  if not args.write:
    time.sleep(15)
  else:
    time.sleep(5)

if __name__ == "__main__":
  # Arguments
  parser = argparse.ArgumentParser(description='Add id3 metadata from iTunes Store to a single file')
  parser.add_argument('-w', dest='write', action='store_const', const=True, default=False, help='Write to file.')
  parser.add_argument('-c', dest='clean', action='store_const', const=True, default=False, help='Delete all existing metadata before adding new metadata')
  parser.add_argument('filename', help='A mp3 file')
  args = parser.parse_args()

  main(args)

