# genshin-music-flac2ogg

原神主题曲 FLAC 转 Minecraft OGG 批量转换工具。

将 FLAC 无损音乐转换为符合 Minecraft Fabric / NeoForge mod 资源包规范的 OGG Vorbis 文件，自动处理命名规范、增量跳过、元数据保留与品质校验。

## 特性

- **Minecraft 命名规范**：自动生成全小写、仅含 `a-z0-9_-` 的合规文件名
- **多语言后缀**：按语言自动添加 `_en_us` / `_zh_cn` 后缀
- **增量转换**：已存在且大小正常的 OGG 文件自动跳过，新增文件只转换新增的
- **品质保障**：48kHz stereo / libvorbis -q:a 5 / 仅音频流（移除封面图）/ 保留元数据
- **错误校验**：检查 ffmpeg 返回码、stderr Error 关键字、输出文件大小阈值
- **零第三方依赖**：仅使用 Python 标准库，通过 subprocess 调用系统 ffmpeg

## 环境要求

- Python 3.10+
- ffmpeg（已编译 libvorbis 支持）

## 使用方法

1. 将 FLAC 文件放入 `flac/` 目录
2. 运行转换脚本：

```bash
python convert_flac_to_ogg.py
```

3. 转换后的 OGG 文件输出到 `ogg/` 目录

## 命名规范

Minecraft mod 资源包中音频文件必须满足：

- 全小写，仅含 `a-z`、`0-9`、`_`、`-`
- 以英文命名为主
- 文件名含中英文的单个源文件，生成两个 OGG（`_en_us` + `_zh_cn` 后缀）
- 纯英文/纯中文的源文件，按语言生成对应后缀的单个 OGG
- 纯音乐不加语言后缀

命名映射在脚本 `NAME_MAP` 中配置：

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

新增 FLAC 文件时，在 `NAME_MAP` 中添加映射即可。未映射的文件会兜底转小写并输出警告。

## 目录结构

```
.
├── flac/                  # FLAC 源文件（gitignore）
├── ogg/                   # OGG 输出文件（gitignore）
├── irc/                   # LRC 歌词文件（gitignore）
├── convert_flac_to_ogg.py # 转换脚本
├── .gitignore
└── README.md
```

## 转换参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 编码器 | libvorbis | OGG Vorbis |
| 质量 | -q:a 5 | ~160 kbps VBR |
| 采样率 | 48000 Hz | 保持源文件 |
| 声道 | 2 (stereo) | 保持源文件 |
| 流映射 | -map 0:a | 仅音频流，移除封面图 |
| 元数据 | -map_metadata 0 | 保留源文件标签 |
