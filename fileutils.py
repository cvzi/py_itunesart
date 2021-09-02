import string
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TPE2, TPOS, TRCK, APIC, TDRC, TIT2, TCON, TALB, TPUB, TCOP, TPOS, TXXX
from mutagen.mp4 import MP4, MP4Cover

__all__ = [
    "asciiString",
    "getStuff",
    "setStuff",
    "getAlbumInfoString",
    "getSongInfoString",
    "getTrackInfoString",
    "getBasicTrackData",
    "getBasicAlbumData"]

__version__ = "1.8"


def asciiString(s):
    return "".join(filter(lambda x: x in string.printable, s))


def valueOrEmpty(metadata, key, key2=False):
    if key in metadata and metadata[key]:
        return str(metadata[key])
    if key2 and key2 in metadata and metadata[key2]:
        return str(metadata[key2])
    return ""


def getStuff(filename, loud=True):
    if filename.endswith('.mp3'):
        return getStuff_mp3(filename, loud)
    else:
        return getStuff_m4a(filename, loud)


def getStuff_mp3(filename, loud=True):
    audio = MP3(filename)
    d = {'type': 'mp3'}

    for attr in audio:
        d[attr] = str(audio[attr])[:50] + \
            ("... ... ..." if len(str(audio[attr])) > 49 else "")
        if loud:
            try:
                print("$" + attr + "$\t",
                      str(audio[attr])[:50],
                      "... ... ..." if len(str(audio[attr])) > 49 else "")
            except BaseException:
                pass
    return d


def getStuff_m4a(filename, loud=True):
    audio = MP4(filename)
    d = {'type': 'mp4'}
    for attr in audio:
        value = audio[attr]
        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        if isinstance(value, str):
            d[attr] = str(value)[:50] + \
                ("... ... ..." if len(str(value)) > 49 else "")
        else:
            d[attr] = value

        if loud:
            try:
                print("$" + attr + "$\t",
                      str(value)[:50],
                      "... ... ..." if len(str(value)) > 49 else "")
            except BaseException:
                pass
    return d


def setStuff(
        filename,
        title=None,
        artist=None,
        albumArtist=None,
        album=None,
        track=None,
        totalTracks=None,
        date=None,
        genre=None,
        artwork=False,
        publisher=None,
        itunescatalogid=None,
        itunesartistid=None,
        itunesalbumid=None,
        disc=None,
        totalDiscs=None,
        write=False,
        clean=False):
    if filename.endswith('.mp3'):
        return setStuff_mp3(filename, title, artist, albumArtist, album, track,
                            totalTracks, date, genre, artwork, publisher,
                            itunescatalogid, itunesartistid, itunesalbumid,
                            disc, totalDiscs, write, clean)
    else:
        return setStuff_m4a(filename, title, artist, albumArtist, album, track,
                            totalTracks, date, genre, artwork, publisher,
                            itunescatalogid, itunesartistid, itunesalbumid,
                            disc, totalDiscs, write, clean)


def setStuff_mp3(
        filename,
        title=None,
        artist=None,
        albumArtist=None,
        album=None,
        track=None,
        totalTracks=None,
        date=None,
        genre=None,
        artwork=False,
        publisher=None,
        itunescatalogid=None,
        itunesartistid=None,
        itunesalbumid=None,
        disc=None,
        totalDiscs=None,
        write=False,
        clean=False):
    try:
        audio = MP3(filename)
    except BaseException:
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

    if totalTracks is not None:
        audio["TXXX:totaltracks"] = TXXX(encoding=3, desc='totaltracks', text=[str(int(totalTracks))])

    if disc is not None and totalDiscs is not None:
        audio["TPOS"] = TPOS(encoding=3, text="%d/%d" % (int(disc), int(totalDiscs)))
        audio["TXXX:totaldiscs"] = TXXX(encoding=3, desc='totaldiscs', text=[str(int(totalDiscs))])
    elif disc is not None:
        audio["TPOS"] = TPOS(encoding=3, text=str(int(disc)))

    if date is not None:
        audio["TDRC"] = TDRC(encoding=3, text=str(date)[0:4])

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

    if publisher is not None:
        audio["TPUB"] = TPUB(encoding=3, text=publisher)
        audio["TCOP"] = TCOP(encoding=3, text=publisher)

    if itunescatalogid is not None:
        audio["TXXX:itunescatalogid"] = TXXX(encoding=3, desc='itunescatalogid', text=[str(int(itunescatalogid))])

    if itunesartistid is not None:
        audio["TXXX:itunesartistid"] = TXXX(encoding=3, desc='itunesartistid', text=[str(int(itunesartistid))])

    if itunesalbumid is not None:
        audio["TXXX:itunesalbumid"] = TXXX(encoding=3, desc='itunesalbumid', text=[str(int(itunesalbumid))])

    if write:
        audio.save()
        print(" - Done.")
    else:
        print("")
    return audio


