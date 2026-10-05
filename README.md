# genshin-music-flac2ogg

A batch conversion tool that converts Genshin Impact main theme FLAC files into Minecraft OGG Vorbis files compliant with Fabric / NeoForge mod resource pack naming conventions.

## Features

- **Minecraft naming compliance**: auto-generates lowercase filenames using only `a-z0-9_-`
- **Language suffixes**: appends `_en_us` / `_zh_cn` suffixes based on the source language
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
- A single source file whose name contains both Chinese and English generates two OGG files (`_en_us` + `_zh_cn` suffixes)
- Pure English / pure Chinese source files generate a single OGG with the corresponding language suffix
- Instrumental tracks have no language suffix

The name mapping is configured via `NAME_MAP` in the script:

```python
NAME_MAP = {
    "A_Letter_From_the_Wind": ["a_letter_from_the_wind_en_us"],
    "Dream_Aria_梦之咏叹": ["dream_aria_en_us", "dream_aria_zh_cn"],
    "Genshin_Impact_Main_Theme": ["genshin_impact_main_theme"],
    "风的来信": ["a_letter_from_the_wind_zh_cn"],
    "The_Long_Way_Home": ["the_long_way_home_en_us"],
    "回家的路": ["the_long_way_home_zh_cn"],
}
```

When adding new FLAC files, add an entry to `NAME_MAP`. Unmapped files fall back to lowercased names with a warning.

## Directory Structure

```
.
├── flac/                  # FLAC source files (gitignored)
├── ogg/                   # OGG output files (gitignored)
├── irc/                   # LRC lyric files (gitignored)
├── convert_flac_to_ogg.py # conversion script
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
