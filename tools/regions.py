"""地区、编号区间、特殊项等共享常量。

被 parse_yumemusic.py 和 csv_to_checklist.py 共同引用，
避免两处维护同一份区间表导致不一致。
"""

# 地区显示顺序
REGION_ORDER = [
    "千星奇域", "蒙德", "璃月", "稻妻", "须弥",
    "枫丹", "纳塔", "挪德卡莱", "至冬", "其他", "无分组",
]

# 编号区间 -> 地区，按顺序检查，第一个命中的算
NUMBER_REGIONS: list[tuple[str, list[tuple[int, int]]]] = [
    ("蒙德", [(1, 23), (177, 178)]),
    ("璃月", [(24, 46), (120, 125)]),
    ("稻妻", [(47, 72)]),
    ("须弥", [(73, 98)]),
    ("枫丹", [(99, 130)]),
    ("纳塔", [(131, 156)]),
    ("挪德卡莱", [(157, 176)]),
    ("至冬", [(189, 200)]),
    ("其他", [(179, 188)]),
]

# 特殊项关键词 -> 地区，顺序重要：先匹配关键词，剩下的才按编号
KEYWORD_REGIONS: list[tuple[str, list[str]]] = [
    ("千星奇域", ["奇域旋律"]),
    ("蒙德", ["青空", "风所爱之城", "旅途的开始"]),
    ("璃月", ["杯中明月", "环佩凭栏望千帆", "璃月", "回家的路"]),
    ("须弥", ["风的来信"]),
]

# 特殊项在地区内的显示顺序
SPECIAL_ORDER: dict[str, list[str]] = {
    "千星奇域": [
        "旋曜玉帛·奇域旋律·童话剧场",
        "旋曜玉帛·奇域旋律·晴空乐园",
        "旋曜玉帛·奇域旋律·烛影夜游",
    ],
    "蒙德": [
        "旋曜玉帛·青空",
        "旋曜玉帛·风所爱之城",
        "旋曜玉帛·旅途的开始",
    ],
    "璃月": [
        "旋曜玉帛·杯中明月",
        "旋曜玉帛·环佩凭栏望千帆",
        "旋曜玉帛·璃月",
        "旋曜玉帛·回家的路·其一",
        "旋曜玉帛·回家的路·其二",
    ],
    "须弥": [
        "旋曜玉帛·风的来信·其二",
        "旋曜玉帛·风的来信·其三",
        "旋曜玉帛·风的来信·其四",
        "旋曜玉帛·风的来信·其一",
    ],
}

# 支持的语言列表：(代码, 显示名)
LANGUAGES: list[tuple[str, str]] = [
    ("zh-CN", "简体中文"),
    ("zh-TW", "繁體中文"),
    ("en", "English"),
    ("ko", "한국어"),
    ("ja", "日本語"),
    ("es", "Español"),
    ("fr", "Français"),
    ("ru", "Русский язык"),
    ("th", "ภาษาไทย"),
    ("vi", "Tiếng Việt"),
    ("de", "Deutsch"),
    ("id", "Bahasa Indonesia"),
    ("pt", "Português"),
    ("tr", "Türkçe"),
    ("it", "Italiano"),
]

CN_NUM = {
    "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}


def cn_to_int(s: str) -> int:
    """中文数字字符串转整数。无法解析返回 -1。"""
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


def classify_region(name: str) -> tuple[str, int]:
    """返回 (地区, 排序数字)。数字 -1 表示特殊项，-2 表示非编号普通项。"""
    import re
    numbered = re.compile(r"^旋曜玉帛·其([零一二三四五六七八九十百\d]+)(?:\(.*?\))?$")

    for region, keywords in KEYWORD_REGIONS:
        for kw in keywords:
            if kw in name:
                return (region, -1)

    m = numbered.match(name)
    if m:
        n = cn_to_int(m.group(1))
        for region, ranges in NUMBER_REGIONS:
            for lo, hi in ranges:
                if lo <= n <= hi:
                    return (region, n)
        return ("无分组", n)

    return ("无分组", -2)