def setStuff_m4a(
        filename,
        title=None,
        artist=None,
        albumArtist=None,
        album=None,
        track=None,
        totalTracks=None,
        date=None,
        genre=None,
        artwork=False,
        publisher=None,
        itunescatalogid=None,
        itunesartistid=None,
        itunesalbumid=None,
        disc=None,
        totalDiscs=None,
        write=False,
        clean=False):

    # iTunes tags: https://mutagen.readthedocs.io/en/latest/api/mp4.html#mutagen.mp4.MP4Tags

    try:
        audio = MP4(filename)
    except BaseException:
        print(" - Failed.")
        return False

    if clean:
        # Delete all tags
        audio.clear()
        audio["disk"] = [(1, 1)]

    if title is not None:
        audio["\xa9nam"] = [str(title)]

    if artist is not None:
        audio["\xa9ART"] = [str(artist)]
        if albumArtist is None:
            audio["aART"] = [str(artist)]

    if albumArtist is not None:
        audio["aART"] = [str(albumArtist)]
        if artist is None:
            audio["\xa9ART"] = [str(albumArtist)]

    if album is not None:
        audio["\xa9alb"] = [str(album)]

    if track is not None and totalTracks is not None:
        audio["trkn"] = [(int(track), int(totalTracks))]
    elif totalTracks is not None and len(audio["trkn"]) and len(audio["trkn"][0]):
        audio["trkn"] = [(int(audio["trkn"][0][0]), int(totalTracks))]

    elif track is not None:
        audio["trkn"] = [(int(track),)]

    if disc is not None and totalDiscs is not None:
        audio["disk"] = [(int(disc), int(totalDiscs))]
    elif disc is not None:
        audio["disk"] = [(int(disc),)]

    if date is not None:
        audio["\xa9day"] = [str(date)]

    if genre is not None:
        audio["\xa9gen"] = [str(genre)]

    if artwork:
        # Add artwork
        audio["covr"] = [
            MP4Cover(
                data=artwork,
                imageformat=MP4Cover.FORMAT_JPEG)]

    if publisher is not None:
        audio["cprt"] = [str(publisher)]

    if itunescatalogid is not None:
        audio["cnID"] = [int(itunescatalogid)]

    if itunesartistid is not None:
        audio["atID"] = [int(itunesartistid)]

    if itunesalbumid is not None:
        audio["plID"] = [int(itunesalbumid)]

    if write:
        audio.save()
        print(" - Done.")
    else:
        print("")
    return audio


def getAlbumInfoString(metadata, mp3s):
    if metadata['type'] == 'mp3':
        return getAlbumInfoString_mp3(metadata, mp3s)
    else:
        return getAlbumInfoString_m4a(metadata, mp3s)


def getAlbumInfoString_mp3(metadata, mp3s):
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
        except BaseException:
            albuminfo += " (%d files)" % len(mp3s)
        if trck == len(mp3s):
            albuminfo += " (%d tracks)" % len(mp3s)
        else:
            albuminfo += " (%d tracks, %d files)" % (trck, len(mp3s))
    else:
        albuminfo += " (%d files)" % len(mp3s)
    return albuminfo, guess


