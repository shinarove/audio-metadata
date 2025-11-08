import os
import argparse
import shutil
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, APIC
from tkinter import Tk, filedialog
from enum import Enum

import common as cm

class ImgFileExtension(Enum):
    NOT_SUPPORTED = 0
    SUPPORTED = 1

def get_img_file_extension(img_path: str) -> ImgFileExtension:
    """
    Get the image file extension of the given file.

    Args:
        img_path (str): The path to the file to get the extension of.
    Returns:
        ImgFileExtension: The enum type of the image file extension.
    """
    if not cm.valid_file_path(img_path):
        return ImgFileExtension.NOT_SUPPORTED

    ext = os.path.splitext(img_path)[1].lower()
    if ext in [".jpg", ".jpeg", ".png"]:
        return ImgFileExtension.SUPPORTED
    else:
        cm.log(cm.LogLevel.WARN, f"The type of the image file: {img_path} is not a supported.")
        return ImgFileExtension.NOT_SUPPORTED


def has_cover(audio_path: str) -> bool:
    """
    Check if the audio file has already a cover image.

    Args:
        audio_path (str): The path to the file, to check if the cover image is already present.
    Returns:
        bool: True if the file has a cover image, False otherwise.
    """
    ext = cm.get_audio_file_extension(audio_path)

    match ext:
        case cm.AudioFileExtension.NOT_SUPPORTED:
            return False
        case cm.AudioFileExtension.MP3:
            audio = MP3(audio_path)
            if audio.tags:
                for tag in audio.tags.values():
                    if tag.FrameID == "APIC":
                        return True
            cm.log(cm.LogLevel.FINE, f"No cover image found.")
            return False
        case cm.AudioFileExtension.M4A:
            audio = MP4(audio_path)
            if "covr" in audio.tags and len(audio.tags["covr"]) > 0:
                return True
            cm.log(cm.LogLevel.FINE, f"No cover image found.")
            return False
    
def select_cover(cover_dir_path: str) -> str | None:
    """
    Open a file dialog to select a cover image.

    Args:
        cover_dir_path (str): The path to the cover directory. The dialog menu will open this directory.
    Returns:
        str: The path to the selected cover image. None if nothing was selected,
        a non image was selected or something went wrong.
    """
    if not cm.valid_dir_path(cover_dir_path):
        return None

    root = Tk()
    root.withdraw()
    cover_path = filedialog.askopenfilename(
        title="Select Cover Image",
        initialdir=cover_dir_path,
        filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
    )
    root.destroy()
    if not cover_path:
        cm.log(cm.LogLevel.FINE, "No cover image selected.")
        return None

    if get_img_file_extension(cover_path) == ImgFileExtension.NOT_SUPPORTED:
        return None
        
    return cover_path

def add_cover(audio_path: str, cover_path: str, used_dir_path: str=None):
    """
    Add the cover image to the audio file. If it does not have a cover image already.

    Args:
        audio_path (str): The path to the file, to add the cover image.
        cover_path (str): The path to the cover image.
        used_dir_path (str, optional): The path to the "used" directory. If set the cover image will be moved there.
    """
    if used_dir_path and not cm.valid_dir_path(used_dir_path):
        return

    img_ext = get_img_file_extension(cover_path)
    if img_ext == ImgFileExtension.NOT_SUPPORTED:
        return

    if has_cover(audio_path):
        cm.log(cm.LogLevel.FINE, f"Has already a cover image.")
        return

    audio_ext = cm.get_audio_file_extension(audio_path)
    match audio_ext:
        case cm.AudioFileExtension.NOT_SUPPORTED:
            return
        case cm.AudioFileExtension.MP3:
            audio = MP3(audio_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            if "APIC" in audio.tags:
                audio.tags.delall("APIC")
            with open(cover_path, "rb") as img:
                audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img.read()))
            audio.save(v2_version=3)
        case cm.AudioFileExtension.M4A:
            audio = MP4(audio_path)
            with open(cover_path, "rb") as img:
                audio["covr"] = [MP4Cover(img.read(), imageformat=MP4Cover.FORMAT_JPEG)]
            audio.save()
    cm.log(cm.LogLevel.SUCCESS, f"Successfully added cover to {audio_path}.")

    # Optional: Move cover_path to used_dir only if it is not already there.
    if used_dir_path:
        # If cover is already inside used_dir, do nothing.
        if os.path.abspath(os.path.dirname(cover_path)) == os.path.abspath(used_dir_path):
            cm.log(cm.LogLevel.FINE, "Cover already located in the used directory. No move required.")
            return

        dest_path = os.path.join(used_dir_path, os.path.basename(cover_path))

        # If a file with same name already exists: do not overwrite.
        if os.path.exists(dest_path):
            cm.log(cm.LogLevel.WARN, f"Cover not moved: A file with the same name already exists in {used_dir_path}.")
            return

        shutil.move(cover_path, dest_path)
        cm.log(cm.LogLevel.FINE, f"Successfully moved cover to {used_dir_path}.")

def add_cover_all(dir_path: str, cover_dir_path: str, used_dir_path: str=None):
    """
    Add the cover image to all supported audio files from the given directory recursively.

    Args:
        dir_path (str): The path to the base directory
        cover_dir_path (str): The path to the directory with cover images.
        used_dir_path (str, optional): The path to the "used" directory. If set the cover image will be moved there.
    """
    if used_dir_path and not cm.valid_dir_path(used_dir_path):
        return

    if not cm.valid_dir_path(dir_path) and not cm.valid_dir_path(cover_dir_path):
        return

    for root, _, files in os.walk(root_dir):
        for file in files:
            print(f"Adding cover image to {file}.")
            audio_path = str(os.path.join(root, file))
            cover_path = select_cover(cover_dir_path)
            if cover_path:
                add_cover(audio_path, cover_path, used_dir_path)
                
                
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add missing cover image to audio files.")
    parser.add_argument(
        "-dir",
        type=str,
        required=True,
        help="Root directory which contains the audio files (.mp3, .m4a) to be edited."
    )
    args = parser.parse_args()
    root_dir = args.dir

    add_cover_all(root_dir, "../covers/downsized", "../covers/downsized/used")