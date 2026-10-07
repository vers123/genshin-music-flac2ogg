import argparse
import csv
import io
import sys
from pathlib import Path

HEADER = ["图标", "名称", "稀有度", "类型", "来源", "用途"]
COL_COUNT = len(HEADER)


def detect_delimiter(sample: str) -> str:
    """根据第一行样本判断分隔符：tab 或逗号。"""
    first = sample.splitlines()[0] if sample else ""
    return "\t" if first.count("\t") > first.count(",") else ","


def parse(stream, delimiter: str) -> list[list[str]]:
    reader = csv.reader(stream, delimiter=delimiter)
    rows: list[list[str]] = []
    for parts in reader:
        if not parts or not any(p.strip() for p in parts):
            continue
        parts = [p.strip() for p in parts]
        if parts == HEADER:
            continue
        if len(parts) < COL_COUNT:
            parts += [""] * (COL_COUNT - len(parts))
        parts = parts[:COL_COUNT]
        if not parts[1]:
            continue
        rows.append(parts)
    return rows


def load_existing(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    """读取现有 CSV，返回 (名称顺序, 名称->行)。表头不匹配则当空处理。"""
    if not path.exists():
        return [], {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != HEADER:
            print(f"[警告] {path} 表头不匹配，按空文件处理", file=sys.stderr)
            return [], {}
        order, by_name = [], {}
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
            if name not in by_name:
                order.append(name)
            by_name[name] = parts
    return order, by_name


def merge(
    existing_order: list[str],
    existing_by_name: dict[str, list[str]],
    new_rows: list[list[str]],
) -> tuple[list[list[str]], list[str]]:
    """合并。返回 (所有行, 新增名称列表)。"""
    order = list(existing_order)
    by_name = dict(existing_by_name)
    added: list[str] = []
    for row in new_rows:
        name = row[1]
        if name in by_name:
            continue
        by_name[name] = row
        order.append(name)
        added.append(name)
    return [by_name[n] for n in order], added


def write_csv(rows: list[list[str]], out) -> None:
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser(description="旋曜玉帛文本 -> CSV（支持合并）")
    p.add_argument("input", help="输入文件路径，或 '-' 表示 stdin")
    p.add_argument("-o", "--output", default="-", help="输出路径，默认 stdout")
    p.add_argument("--overwrite", action="store_true", help="不合并，直接覆盖")
    p.add_argument("--dry-run", action="store_true", help="只显示新增，不写文件")
    args = p.parse_args()

    # 读取原始文本
    if args.input == "-":
        sample = sys.stdin.read()
    else:
        sample = Path(args.input).read_text(encoding="utf-8-sig")
    delimiter = detect_delimiter(sample)
    new_rows = parse(io.StringIO(sample), delimiter)

    if not new_rows:
        print("[警告] 没有解析到有效行", file=sys.stderr)
        return 1

    # stdout 模式：直接输出新数据，不做合并
    if args.output == "-":
        write_csv(new_rows, sys.stdout)
        return 0

    out_path = Path(args.output)

    if args.overwrite:
        merged, added = new_rows, [r[1] for r in new_rows]
        kept = 0
    else:
        order, by_name = load_existing(out_path)
        merged, added = merge(order, by_name, new_rows)
        kept = len(merged) - len(added)

    if args.dry_run:
        for name in added:
            print(f"[新增] {name}")
        print(f"[预览] 新增 {len(added)} 条，保留 {kept} 条，合并后共 {len(merged)} 条")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        write_csv(merged, f)
    print(f"[完成] 写入 {out_path}：新增 {len(added)} 条，保留 {kept} 条，共 {len(merged)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