def getAlbumInfoString_m4a(metadata, mp3s):
    guess = ""
    albuminfo = ""
    if "aART" in metadata and metadata["aART"]:
        guess = metadata["aART"]
        albuminfo = metadata["aART"]
    elif "\xa9ART" in metadata and metadata["\xa9ART"]:
        guess = metadata["\xa9ART"]
        albuminfo = metadata["\xa9ART"]

    if "\xa9alb" in metadata and metadata["\xa9alb"]:
        guess += " - %s" % metadata["\xa9alb"]
        albuminfo += " - %s" % metadata["\xa9alb"]

    if "trkn" in metadata and isinstance(
            metadata["trkn"], tuple) and len(
            metadata["trkn"]) > 1:
        trck = metadata["trkn"]
        try:
            trck = trck[1]
        except BaseException:
            albuminfo += " (%d files)" % len(mp3s)
        if trck == len(mp3s):
            albuminfo += " (%d tracks)" % len(mp3s)
        else:
            albuminfo += " (%d tracks, %d files)" % (trck, len(mp3s))
    else:
        albuminfo += " (%d files)" % len(mp3s)
    return albuminfo, guess


def getSongInfoString(metadata):
    if metadata['type'] == 'mp3':
        return getSongInfoString_mp3(metadata)
    else:
        return getSongInfoString_m4a(metadata)


def getSongInfoString_mp3(metadata):
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
        albuminfo += " (#%s)" % str(metadata["TRCK"])

    return albuminfo, guess


def getSongInfoString_m4a(metadata):
    guess = ""
    albuminfo = ""
    if "\xa9ART" in metadata and metadata["\xa9ART"]:
        guess = metadata["\xa9ART"]
        albuminfo = metadata["\xa9ART"]
    elif "aART" in metadata and metadata["aART"]:
        guess = metadata["aART"]
        albuminfo = metadata["aART"]

    if "\xa9nam" in metadata and metadata["\xa9nam"]:
        guess += " - %s" % metadata["\xa9nam"]
        albuminfo += " - %s" % metadata["\xa9nam"]
    elif "\xa9alb" in metadata and metadata["\xa9alb"]:
        guess += " - %s" % metadata["\xa9alb"]
        albuminfo += " - %s" % metadata["\xa9alb"]

    if "trkn" in metadata and metadata["trkn"]:
        if isinstance(metadata["trkn"], tuple):
            albuminfo += " (#%s)" % str(metadata["trkn"][0])
        else:
            albuminfo += " (#%s)" % str(metadata["trkn"])

    return albuminfo, guess


def getTrackInfoString(metadata):
    if metadata['type'] == 'mp3':
        return getTrackInfoString_mp3(metadata)
    else:
        return getTrackInfoString_m4a(metadata)


def getTrackInfoString_mp3(metadata):
    trackinfo = ""
    if "TRCK" in metadata and metadata["TRCK"]:
        if "/" in metadata["TRCK"]:
            try:
                trackinfo += "(%02d/%02d) " % tuple(int(x)
                                                    for x in metadata["TRCK"].split("/"))
            except ValueError:
                trackinfo += "(%2s/%2s) " % tuple(metadata["TRCK"].split("/"))
        else:
            try:
                trackinfo += "(%02d/ ?) " % (int(metadata["TRCK"]), )
            except ValueError:
                trackinfo += "(%2s/ ?) " % (metadata["TRCK"], )
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


