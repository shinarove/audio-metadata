import os
import librosa
import argparse
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, TBPM

import common as cm

def find_bpm(audio_path: str) -> float:
    """
    Estimate BPM of the given audio file, using librosa.
    
    Args:
        audio_path (str): The path to the file, to find the BPM for.
    Returns:
        float: The estimated BPM value,
        or -1.0 when the file was not an audio file or something went wrong during estimation.
    """
    if cm.get_audio_file_extension(audio_path) == cm.AudioFileExtension.NOT_SUPPORTED:
        return -1.0
    
    try:
        y, sr = librosa.load(audio_path)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if len(tempo) > 0 and tempo[0] > 0.0:
            cm.log(cm.LogLevel.SUCCESS, f"Found BPM: {tempo[0]}")
            return tempo[0]
        else:
            cm.log(cm.LogLevel.WARN, f"Invalid BPM {tempo} returned.")
            return -1.0
        
    except Exception as e:
        cm.log(cm.LogLevel.WARN, f"An error occurred during BPM estimation.")
        return -1.0

def has_bpm(audio_path: str) -> bool:
    """
    Check if the audio file already has a BPM value defined.

    Args:
        audio_path (str): The path to the file, to check if the BPM value is already present.
    Returns:
        bool: True if the file has a BPM value, False otherwise.
    """
    ext = cm.get_audio_file_extension(audio_path)

    match ext:
        case cm.AudioFileExtension.NOT_SUPPORTED:
            return False
        case cm.AudioFileExtension.MP3:
            audio = MP3(audio_path, ID3=ID3)
            bpm_tag = audio.tags.get("TBPM")
            if bpm_tag and bpm_tag.text:
                try:
                    bpm = int(bpm_tag.text[0])
                    return bpm > 0
                except (ValueError, TypeError):
                    cm.log(cm.LogLevel.INFO, f"The first value in the mp3 tag \"TBPM\" is not an numerical value: {bpm_tag.text[0]}.")
                    return False
            else:
                cm.log(cm.LogLevel.FINE, f"No bpm value found.")
                return False
        case cm.AudioFileExtension.M4A:
            audio = MP4(audio_path)
            bpm_list = audio.tags.get("tmpo")
            if bpm_list and len(bpm_list) > 0:
                try:
                    bpm = int(bpm_list[0])
                    return bpm > 0
                except (ValueError, TypeError):
                    cm.log(cm.LogLevel.INFO, f"The first value in the m4a tag \"tmpo\" is not a numerical value: {bpm_list[0]}.")
                    return False
            else:
                cm.log(cm.LogLevel.FINE, f"No bpm value found for.")
                return False
    
def add_bpm(audio_path: str):
    """
    Adds the bpm to the metadata of the audio file.
    - First checks if a bpm value is already present in the audio file.
    - Then determines the bpm value of the audio file.

    Args:
        audio_path (str): The path to the file, to add the BPM value (if not present).
    """
    if has_bpm(audio_path):
        cm.log(cm.LogLevel.FINE, f"Has already a BPM value.")
        return

    bpm = find_bpm(audio_path)
    if bpm <= 0.0:
        return # Unsuccessful finding bpm for audio

    ext = cm.get_audio_file_extension(audio_path)
    bpm_value = int(round(bpm))

    match ext:
        case cm.AudioFileExtension.NOT_SUPPORTED:
            return
        case cm.AudioFileExtension.MP3:
            audio = MP3(audio_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            if "TBPM" in audio.tags:
                # Delete all old existing TBPM tags in file.
                audio.tags.delall("TBPM")
            audio.tags.add(TBPM(encoding=3, text=str(bpm_value)))
            audio.save(v2_version=3)
        case cm.AudioFileExtension.M4A:
            audio = MP4(audio_path)
            if audio.tags is None:
                audio.add_tags()
            audio["tmpo"] = [bpm_value]
            audio.save()

    cm.log(cm.LogLevel.SUCCESS, f"Successfully added BPM to {audio_path}.")

def add_bpm_all(dir_path: str):
    """
    Adds the bpm to all supported audio files from the given directory recursively.

    Args:
        dir_path (str): The path to the base directory.
    """
    if not cm.valid_dir_path(dir_path):
        return

    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = os.path.join(root, file)
            add_bpm(file_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add missing BPM information to audio files.")
    parser.add_argument(
        "-dir",
        type=str,
        required=True,
        help="Root directory which contains the audio files (.mp3, .m4a) to be analyzed."
    )
    args = parser.parse_args()
    root_dir = args.dir

    add_bpm_all(root_dir)