"""
Charlottesville Building Permits - Downtown Mall 数据清洗
========================================================
用法: python3 clean_permits.py building_permits_all.csv
"""

import csv
import sys
from collections import Counter
from datetime import datetime

if len(sys.argv) < 2:
    print("用法: python3 clean_permits.py building_permits_all.csv")
    sys.exit(1)

filepath = sys.argv[1]

# 读取数据
with open(filepath, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    records = list(reader)

print(f"📂 Total records: {len(records)}")

# ============================================================
# 过滤 Downtown Mall 区域
# Downtown Mall = E Main St 大约 100-700 block
# 附近相关街道: E Water St, Market St, Old Preston Ave
# ============================================================
DOWNTOWN_KEYWORDS = [
    "E MAIN", "EAST MAIN",
    "W MAIN", "WEST MAIN",
    "E WATER", "EAST WATER",
    "MARKET ST",
    "DOWNTOWN",
    "2ND ST",  # 贯穿 Mall 的交叉街
    "3RD ST",
    "4TH ST",
    "5TH ST",
    "OLD PRESTON",
]

downtown = []
for rec in records:
    addr = rec.get("PropertyAddress", "").upper()
    if any(kw in addr for kw in DOWNTOWN_KEYWORDS):
        downtown.append(rec)

print(f"🏬 Downtown Mall area: {len(downtown)} records")

# ============================================================
# 按年统计
# ============================================================
def get_year(rec):
    """从 AppliedDate 或 IssuedDate 提取年份"""
    for field in ["IssuedDate", "AppliedDate"]:
        val = rec.get(field, "")
        if val and val.strip():
            try:
                return int(val[:4])
            except:
                pass
    return None

# 全市按年
year_all = Counter()
for rec in records:
    y = get_year(rec)
    if y:
        year_all[y] += 1

# Downtown 按年
year_dt = Counter()
for rec in downtown:
    y = get_year(rec)
    if y:
        year_dt[y] += 1

# ============================================================
# 输出 CSV
# ============================================================

# 1. Downtown permits 完整数据
fieldnames = records[0].keys()
with open("permits_downtown_mall.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(downtown)
print(f"💾 Saved: permits_downtown_mall.csv")

# 2. 按年统计
years = sorted(set(list(year_all.keys()) + list(year_dt.keys())))
with open("permits_by_year.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["year", "all_city", "downtown_mall"])
    for y in years:
        writer.writerow([y, year_all.get(y, 0), year_dt.get(y, 0)])
print(f"💾 Saved: permits_by_year.csv")

# ============================================================
# 终端可视化
# ============================================================
max_val = max(year_all.values()) if year_all else 1
BAR_WIDTH = 50  # 最大柱宽

print(f"\n{'='*70}")
print(f"📊 全市 Building Permits (按年)")
print(f"{'='*70}")
for y in years:
    n = year_all.get(y, 0)
    bar_len = int(n / max_val * BAR_WIDTH)
    bar = "█" * bar_len
    print(f"  {y} │ {bar} {n}")

if year_dt:
    max_dt = max(year_dt.values())
    print(f"\n{'='*70}")
    print(f"📊 Downtown Mall 区域 Permits (按年)")
    print(f"{'='*70}")
    for y in years:
        n = year_dt.get(y, 0)
        bar_len = int(n / max_dt * BAR_WIDTH) if max_dt > 0 else 0
        bar = "█" * bar_len
        print(f"  {y} │ {bar} {n}")

# ============================================================
# Downtown Permit 类型分布
# ============================================================
if downtown:
    type_counts = Counter(rec.get("PermitType", "Unknown") for rec in downtown)
    print(f"\n{'='*70}")
    print(f"📊 Downtown Mall - Permit 类型分布")
    print(f"{'='*70}")
    for ptype, count in type_counts.most_common(10):
        print(f"  {ptype:30s} {count}")

    # 地址分布 Top 15
    addr_counts = Counter(rec.get("PropertyAddress", "Unknown") for rec in downtown)
    print(f"\n{'='*70}")
    print(f"📊 Downtown Mall - 热门地址 Top 15")
    print(f"{'='*70}")
    for addr, count in addr_counts.most_common(15):
        print(f"  {addr:40s} {count}")

print(f"\n✅ Done!")