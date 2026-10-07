# genshin-music-flac2ogg

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/vers123/genshin-music-flac2ogg/releases/tag/v1.0.0)

A batch conversion tool that converts Genshin Impact main theme FLAC files into Minecraft OGG Vorbis files compliant with Fabric / NeoForge mod resource pack naming conventions.

Also includes a small toolkit for maintaining the in-game music item catalog and generating a checkable collection list.

## Features

### FLAC to OGG conversion

- Minecraft naming compliance: auto-generates lowercase filenames using only a-z0-9_-
- Language suffixes: appends _zh / _en / _jp / _ko based on the source language
- Incremental conversion: skips existing valid OGG files; only converts newly added FLAC files
- Quality assurance: 48 kHz stereo / libvorbis -q:a 5 / audio stream only / metadata preserved
- Error validation: checks ffmpeg return code, stderr Error keywords, and output file size threshold
- Zero third-party dependencies: uses only the Python standard library, invoking ffmpeg via subprocess

### Catalog and checklist tools

- Merge-based CSV updates: append new items without overwriting manual edits
- Markdown checklist: clickable task list generated from the CSV
- Checkbox preservation: existing checked state survives regeneration, matched by item name
- Stable sorting: special series first, numbered items sorted numerically

## Requirements

- Python 3.10+
- ffmpeg (compiled with libvorbis support)

## Usage

### Convert FLAC to OGG

1. Place FLAC files in the flac/ directory.
2. Run the conversion script:

       python convert_flac_to_ogg.py

3. Converted OGG files are written to the ogg/ directory.

### Update the item catalog

Merge new items into the existing CSV (existing rows are kept):

       python tools/parse_yumemusic.py tools/raw_new.txt -o data/yumemusic.csv

Preview what would be added, without writing:

       python tools/parse_yumemusic.py tools/raw_new.txt -o data/yumemusic.csv --dry-run

Overwrite instead of merge:

       python tools/parse_yumemusic.py tools/raw_new.txt -o data/yumemusic.csv --overwrite

The input can be tab-separated or comma-separated. Duplicate header rows and blank rows are skipped.

### Generate the checklist

       python tools/csv_to_checklist.py

Output is written to data/yumemusic.md. To reset all checkboxes:

       python tools/csv_to_checklist.py --reset

## Naming Convention

Audio files in a Minecraft mod resource pack must follow these rules:

- All lowercase, containing only a-z, 0-9, _, -
- English names as the base
- Language suffixes: zh (Chinese), en (English), jp (Japanese), ko (Korean)
- Instrumental tracks have no language suffix

The mapping is configured in data/name_map.csv with columns:

    source_stem, output_stem, display_name, rarity, type, source, note

When adding new FLAC files, add a row to data/name_map.csv.
If data/name_map.csv is missing or empty, the script falls back to the built-in DEFAULT_NAME_MAP.
Unmapped files fall back to lowercased names with a warning.

## Data Files

- data/name_map.csv: FLAC source stem to OGG output stem mapping, read by the conversion script.
- data/yumemusic.csv: metadata archive of the in-game item catalog, maintained manually or via the parser.
- data/yumemusic.md: generated Markdown checklist, not used by the conversion script.

### Catalog CSV format

data/yumemusic.csv has 6 columns:

    icon, name, rarity, type, source, usage

The name column is the unique key used for merging and checkbox matching.

### Data Sources

- data/yumemusic.csv can be regenerated or merged from a raw item list:

        python tools/parse_yumemusic.py raw.txt -o data/yumemusic.csv

  The raw input must have 6 columns. Duplicate header rows and blank rows are skipped.
  By default, existing rows are preserved and only new names are appended.

- data/name_map.csv is maintained manually. Each row maps one FLAC source stem
  to one OGG output stem. When adding a new track, append a row here instead of
  editing the Python script.

## Checklist

data/yumemusic.md is a Markdown task list. Items are grouped into two sections:

- Special: tracks whose name does not match the pattern "旋曜玉帛·其N". These include
  album tracks like "《风的来信》·其一" and sub-series like "奇域旋律·xxx".
  Series order is controlled by SERIES_ORDER in tools/csv_to_checklist.py.
- Numbered: tracks matching "旋曜玉帛·其N", sorted by the numeric value of N.

Checked state is preserved across regeneration. The script reads the existing
data/yumemusic.md, collects all names marked with [x], and reapplies the mark
to matching rows in the new output. Items that disappear from the CSV are dropped
along with their state.

data/yumemusic.md is listed in .gitignore by default. Remove that line if you
want to track your collection progress in version control.

## Directory Structure

    .
    |-- data/
    |   |-- name_map.csv
    |   |-- yumemusic.csv
    |   `-- yumemusic.md
    |-- tools/
    |   |-- parse_yumemusic.py
    |   `-- csv_to_checklist.py
    |-- flac/
    |-- ogg/
    |-- irc/
    |-- convert_flac_to_ogg.py
    |-- .gitattributes
    |-- .gitignore
    `-- README.md

## Conversion Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Encoder | libvorbis | OGG Vorbis |
| Quality | -q:a 5 | ~160 kbps VBR |
| Sample rate | 48000 Hz | preserved from source |
| Channels | 2 (stereo) | preserved from source |
| Stream map | -map 0:a | audio only, cover art removed |
| Metadata | -map_metadata 0 | source tags preserved |

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project is licensed under the MIT License. See LICENSE for details.
