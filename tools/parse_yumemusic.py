"""旋曜玉帛文本 -> CSV，支持合并、更新、覆盖。

用法：
    # 合并：保留已有行，只追加新行
    python tools/parse_yumemusic.py raw.txt -o data/yumemusic.csv

    # 更新：同编号的行用新内容覆盖（编号项按编号匹配，其他按名称）
    python tools/parse_yumemusic.py raw.txt -o data/yumemusic.csv --update

    # 覆盖：整体重写
    python tools/parse_yumemusic.py raw.txt -o data/yumemusic.csv --overwrite

    # 预览，不写文件
    python tools/parse_yumemusic.py raw.txt -o data/yumemusic.csv --update --dry-run

    # stdout
    python tools/parse_yumemusic.py raw.txt
"""

import argparse
import csv
import io
import re
import sys
from pathlib import Path

# 确保能导入同目录的共享模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

from regions import classify_region, NUMBER_REGIONS  # noqa: E402

HEADER = ["图标", "名称", "稀有度", "类型", "来源", "用途"]
COL_COUNT = len(HEADER)
REQUIRED_FIELDS = ["名称", "稀有度", "类型", "来源"]

# 编号项 key：旋曜玉帛·其N 或 旋曜玉帛·其N(别名)，别名用英文括号
NUMBERED_KEY = re.compile(
    r"^旋曜玉帛·其([零一二三四五六七八九十百\d]+)(?:\(.*?\))?$"
)
NUMBERED_EXTRACT = re.compile(r"^旋曜玉帛·其([零一二三四五六七八九十百\d]+)")


def merge_key(name: str) -> str:
    """编号项用编号做 key，其他用名称。"""
    m = NUMBERED_KEY.match(name)
    return f"num:{m.group(1)}" if m else f"name:{name}"


def _extract_num(name: str) -> int | None:
    """从名称提取编号数字，非编号项返回 None。"""
    m = NUMBERED_EXTRACT.match(name)
    if not m:
        return None
    # 复用 regions 的 cn_to_int
    from regions import cn_to_int
    n = cn_to_int(m.group(1))
    return n if n >= 0 else None


def detect_delimiter(sample: str) -> str:
    first = sample.splitlines()[0] if sample else ""
    return "\t" if first.count("\t") > first.count(",") else ","


def _repair_row(parts: list[str]) -> list[str]:
    """字段数超过预期时，合并名称字段中被逗号拆分的片段。

    约定：只有第 2 列（名称）可能含逗号（在括号别名内），
    稀有度 / 类型 / 来源 / 用途 均不含逗号。
    """
    if len(parts) <= COL_COUNT:
        return parts
    # 末尾 4 列固定为 稀有度, 类型, 来源, 用途
    tail = parts[-(COL_COUNT - 2):]
    head = parts[: len(parts) - (COL_COUNT - 2)]
    icon = head[0]
    name = ",".join(head[1:])
    return [icon, name] + tail


def parse(stream, delimiter: str) -> list[list[str]]:
    reader = csv.reader(stream, delimiter=delimiter)
    rows: list[list[str]] = []
    for parts in reader:
        if not parts or not any(p.strip() for p in parts):
            continue
        parts = [p.strip() for p in parts]
        if parts == HEADER:
            continue
        parts = _repair_row(parts)
        if len(parts) < COL_COUNT:
            parts += [""] * (COL_COUNT - len(parts))
        parts = parts[:COL_COUNT]
        if not parts[1]:
            continue
        rows.append(parts)
    return rows


