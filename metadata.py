import os
import sys
import shutil
import argparse
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TCON, TYER, TPE2, TPOS
from enum import Enum

import common as cm
import terminal as tm
import cover
import bpm

class MetadataFlags(Enum):
    NONE = 0x0000
    HAS_ARTIST = 0x0001
    HAS_TITLE = 0x0002
    HAS_ALBUM = 0x0004
    HAS_ALBUM_ARTIST = 0x0008
    HAS_TRACK_NUMBER = 0x0010
    HAS_DISC_NUMBER = 0x0020
    HAS_GENRE = 0x0040
    HAS_YEAR = 0x0080
    HAS_COVER = 0x0100
    HAS_BPM = 0x0200

def parse_filename(filename: str) -> tuple[str, str] | None:
    """
    Extract artist and title from filename like 'Avicii - Levels.m4a'.

    Args:
        filename (str): The filename.
    Returns:
        tuple[str, str]: Artist and title based on filename.
    """
    base = os.path.splitext(filename)[0]
    parts = base.split(" - ", 1)
    if len(parts) < 2:
        cm.log(cm.LogLevel.WARN, f"Invalid filename: {filename}")
        return None
    artist, title = parts
    return artist.strip(), title.strip()

def is_missing(metadata_flags: int, flag_to_check: MetadataFlags) -> bool:
    return (metadata_flags & flag_to_check.value) == MetadataFlags.NONE.value
    
def get_track_nr(audio_path: str) -> int | None:
    ext = cm.get_audio_file_extension(audio_path)
    
    match ext:
        case cm.AudioFileExtension.NOT_SUPPORTED:
            return None
        case cm.AudioFileExtension.MP3:
            try:
            
                audio = MP3(audio_path, ID3=ID3)
                if audio.tags and "TRCK" in audio.tags:
                    return int(audio.tags["TRCK"].text[0].split("/")[0])
                else:
                    # No track tags currently exist
                    return 1
            except (TypeError, ValueError):
                cm.log(cm.LogLevel.ERROR, f"Failed to read track number of {audio_path}")
                return None
                
        case cm.AudioFileExtension.M4A:
            audio = MP4(audio_path)
            return audio.tags["trkn"][0][0]

def check_metadata(audio_path: str) -> int:
    """
    Checks which metadata is set of an audio file.

    Args:
        audio_path (str): The path to the audio file.
    Returns:
        int: The numerical value constructed out of the MetadataFlags enum.
        Each bit set stands for an already existing metadata.
        If something went wrong returns -1.
    """
    ext = cm.get_audio_file_extension(audio_path)

    res = MetadataFlags.NONE.value
    match ext:
        case cm.AudioFileExtension.NOT_SUPPORTED:
            return -1
        case cm.AudioFileExtension.MP3:
            audio = MP3(audio_path, ID3=ID3)
            if audio.tags is None:
                return res
            if "TIT2" in audio.tags:
                res |= MetadataFlags.HAS_TITLE.value
            if "TPE1" in audio.tags:
                res |= MetadataFlags.HAS_ARTIST.value
            if "TALB" in audio.tags:
                res |= MetadataFlags.HAS_ALBUM.value
            if "TPE2" in audio.tags:
                res |= MetadataFlags.HAS_ALBUM_ARTIST.value
            if "TRCK" in audio.tags:
                res |= MetadataFlags.HAS_TRACK_NUMBER.value
            if "TPOS" in audio.tags:
                res |= MetadataFlags.HAS_DISC_NUMBER.value
            if "TCON" in audio.tags:
                res |= MetadataFlags.HAS_GENRE.value
            if "TYER" in audio.tags:
                res |= MetadataFlags.HAS_YEAR.value

        case cm.AudioFileExtension.M4A:
            audio = MP4(audio_path)
            if audio.tags is None:
                return res
            if "\xa9nam" in audio.tags:
                res |= MetadataFlags.HAS_TITLE.value
            if "\xa9ART" in audio.tags:
                res |= MetadataFlags.HAS_ARTIST.value
            if "\xa9alb" in audio.tags:
                res |= MetadataFlags.HAS_ALBUM.value
            if "aART" in audio.tags:
                res |= MetadataFlags.HAS_ALBUM_ARTIST.value
            if "trkn" in audio.tags:
                res |= MetadataFlags.HAS_TRACK_NUMBER.value
            if "disk" in audio.tags:
                res |= MetadataFlags.HAS_DISC_NUMBER.value
            if "\xa9gen" in audio.tags:
                res |= MetadataFlags.HAS_GENRE.value
            if "\xa9day" in audio.tags:
                res |= MetadataFlags.HAS_YEAR.value

    if cover.has_cover(audio_path):
        res |= MetadataFlags.HAS_COVER.value
    if bpm.has_bpm(audio_path):
        res |= MetadataFlags.HAS_BPM.value
    return res

