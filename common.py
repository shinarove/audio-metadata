import os
import shutil
from enum import Enum

class AudioFileExtension(Enum):
    NOT_SUPPORTED = 0
    MP3 = 1
    M4A = 2

def valid_dir_path(dir_path: str) -> bool:
    """
    Checks if path exists. And the path points to a directory.

    Args:
        dir_path (str): The directory path to check.
    Returns:
        bool: True when the directory path is valid.
    """
    if not os.path.exists(dir_path):
        log(LogLevel.ERROR, f"Does not exists: {dir_path}")
        return False
    elif not os.path.isdir(dir_path):
        log(LogLevel.ERROR, f"Not a directory: {dir_path}")
        return False

    return True

def valid_file_path(file_path: str) -> bool:
    """
    Checks if path exists. And the path points to a file.

    Args:
        file_path (str): The file path to check for.
    Returns:
        bool: True when the file path is valid.
    """
    if not os.path.exists(file_path):
        log(LogLevel.ERROR, f"Does not exists: {file_path}")
        return False
    elif not os.path.isfile(file_path):
        log(LogLevel.ERROR, f"Not a file: {file_path}.")
        return False

    return True

def get_audio_file_extension(file_path: str) -> AudioFileExtension:
    """
    Get the file extension of a file.
    
    Args:
        file_path (str): The file path to get the extension from.
    Returns:
        FileExtension: The enum type of the file extension.
    """
    if not valid_file_path(file_path):
        return AudioFileExtension.NOT_SUPPORTED

    ext = os.path.splitext(file_path)[1].lower()
    match ext:
        case ".mp3":
            return AudioFileExtension.MP3
        case ".m4a":
            return AudioFileExtension.M4A
        case _:
            log(LogLevel.WARN, f"File is not supported: {file_path}")
            return AudioFileExtension.NOT_SUPPORTED


def move_file(source_path: str, dest_path: str):
    """
    Move a file to the destination path.
    """
    if not valid_file_path(source_path):
        log(LogLevel.ERROR, f"Move source does not exists: {source_path}")
        return

    if os.path.abspath(source_path) == os.path.abspath(dest_path):
        log(LogLevel.INFO, f"Move source and destination paths are equal: {source_path} == {dest_path}")
        return

    if os.path.exists(dest_path):
        log(LogLevel.WARN, f"Destination path already exists: {dest_path}")
        log(LogLevel.WARN, f"File will be overwritten!")

    shutil.move(source_path, dest_path)
    log(LogLevel.FINE, f"Successfully moved file to {os.path.dirname(dest_path)}.")

class LogLevel(Enum):
    SUCCESS = 0
    FINE = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    
def log(level: LogLevel, message: str):
    match level:
        case LogLevel.SUCCESS:
            print(f"✅ {message}")
        case LogLevel.FINE:
            print(f"💬 {message}")
        case LogLevel.INFO:
            print(f"ℹ️ {message}")
        case LogLevel.WARN:
            print(f"⚠️ {message}")
        case LogLevel.ERROR:
            print(f"❌ {message}")