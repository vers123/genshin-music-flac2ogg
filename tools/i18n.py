"""多语言支持模块。

语言文件位于 langs/{code}.json，结构：
{
  "names":   { "旋曜玉帛·青空": "Sky", ... },
  "regions": { "蒙德": "Mondstadt", ... },
  "ui":      { "旋曜玉帛 收集清单": "Yumemusic Collection Checklist", ... }
}

翻译文本由用户自行填写；缺失时回退到简体中文，再回退到原文。
"""

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
LANGS_DIR = BASE_DIR / "langs"


def _load(lang_code: str) -> dict[str, Any]:
    path = LANGS_DIR / f"{lang_code}.json"
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}


class Translator:
    """翻译器：names / regions / ui 三类文本，带两级回退。"""

    def __init__(self, lang_code: str = "zh-CN") -> None:
        self.lang_code = lang_code
        self._data = _load(lang_code)
        # 简体中文作为第一回退
        self._fallback = _load("zh-CN") if lang_code != "zh-CN" else {}

    def _get(self, category: str, key: str) -> str | None:
        cat = self._data.get(category)
        if isinstance(cat, dict) and key in cat:
            val = cat[key]
            if isinstance(val, str) and val:
                return val
        fb = self._fallback.get(category)
        if isinstance(fb, dict) and key in fb:
            val = fb[key]
            if isinstance(val, str) and val:
                return val
        return None

    def name(self, original: str) -> str:
        """翻译曲目名称，缺失则返回原文。"""
        return self._get("names", original) or original

    def region(self, original: str) -> str:
        """翻译地区名，缺失则返回原文。"""
        return self._get("regions", original) or original

    def ui(self, key: str) -> str:
        """翻译界面字符串，缺失则返回 key 本身。"""
        return self._get("ui", key) or key


def list_languages() -> list[str]:
    """返回 langs/ 目录下已存在的语言代码列表。"""
    if not LANGS_DIR.exists():
        return []
    return sorted(p.stem for p in LANGS_DIR.glob("*.json"))