def load_existing(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    """读取现有 CSV，返回 (key顺序, key->行)。表头不匹配则当空处理。"""
    if not path.exists():
        return [], {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != HEADER:
            print(f"[警告] {path} 表头不匹配，按空文件处理", file=sys.stderr)
            return [], {}
        order, by_key = [], {}
        for parts in reader:
            if not parts or not any(p.strip() for p in parts):
                continue
            parts = [p.strip() for p in parts]
            if len(parts) < COL_COUNT:
                parts += [""] * (COL_COUNT - len(parts))
            parts = parts[:COL_COUNT]
            name = parts[1]
            if not name:
                continue
            key = merge_key(name)
            if key not in by_key:
                order.append(key)
            by_key[key] = parts
    return order, by_key


def merge(
    existing_order: list[str],
    existing_by_key: dict[str, list[str]],
    new_rows: list[list[str]],
    update: bool = False,
) -> tuple[list[list[str]], list[str], list[str]]:
    """合并。返回 (所有行, 新增名称列表, 更新名称列表)。"""
    order = list(existing_order)
    by_key = dict(existing_by_key)
    added: list[str] = []
    updated: list[str] = []
    for row in new_rows:
        key = merge_key(row[1])
        if key in by_key:
            if update:
                by_key[key] = row
                updated.append(row[1])
            continue
        by_key[key] = row
        order.append(key)
        added.append(row[1])
    return [by_key[k] for k in order], added, updated


def write_csv(rows: list[list[str]], out) -> None:
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(rows)


def validate(rows: list[list[str]]) -> list[str]:
    """校验数据，返回问题列表（空列表表示无问题）。"""
    issues: list[str] = []

    # 1. 必填字段为空
    for r in rows:
        for field_idx, field_name in enumerate(HEADER):
            if field_name in REQUIRED_FIELDS and not r[field_idx].strip():
                issues.append(f"[空字段] {r[1] or '(空名)'} 的「{field_name}」为空")

    # 2. 编号重复
    seen_nums: dict[int, list[str]] = {}
    for r in rows:
        n = _extract_num(r[1])
        if n is not None:
            seen_nums.setdefault(n, []).append(r[1])
    for n, names in seen_nums.items():
        if len(names) > 1:
            issues.append(f"[重号] 编号 {n} 出现 {len(names)} 次：{', '.join(names)}")

    # 3. 编号区间缺号
    all_nums = set(seen_nums.keys())
    for region, ranges in NUMBER_REGIONS:
        for lo, hi in ranges:
            missing = [n for n in range(lo, hi + 1) if n not in all_nums]
            if missing:
                issues.append(
                    f"[缺号] {region} 区间 {lo}-{hi} 缺少：{missing}"
                )

    # 4. 孤立项（无法归入任何地区）
    for r in rows:
        region, _ = classify_region(r[1])
        if region == "无分组":
            issues.append(f"[孤立项] {r[1]} 无法归入任何地区")

    return issues


def main() -> int:
    p = argparse.ArgumentParser(description="旋曜玉帛文本 -> CSV")
    p.add_argument("input", help="输入文件路径，或 '-' 表示 stdin")
    p.add_argument("-o", "--output", default="-", help="输出路径，默认 stdout")
    p.add_argument("--update", action="store_true",
                   help="同 key 的行用新内容覆盖")
    p.add_argument("--overwrite", action="store_true",
                   help="不合并，直接覆盖")
    p.add_argument("--dry-run", action="store_true",
                   help="只显示新增/更新，不写文件")
    p.add_argument("--validate", action="store_true",
                   help="写入前运行数据校验（空字段/重号/缺号/孤立项）")
    args = p.parse_args()

    if args.input == "-":
        sample = sys.stdin.read()
    else:
        sample = Path(args.input).read_text(encoding="utf-8-sig")
    delimiter = detect_delimiter(sample)
    new_rows = parse(io.StringIO(sample), delimiter)

    if not new_rows:
        print("[警告] 没有解析到有效行", file=sys.stderr)
        return 1

    if args.validate:
        issues = validate(new_rows)
        if issues:
            print(f"[校验] 发现 {len(issues)} 个问题：", file=sys.stderr)
            for issue in issues:
                print(f"  {issue}", file=sys.stderr)
        else:
            print("[校验] 数据正常，未发现问题", file=sys.stderr)

    if args.output == "-":
        write_csv(new_rows, sys.stdout)
        return 0

    out_path = Path(args.output)

    if args.overwrite:
        merged = new_rows
        added = [r[1] for r in new_rows]
        updated: list[str] = []
        kept = 0
    else:
        order, by_key = load_existing(out_path)
        merged, added, updated = merge(order, by_key, new_rows, update=args.update)
        kept = len(merged) - len(added)

    if args.dry_run:
        for name in added:
            print(f"[新增] {name}")
        for name in updated:
            print(f"[更新] {name}")
        print(f"[预览] 新增 {len(added)} 条，更新 {len(updated)} 条，"
              f"保留 {kept} 条，合并后共 {len(merged)} 条")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        write_csv(merged, f)
    print(f"[完成] 写入 {out_path}：新增 {len(added)} 条，"
          f"更新 {len(updated)} 条，保留 {kept} 条，共 {len(merged)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