def getTrackInfoString_m4a(metadata):
    trackinfo = ""
    if "trkn" in metadata and metadata["trkn"]:
        if isinstance(metadata["trkn"], tuple):
            try:
                trackinfo += "(%02d/%02d) " % tuple(int(x)
                                                    for x in metadata["trkn"][0:2])
            except ValueError:
                trackinfo += "(%2s/%2s) " % metadata["trkn"][0:2]
        else:
            try:
                trackinfo += "(%02d/ ?) " % (int(metadata["trkn"]), )
            except ValueError:
                trackinfo += "(%2s/ ?) " % str(metadata["trkn"])
    else:
        trackinfo += "( ?/? ) "

    if "\xa9ART" in metadata and metadata["\xa9ART"]:
        trackinfo += metadata["\xa9ART"]
    elif "aART" in metadata and metadata["aART"]:
        trackinfo += metadata["aART"]
    else:
        trackinfo += "  "

    if "\xa9nam" in metadata and metadata["\xa9nam"]:
        trackinfo += " - %s" % metadata["\xa9nam"]

    if trackinfo.strip() == '( ?/? )':
        # empty data
        trackinfo = ""

    return trackinfo


def getBasicTrackData(metadata):
    if metadata['type'] == 'mp3':
        return getBasicTrackData_mp3(metadata)
    else:
        return getBasicTrackData_m4a(metadata)


def getBasicTrackData_mp3(metadata):
    track = -1
    totalTracks = -1
    if "TRCK" in metadata and metadata["TRCK"]:
        if "/" in metadata["TRCK"]:
            try:
                trackSplit = [int(x) for x in metadata["TRCK"].split("/")]
                track = trackSplit[0]
                totalTracks = trackSplit[1]
            except (ValueError, IndexError) as e:
                pass
        else:
            try:
                track = int(metadata["TRCK"])
            except ValueError:
                pass

    return {
        'album': valueOrEmpty(metadata, 'TALB'),
        'artist': valueOrEmpty(metadata, 'TPE1', 'TPE2'),
        'albumArtist': valueOrEmpty(metadata, 'TPE2', 'TPE1'),
        'title': valueOrEmpty(metadata, 'TIT2'),
        'track': track,
        'totalTracks': totalTracks
    }


def getBasicTrackData_m4a(metadata):
    track = -1
    totalTracks = -1
    if "trkn" in metadata and metadata["trkn"]:
        if isinstance(metadata["trkn"], tuple):
            try:
                track = int(metadata["trkn"][0])
                totalTracks = int(metadata["trkn"][1])
            except (ValueError, IndexError) as e:
                pass
        else:
            try:
                track = int(metadata["trkn"])
            except ValueError:
                pass

    return {
        'album': valueOrEmpty(metadata, '\xa9alb'),
        'artist': valueOrEmpty(metadata, '\xa9ART', 'aART'),
        'albumArtist': valueOrEmpty(metadata, 'aART', '\xa9ART'),
        'title': valueOrEmpty(metadata, '\xa9nam'),
        'track': track,
        'totalTracks': totalTracks
    }


def getBasicAlbumData(metadata):
    if metadata['type'] == 'mp3':
        return getBasicAlbumData_mp3(metadata)
    else:
        return getBasicAlbumData_m4a(metadata)


def getBasicAlbumData_mp3(metadata):
    trck = -1
    if "TRCK" in metadata and metadata["TRCK"] and "/" in metadata["TRCK"]:
        trck = metadata["TRCK"].split("/")[1]
        try:
            trck = int(trck)
        except BaseException:
            trck = len(mp3s)

    return {
        'name': valueOrEmpty(metadata, 'TALB'),
        'artist': valueOrEmpty(metadata, 'TPE2', 'TPE1'),
        'totalTracks': trck,
    }


def getBasicAlbumData_m4a(metadata):
    trck = -1
    if "trkn" in metadata and isinstance(
            metadata["trkn"], tuple) and len(
            metadata["trkn"]) > 1:
        trck = metadata["trkn"]
        try:
            trck = int(trck[1])
        except BaseException:
            trck = len(mp3s)

    return {
        'name': valueOrEmpty(metadata, '\xa9alb'),
        'artist': valueOrEmpty(metadata, 'aART', '\xa9ART'),
        'totalTracks': trck
    }
