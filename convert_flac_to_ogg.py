"""FLAC -> OGG(Vorbis) 批量转换脚本（Minecraft 适用）

仅依赖 Python 标准库，通过 subprocess 调用系统 ffmpeg。
转换参数：libvorbis / -q:a 5 / 48000Hz / stereo / 仅音频流 / 保留元数据
"""

import subprocess
import sys
from pathlib import Path

# 目录配置
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "flac"
OUTPUT_DIR = BASE_DIR / "ogg"

# 转换参数（针对 Minecraft 优化）
FFMPEG_ARGS = [
    "-map", "0:a",           # 只取音频流，丢弃封面图等视频流
    "-map_metadata", "0",    # 保留源文件元数据
    "-c:a", "libvorbis",     # OGG Vorbis 编码器
    "-q:a", "5",             # 质量档位 ~160kbps
    "-ar", "48000",          # 采样率保持 48kHz
    "-ac", "2",              # 立体声
    "-y",                    # 覆盖已存在文件，避免交互阻塞
]

# 输出文件最小字节阈值（低于此值视为转换失败）
MIN_OUTPUT_BYTES = 10 * 1024  # 10 KB

# Minecraft mod 资源命名映射：FLAC 文件名(不含扩展名) -> OGG 文件名列表(不含扩展名)
# 规范：全小写，仅 a-z0-9_-，以英文为主
# 语言后缀使用 Minecraft 标准 xx_yy 格式（en_us / zh_cn / ja_jp / ko_kr 等）
# 纯音乐不加语言后缀
NAME_MAP: dict[str, list[str]] = {
    # 纯音乐（无语言后缀）
    "Genshin_Impact_Main_Theme": ["main_theme"],
    "Dream_Aria_梦之咏叹": ["dream_aria"],
    "未行之路_The_Road_Not_Taken": ["the_road_not_taken"],

    # 经过 / Passing Memories
    "经过": ["passing_memories_zh_cn"],
    "Passing_Memories": ["passing_memories_en_us"],
    "記憶の旅_Passing_Memories__记忆之旅": ["passing_memories_ja_jp"],

    # 回家的路 / The Long Way Home
    "回家的路": ["the_long_way_home_zh_cn"],
    "The_Long_Way_Home": ["the_long_way_home_en_us"],

    # 风的来信 / A Letter From the Wind
    "风的来信": ["a_letter_from_the_wind_zh_cn"],
    "A_Letter_From_the_Wind": ["a_letter_from_the_wind_en_us"],
    "風の思い出_A_Letter_From_the_Wind_jp": ["a_letter_from_the_wind_ja_jp"],
    "바람의 편지_A_Letter_From_the_Wind_hk": ["a_letter_from_the_wind_ko_kr"],
}


def get_output_names(src_stem: str) -> list[str]:
    """根据映射表获取合规的输出文件名列表，未映射的默认转小写并警告。"""
    if src_stem in NAME_MAP:
        return NAME_MAP[src_stem]
    # 兜底：转小写，非 a-z0-9_- 的字符替换为下划线
    fallback = "".join(c if c.isascii() and (c.isalnum() or c in "-_") else "_" for c in src_stem.lower())
    print(f"[警告] 文件名 '{src_stem}' 未在 NAME_MAP 中，使用兜底命名 '{fallback}'")
    return [fallback]


def convert_one(src: Path, dst: Path) -> bool:
    """转换单个 FLAC 文件到 OGG，成功返回 True。"""
    cmd = ["ffmpeg", "-i", str(src)] + FFMPEG_ARGS + [str(dst)]
    print(f"[转换] {src.name} -> {dst.name}")
    print(f"[命令] {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        print("[错误] 未找到 ffmpeg，请确认已安装并加入 PATH")
        return False

    # 检查返回码
    if result.returncode != 0:
        print(f"[失败] ffmpeg 返回码 {result.returncode}")
        print("---- stderr ----")
        print(result.stderr[-2000:])
        return False

    # 检查 stderr 中是否有 Error 关键字（即使返回码为 0 也要检查）
    if "Error" in result.stderr or "error" in result.stderr:
        print("[警告] stderr 中包含 Error 关键字，请检查：")
        print(result.stderr[-1500:])

    # 检查输出文件
    if not dst.exists():
        print("[失败] 输出文件未生成")
        return False

    size = dst.stat().st_size
    if size < MIN_OUTPUT_BYTES:
        print(f"[失败] 输出文件过小：{size} 字节（阈值 {MIN_OUTPUT_BYTES}）")
        return False

    print(f"[完成] 输出大小：{size / 1024:.1f} KB")
    return True


def main() -> int:
    if not INPUT_DIR.exists():
        print(f"[错误] 输入目录不存在：{INPUT_DIR}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    flac_files = sorted(INPUT_DIR.glob("*.flac"))
    if not flac_files:
        print(f"[警告] {INPUT_DIR} 下没有 .flac 文件")
        return 1

    print(f"找到 {len(flac_files)} 个 FLAC 文件")
    print(f"输出目录：{OUTPUT_DIR}")
    print("=" * 60)

    success = 0
    skipped = 0
    failed = 0
    for src in flac_files:
        output_names = get_output_names(src.stem)
        for out_name in output_names:
            dst = OUTPUT_DIR / (out_name + ".ogg")
            # 跳过已存在且大小正常的输出文件（增量转换）
            if dst.exists() and dst.stat().st_size >= MIN_OUTPUT_BYTES:
                print(f"[跳过] {dst.name} 已存在（{dst.stat().st_size / 1024:.1f} KB）")
                skipped += 1
                print("-" * 60)
                continue
            if convert_one(src, dst):
                success += 1
            else:
                failed += 1
            print("-" * 60)

    print(f"全部完成：成功 {success} 个，跳过 {skipped} 个，失败 {failed} 个")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
