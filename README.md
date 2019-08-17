# py_itunesart
Download album cover and meta data information from [Apple iTunes API](https://affiliate.itunes.apple.com/resources/documentation/itunes-store-web-service-search-api/).

Metadata and album cover can be stored in mp3 metadata/id3

Can be used from the command line or from [Mp3Tag](http://www.mp3tag.de)

Requirements:
 * Python 3
 * [Mutagen](https://bitbucket.org/lazka/mutagen) python module `pip install mutagen`

# Mp3Tag

To add it to the Mp3Tag context menu, do the following steps in Mp3Tag:

![Mp3Tag instructions](https://raw.githubusercontent.com/cvzi/py_itunesart/master/mp3tag.jpg)

## Metadata from iTunes (Single song)
 * Open Tools -> Options -> Tools
 * Click on the "New" icon
 * Enter the name that shall appear in the context menu
 * For path choose your python.exe
 * For parameter use: `C:\pathtofile\download_itunes_meta_single.py -c -w "%_path%"`
 * Accept the "for all selected files" option

## Metadata from iTunes (Album/Folder)
 * Open Tools -> Options -> Tools
 * Click on the "New" icon
 * Enter the name that shall appear in the context menu
 * For path choose your python.exe
 * For parameter use: `C:\pathtofile\download_itunes_meta.py -c -w`
 * Uncheck the "for all selected files" option

## Only cover from iTunes (Single song)
 * Open Tools -> Options -> Tools
 * Click on the "New" icon
 * Enter the name that shall appear in the context menu
 * For path choose your python.exe
 * For parameter use: `C:\pathtofile\gui.py "%_path%"`
 * Uncheck the "for all selected files" option

## Only cover from iTunes (Album/Folder)
 * Open Tools -> Options -> Tools
 * Click on the "New" icon
 * Enter the name that shall appear in the context menu
 * For path choose your python.exe
 * For parameter use: `C:\pathtofile\gui.py -a "%_path%"`
 * Uncheck the "for all selected files" option


# GUI
tkinter GUI screenshot:

![Artwork GUI](https://raw.githubusercontent.com/cvzi/py_itunesart/master/gui.jpg)
