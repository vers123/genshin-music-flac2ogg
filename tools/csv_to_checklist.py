import argparse
import csv
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = BASE_DIR / "data" / "yumemusic.csv"
DEFAULT_OUTPUT = BASE_DIR / "data" / "yumemusic.md"

NORMAL_PATTERN = re.compile(r"^旋曜玉帛·其[零一二三四五六七八九十百\d]+$")

# 匹配 "- [x] 名称  <!-- 来源 -->" 或 "- [x] 名称"
CHECKBOX_PATTERN = re.compile(r"^- \[([ xX])\]\s+(.+?)(?:\s+<!--.*?-->)?\s*$")

SERIES_ORDER = [
    "《风的来信》",
    "《回家的路》",
    "奇域旋律",
    "单曲",
    "其他",
]

CN_NUM = {
    "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}


def cn_to_int(s: str) -> int:
    if s.isdigit():
        return int(s)
    total = section = 0
    for ch in s:
        if ch == "百":
            section = (section or 1) * 100
            total += section
            section = 0
        elif ch == "十":
            section = (section or 1) * 10
            total += section
            section = 0
        elif ch in CN_NUM:
            section = CN_NUM[ch]
        else:
            return -1
    return total + section


def parse_special(name: str):
    m = re.match(r"^旋曜玉帛·《(.+?)》·其(.+)$", name)
    if m:
        return (f"《{m.group(1)}》", cn_to_int(m.group(2)))
    m = re.match(r"^旋曜玉帛·奇域旋律·(.+)$", name)
    if m:
        return ("奇域旋律", m.group(1))
    m = re.match(r"^旋曜玉帛·(.+)$", name)
    if m:
        return ("单曲", m.group(1))
    return ("其他", name)


def series_rank(series: str) -> int:
    try:
        return SERIES_ORDER.index(series)
    except ValueError:
        return len(SERIES_ORDER)


def special_sort_key(name: str):
    series, sub = parse_special(name)
    rank = series_rank(series)
    if isinstance(sub, int):
        return (rank, 0, sub, name)
    return (rank, 1, 0, sub, name)


def normal_sort_key(name: str):
    m = re.search(r"其([零一二三四五六七八九十百]+|\d+)", name)
    return cn_to_int(m.group(1)) if m else 10**9


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_checked(path: Path) -> set[str]:
    """从已有 MD 里读出所有已勾选的名称。"""
    if not path.exists():
        return set()
    checked: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = CHECKBOX_PATTERN.match(line.strip())
        if not m:
            continue
        if m.group(1).lower() == "x":
            checked.add(m.group(2).strip())
    return checked


def format_item(row: dict, checked: bool) -> str:
    name = row["名称"]
    source = row["来源"] or ""
    mark = "x" if checked else " "
    suffix = f"  <!-- {source} -->" if source else ""
    return f"- [{mark}] {name}{suffix}"


def render(rows: list[dict], checked: set[str]) -> str:
    special, normal = [], []
    for r in rows:
        (normal if NORMAL_PATTERN.match(r["名称"]) else special).append(r)

    special.sort(key=lambda r: special_sort_key(r["名称"]))
    normal.sort(key=lambda r: normal_sort_key(r["名称"]))

    lines = ["# 旋曜玉帛 收集清单", "", f"共 {len(rows)} 项。", ""]
    if special:
        lines.append("## 特殊")
        lines.append("")
        lines.extend(format_item(r, r["名称"] in checked) for r in special)
        lines.append("")
    if normal:
        lines.append("---")
        lines.append("")
        lines.append("## 其N")
        lines.append("")
        lines.extend(format_item(r, r["名称"] in checked) for r in normal)
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="yumemusic.csv -> Markdown checklist")
    p.add_argument("-i", "--input", default=str(DEFAULT_INPUT))
    p.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--reset", action="store_true", help="忽略已有勾选，全部重置为未勾选")
    args = p.parse_args()

    in_path, out_path = Path(args.input), Path(args.output)
    if not in_path.exists():
        print(f"[错误] 输入不存在：{in_path}", file=sys.stderr)
        return 1

    rows = load_rows(in_path)
    checked = set() if args.reset else load_checked(out_path)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(rows, checked), encoding="utf-8")

    # 统计时只算当前 CSV 里存在的名称
    names = {r["名称"] for r in rows}
    kept = len(checked & names)
    print(f"[完成] 写入 {out_path}，共 {len(rows)} 项，保留勾选 {kept} 项")
    return 0


if __name__ == "__main__":
    sys.exit(main())
