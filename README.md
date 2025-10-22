# 📸 Photo‑Cleaner
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/downloads/)
[![GitHub Actions CI](https://github.com/jimmyneutron99/photo-cleaner/actions/workflows/ci.yml/badge.svg)](https://github.com/jimmyneutron99/photo-cleaner/actions/workflows/ci.yml)

A **single‑file command‑line tool that:

* Strips **all** EXIF / IPTC / XMP metadata from JPEG, PNG, GIF, TIFF, WebP, etc.  
* Detects and **removes any hidden or appended data** (e.g. a zip file, encrypted blob, or stray bytes after the official end‑of‑image marker).  
* Re‑encodes the image and **overwrites the original file** in place.  
* Works on **Windows, macOS and Linux** (including WSL).

> **⚠️  The script rewrites your original files.**  
> Keep a backup or run a dry‑run (`-n`) first.

---  

## Table of Contents
- [Installation](#installation)  
- [Running the tool](#running-the-tool)  
- [CLI options](#cli-options)  
- [Contributing](#contributing)  
- [License](#license)  

---  

## Installation

```bash
# Clone the repository
git clone https://github.com/jimmyneutron99/photo-cleaner.git
cd photo-cleaner

# (Optional but recommended) create a virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate   # macOS / Linux
# On Windows use:
# .venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt


Running the tool

# Interactive mode – you will be prompted for a folder
python cleanphotos.py

# Or pass the folder path directly
python cleanphotos.py "/path/to/your/photos"

# Show the help / CLI options
python cleanphotos.py -h


CLI Options

-r, --recursive	Walk sub‑folders recursively (default: on).
-n, --dry-run	Show what would be cleaned without touching any files.
-v, --verbose	Print a line for every processed file.
-h, --help	Show the help message.
