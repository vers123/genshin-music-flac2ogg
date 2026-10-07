"""根据各语言截图提取的名称，填充 langs/{lang}.json 的 names 字段。"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from regions import cn_to_int

BASE = Path(__file__).resolve().parent.parent
LANGS_DIR = BASE / "langs"
TOOLS_DIR = Path(__file__).parent

# 读取有序的 CSV 键
zh_keys = [l.strip() for l in (TOOLS_DIR / "_zh_keys.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
print(f"CSV 键数量: {len(zh_keys)}")

LANGUAGES = ["en", "ja", "ko", "es", "fr", "ru", "th", "vi", "de", "id", "pt", "tr", "it", "zh-TW"]

# 编号项正则：提取 "其X" 部分
NUM_RE = re.compile(r"^旋曜玉帛·其([^()（）]+)(?:\((.*)\))?$")


def extract_number(key: str) -> int | None:
    """从 CSV 键提取阿拉伯数字，特殊项返回 None。"""
    m = NUM_RE.match(key)
    if not m:
        return None
    cn_num = m.group(1)
    return cn_to_int(cn_num)


def build_value(key: str, translated_name: str, prefix: str, lang: str) -> str:
    """根据键类型构建翻译值。"""
    m = NUM_RE.match(key)
    if not m:
        # 特殊项：直接使用翻译名
        return translated_name
    cn_num = m.group(1)
    alias = m.group(2)  # 可能为空（至冬项）

    if not alias:
        # 至冬项：翻译名已经是 "{prefix} {N}" 格式，直接使用
        return translated_name

    # 编号项有别名：构建 "{prefix} {N} ({translated_alias})"
    if lang == "zh-TW":
        # 繁体中文保留中文数字
        return f"旋曜玉帛·其{cn_num}({translated_name})"
    else:
        num = cn_to_int(cn_num)
        # 判断前缀分隔符
        if lang == "ja":
            sep = "·"
        elif lang == "ko":
            sep = " · "
        else:
            sep = " "
        return f"{prefix}{sep}{num} ({translated_name})"


for lang in LANGUAGES:
    names_file = TOOLS_DIR / f"_{lang}_names.txt"
    if not names_file.exists():
        print(f"跳过 {lang}: 文件不存在")
        continue

    lines = [l.rstrip("\n") for l in names_file.read_text(encoding="utf-8").splitlines()]
    prefix_line = lines[0]
    assert prefix_line.startswith("PREFIX="), f"{lang}: 第一行不是 PREFIX="
    prefix = prefix_line[len("PREFIX="):]
    names = lines[1:]

    if len(names) != len(zh_keys):
        print(f"警告 {lang}: 名称数量 {len(names)} != 键数量 {len(zh_keys)}")

    # 读取现有 JSON
    json_path = LANGS_DIR / f"{lang}.json"
    data = json.loads(json_path.read_text(encoding="utf-8"))

    filled = 0
    for i, key in enumerate(zh_keys):
        if i >= len(names):
            break
        translated = names[i]
        if not translated:
            continue
        value = build_value(key, translated, prefix, lang)
        if key in data["names"]:
            data["names"][key] = value
            filled += 1

    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    empty = sum(1 for v in data["names"].values() if not v)
    print(f"{lang}: 填充 {filled}, 剩余空值 {empty}, prefix='{prefix}'")

print("\n完成")
