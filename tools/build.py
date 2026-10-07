"""一键构建：解析 raw -> 校验 -> 生成 CSV + 多语言清单。

用法：
    python tools/build.py                      # 全量构建（中文 + 所有已有翻译的语言）
    python tools/build.py --langs zh-CN,en,ja  # 只构建指定语言
    python tools/build.py --no-validate        # 跳过数据校验
    python tools/build.py --reset              # 重置勾选状态
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = Path(__file__).resolve().parent
RAW_FILE = TOOLS_DIR / "raw_new.txt"
CSV_FILE = BASE_DIR / "data" / "yumemusic.csv"

sys.path.insert(0, str(TOOLS_DIR))
from regions import LANGUAGES  # noqa: E402
from i18n import list_languages  # noqa: E402


def run(cmd: list[str]) -> int:
    print(f"\n>>> {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=str(BASE_DIR))


def main() -> int:
    p = argparse.ArgumentParser(description="一键构建 CSV + 多语言清单")
    p.add_argument("--langs", default=None,
                   help="逗号分隔的语言代码，默认构建中文 + 所有已有翻译文件的语言")
    p.add_argument("--no-validate", action="store_true", help="跳过数据校验")
    p.add_argument("--reset", action="store_true", help="重置勾选状态")
    args = p.parse_args()

    if not RAW_FILE.exists():
        print(f"[错误] 找不到源数据：{RAW_FILE}", file=sys.stderr)
        return 1

    # 1. 解析 + 校验 + 生成 CSV
    parse_cmd = [
        sys.executable, str(TOOLS_DIR / "parse_yumemusic.py"),
        str(RAW_FILE), "-o", str(CSV_FILE), "--overwrite",
    ]
    if not args.no_validate:
        parse_cmd.append("--validate")
    rc = run(parse_cmd)
    if rc != 0:
        print("[错误] 解析 CSV 失败", file=sys.stderr)
        return rc

    # 2. 确定要构建的语言
    if args.langs:
        lang_codes = [c.strip() for c in args.langs.split(",") if c.strip()]
    else:
        # 默认：中文 + 所有已有翻译文件的语言
        existing = set(list_languages())
        lang_codes = ["zh-CN"] + [c for c, _ in LANGUAGES if c != "zh-CN" and c in existing]

    if not lang_codes:
        lang_codes = ["zh-CN"]

    # 3. 生成各语言清单
    for code in lang_codes:
        checklist_cmd = [
            sys.executable, str(TOOLS_DIR / "csv_to_checklist.py"),
            "--lang", code,
        ]
        if args.reset:
            checklist_cmd.append("--reset")
        rc = run(checklist_cmd)
        if rc != 0:
            print(f"[警告] 生成 {code} 清单失败", file=sys.stderr)

    print(f"\n[构建完成] 共生成 {len(lang_codes)} 个语言版本：{', '.join(lang_codes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
