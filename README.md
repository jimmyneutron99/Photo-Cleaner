# 📸 Photo‑Cleaner  

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)  
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://www.python.org/downloads/)  
[![GitHub Actions CI](https://github.com/jimmyneutron99/photo-cleaner/actions/workflows/ci.yml/badge.svg)](https://github.com/<YOUR_USER>/photo-cleaner/actions/workflows/ci.yml)

A **single‑file, zero‑dependency‑except‑Pillow** command‑line tool that:

* Strips **all** EXIF / IPTC / XMP metadata from JPEG, PNG, GIF, TIFF, WebP, etc.  
* Detects and **removes any hidden or appended data** (e.g. a zip file, encrypted blob, or any stray bytes after the official end‑of‑image marker).  
* Re‑encodes the image and **overwrites the original file** in place.  
* Works on **Windows, macOS and Linux** (including WSL).  

> **⚠️  The script rewrites your original files.**  
> Keep a backup or run a dry‑run (`‑n`) first.

---

## Table of Contents  

- [Installation](#installation)  
- [Usage](#usage)  
- [Examples](#examples)  
- [How it works](#how-it-works)  
- [CLI options](#cli-options)  
- [Running a dry‑run](#dry‑run)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Installation  

```bash
# Clone the repo
git clone https://github.com/<YOUR_USER>/photo-cleaner.git
cd photo-cleaner

# (Optional but recommended) use a virtual environment
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Usage

# Interactive mode (you will be prompted for the folder)
python cleanphotos.py

# Or give the folder directly
python cleanphotos.py "/path/to/your/photos"

# Show help
python cleanphotos.py -h

# CLI Options

-r, --recursive	Walk sub‑folders recursively (default: on).
-n, --dry-run	Show what would be cleaned without touching any files.
-v, --verbose	Print a line for every processed file.
-h, --help	Show the help message.
