"""从 data/yumemusic.csv 生成可勾选的 Markdown 清单。

规则：
- 编号项：旋曜玉帛·其N 或 旋曜玉帛·其N(别名)，按 N 数字升序
- 特殊项：命中 KEYWORD_REGIONS 的系列曲，以及不含其N的曲目，按 SPECIAL_ORDER
- 顶部生成目录，可点击跳转
- 保留已有勾选状态（按归一化名称匹配，跨重命名/跨语言保留）
- 支持 --lang 生成多语言版本（翻译文本由 langs/{code}.json 提供）

用法：
    python tools/csv_to_checklist.py
    python tools/csv_to_checklist.py --reset
    python tools/csv_to_checklist.py --lang en
    python tools/csv_to_checklist.py --lang en -o data/yumemusic_en.md
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# 确保能导入同目录的共享模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from regions import (  # noqa: E402
    REGION_ORDER,
    SPECIAL_ORDER,
    classify_region,
)
from i18n import Translator  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = BASE_DIR / "data" / "yumemusic.csv"
DEFAULT_OUTPUT = BASE_DIR / "data" / "yumemusic.md"

GAME_VERSION = "V7.1"

CHECKBOX_PATTERN = re.compile(r"^- \[([ xX])\]\s+(.+?)(?:\s+<!--.*?-->)?\s*$")

# 名称尾部括号别名，如 "旋曜玉帛·其一(晨曦酒庄)" -> "旋曜玉帛·其一"
ALIAS_SUFFIX = re.compile(r"\(.*?\)\s*$")


def normalize_name(name: str) -> str:
    """归一化名称用于跨重命名/跨语言匹配勾选状态：
    - 去掉尾部括号别名
    - 去掉书名号《》
    """
    name = ALIAS_SUFFIX.sub("", name).strip()
    name = name.replace("《", "").replace("》", "")
    return name


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_checked(path: Path) -> set[str]:
    if not path.exists():
        return set()
    checked: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = CHECKBOX_PATTERN.match(line.strip())
        if not m:
            continue
        if m.group(1).lower() == "x":
            checked.add(normalize_name(m.group(2).strip()))
    return checked


def load_previous_order(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    order: dict[str, int] = {}
    idx = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        m = CHECKBOX_PATTERN.match(line.strip())
        if not m:
            continue
        name = normalize_name(m.group(2).strip())
        if name not in order:
            order[name] = idx
            idx += 1
    return order


def special_key(region: str, name: str, csv_idx: int, prev_order: dict[str, int]):
    """特殊项排序：SPECIAL_ORDER > 旧 MD 位置 > CSV 顺序。"""
    so = SPECIAL_ORDER.get(region, [])
    so_idx = {n: i for i, n in enumerate(so)}
    # prev_order 的 key 已归一化，匹配时也归一化
    so_idx_norm = {normalize_name(n): i for n, i in so_idx.items()}
    name_norm = normalize_name(name)

    if name in so_idx:
        return (so_idx[name], 0, 0)

    if name_norm in prev_order:
        pos = prev_order[name_norm]
        anchor = -1
        for other, other_pos in prev_order.items():
            if other_pos < pos and other in so_idx_norm and so_idx_norm[other] > anchor:
                anchor = so_idx_norm[other]
        return (anchor, 1, pos)

    return (len(so), 2, csv_idx)


def format_item(row: dict, checked: bool, tr: Translator) -> str:
    name = tr.name(row["名称"])
    source = row["来源"] or ""
    mark = "x" if checked else " "
    suffix = f"  <!-- {source} -->" if source else ""
    return f"- [{mark}] {name}{suffix}"


def render(
    rows: list[dict],
    checked: set[str],
    prev_order: dict[str, int],
    tr: Translator,
) -> str:
    groups: dict[str, list[tuple[int, str, dict, int]]] = {r: [] for r in REGION_ORDER}
    for idx, row in enumerate(rows):
        name = row["名称"]
        region, num = classify_region(name)
        groups.setdefault(region, []).append((num, name, row, idx))

    for region, items in groups.items():
        def key(item):
            num, name, _, csv_idx = item
            if num < 0:
                a, b, c = special_key(region, name, csv_idx, prev_order)
                return (0, a, b, c)
            return (1, 0, 0, num)
        items.sort(key=key)

    active_regions = [r for r in REGION_ORDER if groups.get(r)]

    title = tr.ui("旋曜玉帛 收集清单")
    version_label = tr.ui("当前版本")
    total_label = tr.ui("共")
    item_label = tr.ui("项")
    toc_label = tr.ui("目录")

    lines = [
        f"# {title}",
        "",
        f"{version_label}：{GAME_VERSION}",
        "",
        f"{total_label} {len(rows)} {item_label}。",
        "",
    ]

    if active_regions:
        lines.append(f"## {toc_label}")
        lines.append("")
        for region in active_regions:
            r_label = tr.region(region)
            lines.append(f"- [{r_label}](#{region})（{len(groups[region])}）")
        lines.append("")
        lines.append("---")
        lines.append("")

    for i, region in enumerate(active_regions):
        if i > 0:
            lines.append("---")
            lines.append("")
        lines.append(f"## {tr.region(region)}")
        lines.append("")
        for _, _, row, _ in groups[region]:
            is_checked = normalize_name(row["名称"]) in checked
            lines.append(format_item(row, is_checked, tr))
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="yumemusic.csv -> Markdown checklist")
    p.add_argument("-i", "--input", default=str(DEFAULT_INPUT))
    p.add_argument("-o", "--output", default=None,
                   help="输出路径，默认 data/yumemusic.md；指定 --lang 时默认 data/yumemusic_{lang}.md")
    p.add_argument("--lang", default="zh-CN", help="输出语言代码（如 en、ja），默认 zh-CN")
    p.add_argument("--reset", action="store_true", help="忽略已有勾选，全部重置为未勾选")
    args = p.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"[错误] 输入不存在：{in_path}", file=sys.stderr)
        return 1

    # 输出路径：指定了就用指定的；否则按语言生成默认名
    if args.output:
        out_path = Path(args.output)
    else:
        if args.lang == "zh-CN":
            out_path = DEFAULT_OUTPUT
        else:
            out_path = BASE_DIR / "data" / f"yumemusic_{args.lang}.md"

    rows = load_rows(in_path)
    tr = Translator(args.lang)

    # 勾选状态始终从中文版 md 读取，保证跨语言一致
    checked_source = DEFAULT_OUTPUT
    checked = set() if args.reset else load_checked(checked_source)
    prev_order = {} if args.reset else load_previous_order(checked_source)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(rows, checked, prev_order, tr), encoding="utf-8")

    names = {normalize_name(r["名称"]) for r in rows}
    kept = len(checked & names)
    print(f"[完成] 写入 {out_path}，共 {len(rows)} 项，保留勾选 {kept} 项（语言：{args.lang}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
