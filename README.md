# genshin-music-flac2ogg

A batch conversion tool that converts Genshin Impact main theme FLAC files into Minecraft OGG Vorbis files compliant with Fabric / NeoForge mod resource pack naming conventions.

## Features

- **Minecraft naming compliance**: auto-generates lowercase filenames using only `a-z0-9_-`
- **Language suffixes**: appends `_zh` / `_en` / `_jp` / `_ko` suffixes based on the source language
- **Incremental conversion**: skips existing valid OGG files; only converts newly added FLAC files
- **Quality assurance**: 48 kHz stereo / libvorbis -q:a 5 / audio stream only (cover art removed) / metadata preserved
- **Error validation**: checks ffmpeg return code, stderr Error keywords, and output file size threshold
- **Zero third-party dependencies**: uses only the Python standard library, invoking ffmpeg via subprocess

## Requirements

- Python 3.10+
- ffmpeg (compiled with libvorbis support)

## Usage

1. Place FLAC files in the `flac/` directory.
2. Run the conversion script:

```bash
python convert_flac_to_ogg.py
```

3. Converted OGG files are written to the `ogg/` directory.

## Naming Convention

Audio files in a Minecraft mod resource pack must follow these rules:

- All lowercase, containing only `a-z`, `0-9`, `_`, `-`
- English names as the base
- Language suffixes: `zh` (Chinese), `en` (English), `jp` (Japanese), `ko` (Korean)
- Instrumental tracks have no language suffix

The mapping is configured in `data/name_map.csv`:

```csv
source_stem,output_stem,display_name,rarity,type,source,note
Genshin_Impact_Main_Theme,main_theme,原神主题曲,4星,旋曜玉帛,大世界拾取,
```

When adding new FLAC files, add a row to `data/name_map.csv`.
If `data/name_map.csv` is missing or empty, the script falls back to the built-in `DEFAULT_NAME_MAP`.
Unmapped files fall back to lowercased names with a warning.

## Data Files

- `data/name_map.csv`: FLAC source stem to OGG output stem mapping, read by the conversion script.
- `data/yumemusic.csv`: full metadata archive of the in-game "旋曜玉帛" items (not used by the script).

## Directory Structure

```text
.
├── data/
│   ├── name_map.csv
│   └── yumemusic.csv
├── flac/
├── ogg/
├── irc/
├── convert_flac_to_ogg.py
├── .gitignore
└── README.md
```

## Conversion Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Encoder | libvorbis | OGG Vorbis |
| Quality | -q:a 5 | ~160 kbps VBR |
| Sample rate | 48000 Hz | preserved from source |
| Channels | 2 (stereo) | preserved from source |
| Stream map | -map 0:a | audio only, cover art removed |
| Metadata | -map_metadata 0 | source tags preserved |
