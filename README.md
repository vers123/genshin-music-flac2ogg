# genshin-music-flac2ogg

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/vers123/genshin-music-flac2ogg/releases/tag/v1.1.0)

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
- Data validation: checks for empty fields, duplicate numbers, missing numbers in region ranges, and unclassified items
- Markdown checklist: clickable task list grouped by in-game region, generated from the CSV
- Checkbox preservation: existing checked state survives regeneration, matched by normalized item name (works across renames and languages)
- Multi-language output: generate checklists in 15 languages via `--lang`; translations live in `langs/*.json` with fallback to Simplified Chinese
- One-click build: `tools/build.py` runs parse → validate → generate all language checklists

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

Run data validation (empty fields / duplicate numbers / missing numbers / unclassified items):

       python tools/parse_yumemusic.py tools/raw_new.txt -o data/yumemusic.csv --validate

Preview what would be added, without writing:

       python tools/parse_yumemusic.py tools/raw_new.txt -o data/yumemusic.csv --dry-run

Overwrite instead of merge:

       python tools/parse_yumemusic.py tools/raw_new.txt -o data/yumemusic.csv --overwrite

The input can be tab-separated or comma-separated. Duplicate header rows and blank rows are skipped.
Names containing commas inside parentheses are repaired automatically.

### Generate the checklist

       python tools/csv_to_checklist.py

Output is written to `data/yumemusic.md`. To reset all checkboxes:

       python tools/csv_to_checklist.py --reset

Generate a checklist in another language (e.g. English, Japanese):

       python tools/csv_to_checklist.py --lang en
       python tools/csv_to_checklist.py --lang ja

Output is written to `data/yumemusic_{lang}.md`. Checkbox state is always read from the
Chinese `data/yumemusic.md`, so progress stays consistent across all languages.

### One-click build

Parse, validate, and regenerate the CSV plus checklists for all languages that have
a translation file in `langs/`:

       python tools/build.py

Build only specific languages:

       python tools/build.py --langs zh-CN,en,ja

Skip validation or reset all checkboxes:

       python tools/build.py --no-validate
       python tools/build.py --reset

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
- data/yumemusic.md: generated Markdown checklist (Chinese), not used by the conversion script.
- data/yumemusic_{lang}.md: generated Markdown checklists for other languages.
- langs/{code}.json: translation files for 15 languages (zh-CN, zh-TW, en, ja, ko, es, fr, ru, th, vi, de, id, pt, tr, it). Each file has `names`, `regions`, and `ui` keys. Missing translations fall back to Simplified Chinese, then the original text. Regenerate templates with `python tools/_gen_lang_templates.py` when items are added or removed.

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

`data/yumemusic.md` is a Markdown task list. Items are grouped by in-game region,
with a table of contents at the top for quick navigation.

- Region grouping is determined by number ranges and keywords configured in
  `tools/regions.py` (`NUMBER_REGIONS`, `KEYWORD_REGIONS`).
- Special series (album tracks, sub-series) are ordered via `SPECIAL_ORDER`.
- Numbered tracks ("旋曜玉帛·其N") are sorted by the numeric value of N.

Checked state is preserved across regeneration. The script reads the existing
Chinese `data/yumemusic.md`, collects all names marked with `[x]` (normalized by
removing parenthesized aliases and `《》`), and reapplies the mark to matching rows.
Items that disappear from the CSV are dropped along with their state.

For other languages (`data/yumemusic_{lang}.md`), checkbox state is always read
from the Chinese `data/yumemusic.md`, so your progress stays consistent across
all language versions.

`data/yumemusic.md` and `data/yumemusic_*.md` are listed in `.gitignore` by
default. Remove those lines if you want to track your collection progress in
version control.

## Directory Structure

    .
    |-- data/
    |   |-- name_map.csv
    |   |-- yumemusic.csv
    |   |-- yumemusic.md            # generated (zh-CN)
    |   `-- yumemusic_*.md          # generated (other languages)
    |-- langs/
    |   `-- {code}.json             # 15 translation files
    |-- tools/
    |   |-- regions.py              # shared constants (regions, ranges, languages)
    |   |-- i18n.py                 # translation system with fallback
    |   |-- parse_yumemusic.py      # raw text -> CSV (with --validate)
    |   |-- csv_to_checklist.py     # CSV -> Markdown checklist (--lang)
    |   |-- build.py                # one-click build pipeline
    |   `-- _gen_lang_templates.py  # regenerate langs/*.json templates
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