def set_basic_metadata(audio_path: str,
                       title: str=None,
                       artist: str=None,
                       album: str=None,
                       album_artist: str=None,
                       track_nr: int=None,
                       disc_nr: int=None,
                       genre: str=None,
                       year: int=None):
    """
    Sets the basic metadata to the audio file.

    Args:
        audio_path (str): Path to the audio file.
        title (str, optional): The title of the audio.
        artist (str, optional): The artist of the audio.
        album (str, optional): The album name of the audio.
        album_artist (str, optional): The album artist of the audio.
        track_nr (str, optional): The track number of the audio.
        disc_nr (str, optional): The disc number of the audio.
        genre (str, optional): The genre of the audio.
        year (str, optional): The release year of the audio.
    """
    ext = cm.get_audio_file_extension(audio_path)

    match ext:
        case cm.AudioFileExtension.NOT_SUPPORTED:
            return
        case cm.AudioFileExtension.MP3:
            audio = MP3(audio_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            if title:
                audio.tags.delall("TIT2")
                audio.tags.add(TIT2(encoding=3, text=title))
            if artist:
                audio.tags.delall("TPE1")
                audio.tags.add(TPE1(encoding=3, text=artist))
            if album:
                audio.tags.delall("TALB")
                audio.tags.add(TALB(encoding=3, text=album))
            if album_artist:
                audio.tags.delall("TPE2")
                audio.tags.add(TPE2(encoding=3, text=album_artist))
            if track_nr:
                audio.tags.delall("TRCK")
                audio.tags.add(TRCK(encoding=3, text=track_nr))
            if disc_nr:
                audio.tags.delall("TPOS")
                audio.tags.add(TPOS(encoding=3, text=disc_nr))
            if genre:
                audio.tags.delall("TCON")
                audio.tags.add(TCON(encoding=3, text=genre))
            if year:
                audio.tags.delall("TYER")
                audio.tags.add(TYER(encoding=3, text=year))
            audio.save()

        case cm.AudioFileExtension.M4A:
            audio = MP4(audio_path)
            if audio.tags is None:
                audio.add_tags()
            if title: audio["\xa9nam"] = title
            if artist: audio["\xa9ART"] = artist
            if album: audio["\xa9alb"] = album
            if album_artist: audio["aART"] = album_artist
            if track_nr: audio["trkn"] = [(track_nr, 0)]
            if disc_nr: audio["disk"] = [(disc_nr, 0)]
            if genre: audio["\xa9gen"] = genre
            if year: audio["\xa9day"] = year
            audio.save()

def add_metadata(audio_path: str,
                 cover_dir_path: str,
                 used_dir_path: str=None,
                 move_to_dir_path: str=None) -> bool:
    """
    Adds metadata to the provided audio file.
    If a tag is missing it asks the user to add it.

    Args:
        audio_path (str): Path to the audio file.
        cover_dir_path (str): Path to the cover directory. Used for the cover selection.
        used_dir_path (str, optional): Path to the used directory. Used for the cover selection.
        Defines the directory where the selected cover will be moved to.
        move_to_dir_path (str, optional): Path to the directory where the audio will be moved to.
        If no directory was provided the file will not be moved.
    Return:
        bool: False if a key interrupt was caught during input fetching.
        True when more audio file can be edited.
    """
    metadata_flags = check_metadata(audio_path)
    if metadata_flags < 0:
        return True # Either path does not exist, is not a file or is not supported.

    if used_dir_path and not cm.valid_dir_path(used_dir_path):
        return True # Provided used dir path is not valid.

    if move_to_dir_path and not cm.valid_dir_path(move_to_dir_path):
        return True # Provided move-to path is not valid.

    parsed_info = parse_filename(os.path.basename(audio_path))
    if parsed_info is None:
        return True # File does not have the right name format.

    title = parsed_info[1] if is_missing(metadata_flags, MetadataFlags.HAS_TITLE) else None
    artist = parsed_info[0] if is_missing(metadata_flags, MetadataFlags.HAS_ARTIST) else None

    default_album = f"{parsed_info[1]} - Single"
    album = None
    album_artist = None
    track_nr = None
    if is_missing(metadata_flags, MetadataFlags.HAS_ALBUM):
        tm_result, album = tm.ask_input_str("Album name", default=default_album)
        if tm_result == tm.TerminalResult.EXIT:
            return False
    
    if is_missing(metadata_flags, MetadataFlags.HAS_ALBUM_ARTIST) or album != default_album:
        tm_result, album_artist = tm.ask_input_str("Album artist", default=parsed_info[0])
        if tm_result == tm.TerminalResult.EXIT:
            return False
        
        default_track_nr = 1
        if not is_missing(metadata_flags, MetadataFlags.HAS_TRACK_NUMBER):
            raw = get_track_nr(audio_path)
            if raw:
                default_track_nr = raw
        if album != default_album or default_track_nr != 1:
            tm_result, track_nr = tm.ask_input_int("Track number", default=default_track_nr)
            if tm_result == tm.TerminalResult.EXIT:
                return False
        else:
            track_nr = 1

    genre = None
    if is_missing(metadata_flags, MetadataFlags.HAS_GENRE):
        tm_result, genre = tm.ask_input_str("Genre", default="")
        if tm_result == tm.TerminalResult.EXIT:
            return False

    year = None
    if is_missing(metadata_flags, MetadataFlags.HAS_YEAR):
        tm_result, year = tm.ask_input_int("Year", default=2025)
        if tm_result == tm.TerminalResult.EXIT:
            return False

    # Set all the basic metadata
    set_basic_metadata(audio_path, title, artist, album, album_artist, track_nr, 1, genre, year)

    if is_missing(metadata_flags, MetadataFlags.HAS_COVER):
        cover_path = cover.select_cover(cover_dir_path)
        if cover_path:
            cover.add_cover(audio_path, cover_path, used_dir_path)

    if is_missing(metadata_flags, MetadataFlags.HAS_BPM):
        bpm.add_bpm(audio_path)

    # Optional move...
    if move_to_dir_path:
        cm.move_file(audio_path, os.path.join(move_to_dir_path, os.path.basename(audio_path)))

    return True

def add_metadata_all(audio_dir_path: str,
                     cover_dir_path: str,
                     used_dir_path: str=None,
                     move_to_dir_path: str=None):
    """
    Adds the metadata to all the audio files in the audio_dir_path.

    Args:
        audio_dir_path (str): Path to the audio directory.
        cover_dir_path (str): Path to the cover directory. Used for the cover selection.
        used_dir_path (str, optional): Path to the used directory. Used for the cover selection.
        Defines the directory where the selected cover will be moved to.
        move_to_dir_path (str, optional): Path to the directory where the audio will be moved to.
    """
    if not cm.valid_dir_path(audio_dir_path):
        return
    if not cm.valid_dir_path(cover_dir_path):
        return
    if used_dir_path and not cm.valid_dir_path(used_dir_path):
        return
    if move_to_dir_path and not cm.valid_dir_path(move_to_dir_path):
        return

    files = [f for f in os.listdir(audio_dir_path)
             if os.path.isfile(os.path.join(audio_dir_path, f))]

    if not files:
        cm.log(cm.LogLevel.INFO, f"No audio files found in {audio_dir_path}")
        return

    cm.log(cm.LogLevel.INFO, "Press Ctr+C to exit.\n")

    for file in files:
        file_path = os.path.join(audio_dir_path, file)
        cm.log(cm.LogLevel.INFO, f"Processing: {file}")

        do_next = add_metadata(file_path, cover_dir_path, used_dir_path, move_to_dir_path)
        if not do_next:
            return # Exiting the main loop.

if __name__ == "__main__":
    add_metadata_all("../../Playlists/Trap",
                     "../covers/downsized",
                     "../covers/downsized/used"
                     #,"../../Playlists"
                     )