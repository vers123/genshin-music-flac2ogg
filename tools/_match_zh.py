"""匹配中文缩写列表到 CSV 全名，输出有序的 CSV 键列表。"""
import csv
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CSV_PATH = BASE / "data" / "yumemusic.csv"
ORDER_PATH = Path(__file__).parent / "_zh_order.txt"

with CSV_PATH.open(encoding="utf-8-sig") as f:
    csv_names = [r["名称"] for r in csv.DictReader(f)]

zh_order = [l.strip() for l in ORDER_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]

# 构建别名 -> 全名 映射
alias_to_full = {}
special_to_full = {}
for name in csv_names:
    # 去掉尾部空括号
    clean = re.sub(r"\(\)$", "", name)
    # 编号项别名
    m = re.match(r"^旋曜玉帛·其[^(（]*(?:\((.*)\))?$", clean)
    if m and m.group(1):
        alias_to_full[m.group(1)] = name
    # 特殊项
    if name.startswith("旋曜玉帛·"):
        special_to_full[re.sub(r"\(\)$", "", name)[len("旋曜玉帛·"):]] = name

# 手动覆盖（OCR 与 CSV 的字符差异）
MANUAL_OVERRIDES = {
    "清波微荡": "旋曜玉帛·其三十(轻波微荡)",
    "多情东逝": "旋曜玉帛·其三十三(多情东浙)",
    "远离尘嚣": "旋曜玉帛·其六十二(远离尘器)",
}

result = []
unmatched = []
for zh in zh_order:
    if zh in MANUAL_OVERRIDES:
        result.append(MANUAL_OVERRIDES[zh])
    elif zh.startswith("旋曜玉帛·"):
        clean = re.sub(r"\(\)$", "", zh)
        if clean in csv_names or clean + "()" in csv_names:
            result.append(clean + "()" if clean + "()" in csv_names else clean)
        else:
            unmatched.append(zh)
    elif zh in special_to_full:
        result.append(special_to_full[zh])
    elif zh in alias_to_full:
        result.append(alias_to_full[zh])
    else:
        unmatched.append(zh)

print(f"匹配成功: {len(result)} / {len(zh_order)}")
if unmatched:
    print(f"未匹配 ({len(unmatched)}):")
    for u in unmatched:
        print(f"  - {u}")

out = Path(__file__).parent / "_zh_keys.txt"
out.write_text("\n".join(result), encoding="utf-8")
print(f"\n已写入 {out}")
