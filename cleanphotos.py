#!/usr/bin/env python3
"""
cleanphotos.py
==============

A tiny command‑line utility that:

* Walks a folder (recursively) and finds common image types.
* Strips ALL metadata (EXIF / IPTC / XMP).
* Removes any data that appears after the official end‑of‑file marker,
  which is where hidden or encrypted payloads are often stored.
* Re‑encodes the image with Pillow, thereby discarding any
  obscure “metadata‑like” structures inside the image stream.
* Overwrites the original file with the cleaned version.

⚠️  The script *replaces* the original files.  Keep a backup of
    anything you don’t want to lose.

Usage
-----
    python cleanphotos.py            # you will be prompted for a folder
    python cleanphotos.py /path/to/folder   # folder supplied as argument
"""

import os
import sys
import argparse
import pathlib
import shutil
import tempfile
from typing import List

from tqdm import tqdm
from PIL import Image, UnidentifiedImageError

# ----------------------------------------------------------------------
# Helper functions for “trailing‑data trimming”
# ----------------------------------------------------------------------


def trim_jpeg(data: bytes) -> bytes:
    """
    JPEG files end with the two bytes 0xFF 0xD9.
    Anything after the *last* occurrence of those bytes is considered
    trailing data and is removed.
    """
    eoi = b'\xff\xd9'
    pos = data.rfind(eoi)
    if pos == -1:
        # Not a valid JPEG – just return the original data.
        return data
    # Include the EOI marker itself.
    return data[: pos + len(eoi)]


def trim_png(data: bytes) -> bytes:
    """
    PNG files end with the IEND chunk:
        00 00 00 00 49 45 4E 44 AE 42 60 82
    The script parses the chunk list until it finds IEND,
    then discards everything after that.
    """
    # PNG signature (first 8 bytes) must be present.
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        return data  # Not a PNG.

    # Scan chunks.
    offset = 8  # start after signature
    while offset + 8 <= len(data):
        # Each chunk: length (4), type (4), data (length), CRC (4)
        length = int.from_bytes(data[offset : offset + 4], "big")
        ctype = data[offset + 4 : offset + 8]

        # Move to next chunk start.
        next_offset = offset + 8 + length + 4  # 8 header + data + CRC

        if ctype == b'IEND':
            # Return everything up to (and including) IEND chunk.
            return data[: next_offset]

        offset = next_offset

    # No IEND found – return original.
    return data


def trim_gif(data: bytes) -> bytes:
    """
    GIF files end with a trailer byte 0x3B.
    Anything after the *last* 0x3B is stripped.
    """
    trailer = b'\x3b'
    pos = data.rfind(trailer)
    if pos == -1:
        return data
    return data[: pos + 1]


def trim_webp(data: bytes) -> bytes:
    """
    WebP is based on RIFF. The file should end exactly at the size indicated in the header.
    If extra bytes exist after that size they are removed.
    """
    if not data.startswith(b'RIFF'):
        return data
    # Bytes 4‑7 contain the file size (little‑endian) *excluding* the 8‑byte RIFF header.
    declared_size = int.from_bytes(data[4:8], "little")
    expected_len = declared_size + 8
    if len(data) > expected_len:
        return data[:expected_len]
    return data


def trim_image_data(data: bytes, ext: str) -> bytes:
    """
    Dispatch to the appropriate trimming routine based on extension.
    """
    ext = ext.lower()
    if ext in (".jpg", ".jpeg"):
        return trim_jpeg(data)
    if ext == ".png":
        return trim_png(data)
    if ext == ".gif":
        return trim_gif(data)
    if ext == ".webp":
        return trim_webp(data)
    # For TIFF/RAW formats we simply return the original bytes – they are
    # already handled by metadata stripping via Pillow.
    return data


# ----------------------------------------------------------------------
# Core cleaning logic
# ----------------------------------------------------------------------


