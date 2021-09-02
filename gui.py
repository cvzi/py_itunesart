#! python3
import sys
import argparse
import threading
import subprocess
import urllib.request
import functools
import io
import os
import time
import re
import tkinter as tk
import tkinter.ttk as tkk
import PIL.Image
import PIL.ImageTk
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover, AtomDataType
from mutagen.id3 import APIC

from itunesapi import iTunesFindAlbum, iTunesGetTracks
from fileutils import setStuff

__version__ = "1.7"


class Gui(tk.Tk):
    _imageRefs = {}

    def __init__(self, args, files, current_covers=None, check_remove_all=False):
        super().__init__()

        self.args = args
        self.files = files

        self.bind('<Escape>', self.close)
        self.bind('<Return>', functools.partial(self.search, query=None))

        self.title("iTunes Art Downloader")

        self.imageSize = 250
        self.downloadSize = 800
        self.autocloseinseconds = 3

        self._resultWidgets = []
        self.current_images = []
        self.current_images_widgets = []
        self.current_images_remove = []

        frame = tk.Frame(self)
        tk.Label(frame, text="Set general album information:").pack(
            side=tk.LEFT)

        self.check_set_album_info = tk.BooleanVar()
        self.check_set_album_info.set(True)
        tkk.Checkbutton(frame, text="Year, Genre, Album artist, ...",
                        variable=self.check_set_album_info).pack()

        frame.pack(fill=tk.X)

        frame = tk.Frame(self)
        tk.Label(frame, text="Current covers: (Click to remove)").pack(
            side=tk.LEFT)

        self.check_remove_all = tk.BooleanVar()
        tkk.Checkbutton(frame, text="Remove all", variable=self.check_remove_all,
                        command=functools.partial(self.removeCover, None)).pack()

        frame.pack(fill=tk.X)
        row = tk.Frame(self)
        if current_covers:
            for index, img in enumerate(current_covers):
                desc = "Unknown format"
                typestr = "Could not load image"
                photoimage = None

                if isinstance(img, MP4Cover):
                    im = PIL.Image.open(io.BytesIO(img))
                    size = im.size
                    im.thumbnail(size=(150, 150))
                    photoimage = PIL.ImageTk.PhotoImage(im)
                    self.current_images.append(photoimage)

                    desc = str(AtomDataType(img.imageformat)
                               ).replace('AtomDataType.', '')
                    if len(size) == 2:
                        typestr = "%dx%d" % size
                    else:
                        typestr = str(size)

                elif isinstance(img, APIC):
                    im = PIL.Image.open(io.BytesIO(img.data))
                    size = im.size
                    im.thumbnail(size=(150, 150))
                    photoimage = PIL.ImageTk.PhotoImage(im)
                    self.current_images.append(photoimage)

                    desc = str(img.desc)

                    if len(size) == 2:
                        typestr = "%dx%d" % size
                    else:
                        typestr = str(size)
                    typestr += "\n" + str(img.type).replace('PictureType.', '')

                frame = tk.Frame(row)
                frame.pack(padx=2, pady=2, side=tk.LEFT)
                imgbutton = tk.Button(
                    frame, image=photoimage, command=functools.partial(self.removeCover, index))
                imgbutton.pack(fill=tk.X)
                tk.Label(frame, text="%s\n%s" %
                         (typestr, desc)).pack(fill=tk.X)
                self.current_images_widgets.append(imgbutton)

        else:
            tk.Label(row, text="None").pack()

        row.pack(fill=tk.X)

        frame = tk.Frame(self)
        tk.Label(frame, text='Query:').pack(padx=0, pady=2, side=tk.LEFT)
        self.entry = tkk.Entry(frame, textvariable=tk.StringVar(""), width=40)
        self.entry.pack(padx=2, pady=2, side=tk.LEFT)
        tkk.Button(
            frame,
            text="Go",
            command=self.search).pack(
            padx=2,
            pady=2,
            side=tk.LEFT)

        frame.pack(fill=tk.X)

        if check_remove_all:
            self.check_remove_all.set(True)
            self.removeCover(None)

    def close(self, event=None):
        self.withdraw()
        sys.exit()

    def autoclose(self, event=None):
        time.sleep(self.autocloseinseconds)
        self.close()

    def _loadImage(self, widget, url):
        raw_data = urllib.request.urlopen(url).read()
        im = PIL.Image.open(io.BytesIO(raw_data))
        Gui._imageRefs[url] = PIL.ImageTk.PhotoImage(im)
        widget.configure(image=Gui._imageRefs[url])

    def search(self, event=None, query=None):
        if query is None:
            query = self.entry.get()

        if not query or not query.strip():
            return

        self.entry.delete(0, 'end')
        self.entry.insert(0, query)

        for w in self._resultWidgets:
            w.pack_forget()
        self._resultWidgets = []

        itemsPerRow = int(self.winfo_screenwidth() / (self.imageSize + 10))
        maxRows = int(self.winfo_screenheight() / (self.imageSize + 10))

        searchResults = iTunesFindAlbum(
            query, dimensions=(
                self.imageSize, self.imageSize, 'bb'))

        row = None

        if not searchResults:
            row = tk.Frame(self)
            self._resultWidgets.append(row)
            row.pack(fill=tk.X)
            label = tk.Label(row, text="No results.")
            label.pack(fill=tk.X)

        for i, result in enumerate(searchResults):
            if i % itemsPerRow == 0:
                row = tk.Frame(self)
                self._resultWidgets.append(row)
                row.pack(fill=tk.X)
            if len(self._resultWidgets) > maxRows:
                continue

            frame = tk.Frame(row)
            frame.pack(padx=2, pady=2, side=tk.LEFT)
            url = result['image']

            title = '%s - %s' % (result["artist"], result["name"])
            if len(title) > 55:
                title = result["artist"][0:25]
                title += "-" + result["name"][0:55 - len(title)]
            label = tk.Label(frame, text=title)
            label.pack(fill=tk.X)

            if url not in Gui._imageRefs:
                Gui._imageRefs[url] = None

            button = tk.Button(
                frame,
                image=Gui._imageRefs[url],
                command=functools.partial(
                    self.selectedImage,
                    result))
            button.pack(fill=tk.X)

            if Gui._imageRefs[url] is None:
                t = threading.Thread(
                    target=self._loadImage, args=(
                        button, url))
                t.daemon = True
                t.start()

    def removeCover(self, removeIndex=None):
        if self.check_remove_all.get():
            # Select all
            for i, button in enumerate(self.current_images_widgets):
                if i not in self.current_images_remove:
                    self.current_images_remove.append(i)
                    button.configure(bg='red')
        if removeIndex is not None:
            if self.check_remove_all.get():
                # Uncheck "remove all"
                self.check_remove_all.set(False)
            if removeIndex in self.current_images_remove:
                self.current_images_remove.remove(removeIndex)
                self.current_images_widgets[removeIndex].configure(
                    bg='SystemButtonFace')
            else:
                self.current_images_remove.append(removeIndex)
                self.current_images_widgets[removeIndex].configure(bg='red')
        elif not self.check_remove_all.get() and len(self.current_images_remove) == len(self.current_images_widgets):
            # Unselect all if all were selected
            for i, button in enumerate(self.current_images_widgets):
                if i in self.current_images_remove:
                    self.current_images_remove.remove(i)
                    button.configure(bg='SystemButtonFace')

    def selectedImage(self, result):
        if not self.files:
            print("No files found")
            self.entry.delete(0, 'end')
            self.entry.insert(0, "No files found")
            return

        url = result['image'].replace(
            "%dx%dbb.jpg" %
            (self.imageSize, self.imageSize), "%dx%dbb.jpg" %
            (self.downloadSize, self.downloadSize))
        artwork = False
        if self.args.isAlbum:
            dirname = os.path.dirname(self.files[0])
            folderjpg = os.path.join(dirname, 'folder.jpg')
            newfolderjpg = os.path.join(dirname, '_newfolder.jpg')

            urllib.request.urlretrieve(url, newfolderjpg)
            if os.path.exists(newfolderjpg):
                try:
                    if os.path.exists(folderjpg):
                        os.remove(folderjpg)
                except BaseException:
                    try:
                        subprocess.check_call(
                            ["attrib", "-H", "-R", folderjpg])
                        os.remove(folderjpg)
                    except BaseException:
                        os.remove(newfolderjpg)
                if not os.path.exists(folderjpg):
                    os.rename(newfolderjpg, folderjpg)
                    subprocess.check_call(["attrib", "+H", "+R", folderjpg])
            if os.path.exists(folderjpg):
                artwork = open(folderjpg, 'rb').read()

        if not artwork:
            artwork = urllib.request.urlopen(url).read()

        if not artwork:
            print("Could not download artwork")
            self.entry.delete(0, 'end')
            self.entry.insert(0, "Could not download artwork")
            return

        i = 0
        for filename in self.files:
            trackNumber = None
            if filename.lower().endswith('.mp3'):
                try:
                    audio = MP3(filename)
                except BaseException:
                    print("Could not open file: %s" % str(filename))
                    continue
                apic = APIC(
                    encoding=3,  # 3 is for utf-8
                    mime='image/jpeg',  # image/jpeg or image/png
                    type=3,  # 3 is for the cover image
                    desc=u'',
                    data=artwork
                )

                if self.check_remove_all.get():
                    audio.tags.setall("APIC", [apic])
                elif self.current_images_remove:
                    # remove images at specific indexes
                    allpics = audio.tags.getall("APIC")[:]
                    if len(self.current_images_widgets) != len(allpics):
                        print(
                            "This file has different covers than the first file -> Cannot remove covers")
                        audio.tags.add(apic)
                    else:
                        audio.tags.delall("APIC")
                        audio.tags.setall("APIC", [apic])
                        for picindex, pic in enumerate(allpics):
                            if picindex not in self.current_images_remove:
                                audio.tags.add(pic)

                else:
                    audio.tags.add(apic)

                if "TRCK" in audio and audio["TRCK"]:
                    try:
                        m = re.search("\d+", str(audio["TRCK"]))
                        trackNumber = int(m[0])
                    except:
                        pass

                try:
                    audio.save()
                except BaseException:
                    print("Could not save file: %s" % str(filename))
                    continue
            elif filename.lower().endswith('.m4a'):
                try:
                    audio = MP4(filename)
                except BaseException:
                    print("Could not open file: %s" % str(filename))
                    continue
                mp4cover = MP4Cover(
                    data=artwork,
                    imageformat=MP4Cover.FORMAT_JPEG)

                if self.check_remove_all.get():
                    audio["covr"] = [mp4cover]
                elif self.current_images_remove:
                    # remove images at specific indexes
                    allpics = audio["covr"][:]
                    if len(self.current_images_widgets) != len(allpics):
                        print(
                            "This file has different covers than the first file -> Cannot remove covers")
                        audio.tags.add(apic)
                    else:
                        audio["covr"] = [mp4cover]
                        for picindex, pic in enumerate(allpics):
                            if picindex not in self.current_images_remove:
                                audio["covr"].append(pic)

                else:
                    if "covr" in audio:
                        audio["covr"].append(mp4cover)
                    else:
                        audio["covr"] = [mp4cover]

                if "trkn" in audio and len(audio["trkn"]) and len(audio["trkn"][0]):
                    try:
                        trackNumber = int(audio["trkn"][0][0])
                    except:
                        pass

                try:
                    audio.save()
                except BaseException:
                    print("Could not save file: %s" % str(filename))
                    continue
            else:
                print("Wrong file extension. Expected .mp3 or .m4a")
                continue

            # Set album infos
            if self.check_set_album_info.get():
                # find catalogId in track info
                catalogId = None
                disc = None
                totalDiscs = None
                if trackNumber:
                    trackresults = iTunesGetTracks(
                        collectionId=result['collectionId'])
                    for trackresult in trackresults:
                        if trackresult["track"] == trackNumber:
                            catalogId = trackresult["trackId"]
                            disc = trackresult["disc"]
                            totalDiscs = trackresult["totalDiscs"]
                            break

                    if catalogId is None:
                        print("no matching track found")
                else:
                    print("no track number found")

                trackdata = {
                    "albumArtist": result['artist'],
                    "album":  result['name'],
                    "totalTracks": result['totalTracks'],
                    "date": result["date"],
                    "genre": result["genre"],
                    "publisher": result['publisher'],
                    "itunesartistid": result['artistId'],
                    "itunesalbumid": result['collectionId'],
                    "itunescatalogid": catalogId,
                    "disc": disc,
                    "totalDiscs": totalDiscs
                }
                r = setStuff(
                    filename=filename,
                    write=True,
                    clean=False,
                    **trackdata)
                if not r:
                    print("Failed to set album metadata info")

            i += 1

        status = "Saved %d/%d files!" % (i, len(self.files))
        if i == len(self.files):
            status += ' Closing...'

        self.entry.delete(0, 'end')
        self.entry.insert(0, status)
        print(status)

        if i == len(self.files):
            return self.autoclose()

    def __repr__(self):
        return "GuiObject()"

    def __str__(self):
        return "GuiObject()"


