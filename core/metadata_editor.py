import mutagen
import os
import re

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TCON, TPOS, TIT3

def get_folders(base_path):
    """
    Recursively find all folders in the base path and its subfolders.

    Args:
        base_path (str): The base path to search for folders.

    Returns:
        list: A list of folder paths.
    """
    folders = []

    for entry in os.listdir(base_path):
        entry_path = os.path.join(base_path, entry)
        if os.path.isdir(entry_path):
            folders.append(entry_path)
            folders.extend(get_folders(entry_path))
    return folders


def edit_mp3_metadata(folder_path: str, audiobook_data: list, db) -> None:
    """
    Edit the metadata of MP3 files in a folder.

    Args:
        folder_path (str): The path to the folder containing the MP3 files.
        artist (str): The new contributing artist(s) to set.
        album (str): The new album to set.
        genre (str): 
    """

    for filename in os.listdir(folder_path):
        if filename.endswith(".mp3"):
            file_path = os.path.join(folder_path, filename)
            audio = MP3(file_path)

            # If the file doesn't have any existing ID3 tags, create a new ID3 object
            if audio.tags is None:
                audio.tags = ID3()

            # Get the track number from the file name
            name = os.path.splitext(filename)[0]
            match = re.search(r'\d+', name)
            if match:
                track_number = int(match.group())
                title = f"Chapter {track_number}"
            else:
                title = name
            print(f"title is: {title}")

            album = audiobook_data[1] 
            artist = audiobook_data[2]
            series_name = audiobook_data[3]
            book_number = audiobook_data[4]
            last_book_number = None

            # Edit the "Description" section
            audio["title"] = TIT2(encoding=3, text=title)
            print(f"series name is: {series_name}")
            if series_name:
                last_book_number = db.get_last_book_number_in_series(series_name)
                audio["subtitle"] = TIT3(encoding=3, text=series_name)
            print(f"book number: {book_number}")
            if book_number:
                audio["part_of_a_set"] = TPOS(encoding=3, text=f"{book_number}/{last_book_number}")

            # Edit the "Media" section
            audio["artist"] = TPE1(encoding=3, text=artist)
            audio["album"] = TALB(encoding=3, text=album)
            audio["tracknumber"] = TRCK(encoding=3, text=str(track_number))
            audio["genre"] = TCON(encoding=3, text="Audiobook")

            audio.save()
            print(f"Metadata edited for {filename}")

if __name__ == "__main__":
    base_path = "C:\\Users\\Ghost\\Documents\\Personal\\Alicia\\Audiobooks"
    folders = get_folders(base_path)
    genre = "Audiobook"
    for folder in folders:
        album = os.path.basename(folder)
        edit_mp3_metadata(folder, album, genre)