def clean_image_file(path: pathlib.Path) -> bool:
    """
    Returns True if the file was successfully cleaned, False otherwise.
    The function:
      * Reads the raw bytes.
      * Removes any trailing data after the official EOF marker.
      * Loads the image with Pillow (which discards EXIF, IPTC, XMP, etc.).
      * Re‑saves the image to a temporary file (same format, no metadata).
      * Atomically replaces the original file with the cleaned temporary file.
    """
    try:
        raw = path.read_bytes()
    except Exception as e:
        print(f"❌ Unable to read {path}: {e}")
        return False

    # 1️⃣  Trim any trailing data that may have been appended.
    trimmed = trim_image_data(raw, path.suffix)

    # 2️⃣  Load with Pillow – this strips all metadata automatically.
    #     We use a BytesIO so Pillow works on the trimmed data even if
    #     the original file had extra garbage.
    from io import BytesIO

    try:
        img = Image.open(BytesIO(trimmed))
        img.load()  # force loading, catches truncated files
    except UnidentifiedImageError:
        print(f"⚠️  Pillow cannot identify {path}; skipping.")
        return False
    except Exception as e:
        print(f"❌ Error opening {path}: {e}")
        return False

    # 3️⃣  Re‑encode and write to a temporary location.
    # Preserve the original format (JPEG, PNG, …) so the file extension stays valid.
    format_name = img.format  # e.g. "JPEG", "PNG"
    if format_name is None:
        # Fallback to extension‑based guess.
        format_name = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".gif": "GIF",
            ".tif": "TIFF",
            ".tiff": "TIFF",
            ".webp": "WEBP",
        }.get(path.suffix.lower(), "PNG")

    # Pillow will drop all EXIF/metadata unless we explicitly pass it.
    # For JPEG we also explicitly set `optimize=True` to recompress a bit.
    save_kwargs = {}
    if format_name == "JPEG":
        save_kwargs["quality"] = 95
        save_kwargs["optimize"] = True
        # Do not save EXIF at all.
    elif format_name == "PNG":
        save_kwargs["optimize"] = True

    # Temporary path in the same folder – this makes atomic `replace` work on
    # Windows as well.
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=path.suffix, dir=path.parent)
    os.close(tmp_fd)  # Pillow will open it itself.

    try:
        img.save(tmp_path, format=format_name, **save_kwargs)
    except Exception as e:
        print(f"❌ Failed to save cleaned image for {path}: {e}")
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False
    finally:
        img.close()

    # 4️⃣  Atomically replace the original file.
    try:
        # Preserve original file permissions.
        shutil.copymode(path, tmp_path)
        os.replace(tmp_path, path)  # atomic on most platforms
    except Exception as e:
        print(f"❌ Failed to replace original file {path}: {e}")
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return False

    return True


def find_image_files(root: pathlib.Path) -> List[pathlib.Path]:
    """
    Recursively collect files with known image extensions.
    """
    img_exts = {".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".webp"}
    files = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            p = pathlib.Path(dirpath) / name
            if p.suffix.lower() in img_exts:
                files.append(p)
    return files


# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Scan a folder, strip all metadata and trailing data from image files, and overwrite the originals."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Path to the folder containing images (if omitted you will be prompted).",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=True,
        help="Search sub‑folders recursively (default: on).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Do a dry run – report what would be cleaned but do not modify any files.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print a line for every processed file.",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()

    # 0️⃣  Determine folder path.
    if args.folder is None:
        folder_input = input("📂 Enter the full path to the folder containing your photos: ").strip()
        folder = pathlib.Path(folder_input).expanduser().resolve()
    else:
        folder = pathlib.Path(args.folder).expanduser().resolve()

    if not folder.is_dir():
        print(f"❗  The path '{folder}' is not a readable directory.")
        sys.exit(1)

    # 1️⃣  Build the list of image files.
    image_files = find_image_files(folder)
    if not image_files:
        print("🔎 No image files found in the given folder.")
        sys.exit(0)

    print(f"🔎 Found {len(image_files)} image file(s) under {folder}")

    # 2️⃣  Process each file.
    cleaned = 0
    failed = 0

    iterator = tqdm(image_files, desc="Cleaning", unit="file") if not args.dry_run else image_files

    for img_path in iterator:
        if args.verbose:
            print(f"🔧 Processing: {img_path}")

        if args.dry_run:
            # In dry‑run mode we just report the actions we *would* take.
            print(f"[DRY‑RUN] Would clean: {img_path}")
            continue

        success = clean_image_file(img_path)
        if success:
            cleaned += 1
        else:
            failed += 1

    # 3️⃣  Summary
    print("\n🗒️  Summary")
    print(f"   ✔️  Cleaned images : {cleaned}")
    if failed:
        print(f"   ❌  Failed to clean : {failed}")
    else:
        print("   🎉  No errors encountered.")
    if args.dry_run:
        print("\n⚠️  This was a **dry‑run**.  No files were actually modified.")


if __name__ == "__main__":
    # Ensure the script runs with an unbuffered stdout (helps with tqdm on Windows)
    sys.stdout.reconfigure(line_buffering=True)
    main()