def main(args):
    print(args.isAlbum)
    print(args.query)
    print(args.filename)

    if os.path.exists(args.filename):
        if os.path.isdir(args.filename) and not args.isAlbum:
            print(
                "Filename is a folder but album mode not enabled. Use -a for album mode.")
            return 1

    else:
        print("Filename is not a valid path: %s" % (args.filename,))
        return 2

    if args.isAlbum:
        print("++++Album Mode++++")
        dirname = os.path.dirname(
            os.path.abspath(
                args.filename)) if os.path.isfile(
            args.filename) else os.path.abspath(
                args.filename)
        mp3s = []
        walk = os.walk(dirname)
        for root, dirs, files in walk:
            for name in files:
                if name.lower().endswith(('.mp3', '.m4a')):
                    mp3s.append(os.path.join(root, name))
                    print(" *", name)
    else:
        mp3s = [os.path.abspath(args.filename), ]

    query = ""
    current_covers = []
    if args.query:
        query = args.query
    else:
        # Read id3 data
        if mp3s[0].lower().endswith('.mp3'):
            try:
                audio = MP3(mp3s[0])
                if "TALB" in audio and str(audio["TALB"]):
                    query += " " + str(audio["TALB"])
                elif "TIT2" in audio and str(audio["TIT2"]):
                    query += " " + str(audio["TIT2"])
                if "TPE2" in audio and str(audio["TPE2"]):
                    query += " " + str(audio["TPE2"])
                elif "TPE1" in audio and str(audio["TPE1"]):
                    query += " " + str(audio["TPE1"])
                query = query.strip()

                current_covers = audio.tags.getall("APIC")
            except BaseException as e:
                print("Could not read ID3 data:")
                print(e)
        elif mp3s[0].lower().endswith('.m4a'):
            try:
                audio = MP4(mp3s[0])
                if "\xa9alb" in audio and audio["\xa9alb"] and audio["\xa9alb"][0]:
                    query += " " + str(audio["\xa9alb"][0])
                elif "\xa9nam" in audio and audio["\xa9nam"] and audio["\xa9nam"][0]:
                    query += " " + str(audio["\xa9nam"][0])
                if "aART" in audio and audio["aART"] and audio["aART"][0]:
                    query += " " + str(audio["aART"][0])
                elif "\xa9ART" in audio and audio["\xa9ART"] and audio["\xa9ART"][0]:
                    query += " " + str(audio["\xa9ART"][0])
                query = query.strip()

                if "covr" in audio and audio["covr"]:
                    current_covers = audio["covr"]
            except BaseException as e:
                print("Could not read ID3 data:")
                print(e)
        else:
            print("Wrong file extension. Expected .mp3 or .m4a")

    print("Query=%s" % query)

    gui = Gui(args, files=mp3s, current_covers=current_covers,
              check_remove_all=args.remove)
    gui.search(query=query)
    gui.mainloop()


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser(
        description='Add cover from iTunes Store to an album or single file')
    parser.add_argument(
        '-a',
        dest='isAlbum',
        action='store_const',
        const=True,
        default=False,
        help='Album mode, store cover in all files in this directory')

    parser.add_argument(
        '-r',
        dest='remove',
        action='store_const',
        const=True,
        default=False,
        help='Tick "remove all" covers checkbox')

    parser.add_argument(
        '-q',
        dest='query',
        help='Search with this query instead of artist/tile from id3 metadata from the mp3 file')

    parser.add_argument(
        'filename',
        nargs='?',
        help='A mp3 file or folder with multiple mp3 files')

    args = parser.parse_args()

    main(args)
