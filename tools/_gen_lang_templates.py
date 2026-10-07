"""为所有支持的语言生成/更新 JSON 翻译模板。

当 CSV 条目增减时运行此脚本，可重新生成模板，
已填写的翻译值会被保留（需要手动合并或 git 恢复）。

模板包含三类 key：
- names:   CSV 中所有曲目名称（值为空，由用户填写翻译）
- regions: 所有地区名
- ui:      清单界面用字符串

运行：python tools/_gen_lang_templates.py
"""

import csv
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from regions import LANGUAGES, REGION_ORDER

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "yumemusic.csv"
LANGS_DIR = BASE_DIR / "langs"

UI_KEYS = [
    "旋曜玉帛 收集清单",
    "当前版本",
    "共",
    "项",
    "目录",
]


def _merge(existing: dict, template: dict) -> dict:
    """用模板的 key 结构更新 existing，保留已有翻译值。"""
    merged = {}
    for category, items in template.items():
        cat_existing = existing.get(category, {}) if isinstance(existing, dict) else {}
        if not isinstance(cat_existing, dict):
            cat_existing = {}
        merged[category] = {k: cat_existing.get(k, v) for k, v in items.items()}
    return merged


def main() -> int:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    names = [r["名称"] for r in rows]

    LANGS_DIR.mkdir(parents=True, exist_ok=True)

    template = {
        "names": {n: "" for n in names},
        "regions": {r: "" for r in REGION_ORDER},
        "ui": {k: "" for k in UI_KEYS},
    }

    for code, _label in LANGUAGES:
        path = LANGS_DIR / f"{code}.json"
        existing = {}
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing = {}

        data = _merge(existing, template)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"  更新 {path.name}（{len(names)} 个名称）")

    print(f"完成，共更新 {len(LANGUAGES)} 个语言模板于 {LANGS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
