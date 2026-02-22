"""
Downtown Mall Popular Times 数据获取（v3 - 已验证地点）
======================================================
这些地点已在 Google Maps 上确认有 Popular Times 显示。

安装:
  pip3 install --upgrade git+https://github.com/GrocerCheck/LivePopularTimes

运行:
  python3 fetch_populartimes.py
"""

import json
import time
import csv
import sys
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的变量
API_KEY = os.getenv("GOOGLE_API_KEY") # 从系统环境读取

try:
    import livepopulartimes
except ImportError:
    print("❌ 请先安装 LivePopularTimes:")
    print("   pip3 install --upgrade git+https://github.com/GrocerCheck/LivePopularTimes")
    sys.exit(1)

PLACES = [
    {"name": "IX Art Park", "place_id": "ChIJ394bSiKGs4kR9B-gnGQa9-Y", "address": "522 2nd St SE D, Charlottesville, VA 22902"},
    {"name": "Downtown Mall", "place_id": "ChIJ____7yaGs4kR1BhvIOFlBlY", "address": "Downtown Mall, Charlottesville, VA 22902"},
    {"name": "Charlottesville Area Transit", "place_id": "ChIJ68f3IieGs4kRg0JGj_QrgYg", "address": "615 E Water St, Charlottesville, VA 22902"},
    {"name": "Virginia Discovery Museum", "place_id": "ChIJX5VyHieGs4kRBBUAQ7bM7EE", "address": "524 E Main St, Charlottesville, VA 22902"},
    {"name": "Melting Pot", "place_id": "ChIJB4bTwiaGs4kR9ZCpAqsx6Sw", "address": "501 E Water St, Charlottesville, VA 22902"},
    {"name": "York Place", "place_id": "ChIJl8IlOCSGs4kR0SL8hULRO6U", "address": "W Water St, Charlottesville, VA 22902"},
    {"name": "Chaps Ice Cream", "place_id": "ChIJX7tYiCaGs4kRsW1_HVeOKTI", "address": "321 E Main St, Charlottesville, VA 22902"},
    {"name": "Zocalo", "place_id": "ChIJ-0xlhyaGs4kRnhWkdSwEm1w", "address": "201 E Main St Unit E, Charlottesville, VA 22902"},
    {"name": "Charlottesville City Hall", "place_id": "ChIJEaKGDieGs4kRvEt9T7NkD2M", "address": "605 E Main St, Charlottesville, VA 22902"},
    {"name": "SHENANIGANS Toy Store", "place_id": "ChIJW77uHTuGs4kRl_-7i-ctmi8", "address": "601 W Main St, Charlottesville, VA 22903"},
    {"name": "DOMA Korean Kitchen", "place_id": "ChIJUf9ZqzuGs4kR6Av3vRQgHBA", "address": "701 W Main St, Charlottesville, VA 22903"},
    {"name": "Lewis and Clark Memorial Marker", "place_id": "ChIJZb-ObACHs4kRqXHuz8Xg_Kg", "address": "W Main St, Charlottesville, VA 22902"},
    {"name": "Camellias Bar & Roastery", "place_id": "ChIJZR0fwhqHs4kRzrBDF4u8uvA", "address": "400 Preston Ave #150, Charlottesville, VA 22903"},
    {"name": "The Whiskey Jar", "place_id": "ChIJRxkLrSWGs4kRUySqS8deLBg", "address": "227 W Main St, Charlottesville, VA 22902"},
    {"name": "Citizen Burger Bar", "place_id": "ChIJ_VpDnCaGs4kRGdjWndt1uIA", "address": "212 E Main St, Charlottesville, VA 22902"},
    {"name": "Market Street Park", "place_id": "ChIJa5EkdCaGs4kRwpJO_gE35zQ", "address": "101 E Market St, Charlottesville, VA 22902"},
    {"name": "Miller's Downtown", "place_id": "ChIJ13muzCWGs4kRsN2z4eq3h58", "address": "109 W Main St, Charlottesville, VA 22902"},
]

results = {}
success_count = 0

print("🔍 Fetching Popular Times for Downtown Mall locations...")
print("=" * 60)

for i, place in enumerate(PLACES):
    name = place["name"]
    print(f"\n[{i+1}/{len(PLACES)}] 📍 {name}")

    # 方法 1: Place ID
    got_data = False
    try:
        data = livepopulartimes.get_populartimes_by_PlaceID(API_KEY, place["place_id"])
        if data.get("populartimes"):
            results[name] = data
            got_data = True
            success_count += 1
            max_val, max_day, max_hour = 0, "", 0
            for day in data["populartimes"]:
                for h, val in enumerate(day.get("data", [])):
                    if val > max_val:
                        max_val, max_day, max_hour = val, day["name"], h
            print(f"   ✅ PlaceID method worked! Peak: {max_day} {max_hour}:00 ({max_val}/100)")
    except Exception as e:
        print(f"   ⚠️  PlaceID method failed: {str(e)[:80]}")

    if got_data:
        time.sleep(2)
        continue

    # 方法 2: Address
    try:
        data = livepopulartimes.get_populartimes_by_address(place["address"])
        if data.get("populartimes"):
            results[name] = data
            got_data = True
            success_count += 1
            max_val, max_day, max_hour = 0, "", 0
            for day in data["populartimes"]:
                for h, val in enumerate(day.get("data", [])):
                    if val > max_val:
                        max_val, max_day, max_hour = val, day["name"], h
            print(f"   ✅ Address method worked! Peak: {max_day} {max_hour}:00 ({max_val}/100)")
        else:
            print(f"   ❌ No popular times returned")
            results[name] = {"status": "no_data", "raw": data}
    except Exception as e:
        print(f"   ❌ Address method failed: {str(e)[:80]}")
        results[name] = {"status": "error", "error": str(e)}

    time.sleep(3)

# ============================================================
# 保存结果
# ============================================================
print("\n" + "=" * 60)
print(f"📊 Results: {success_count}/{len(PLACES)} places returned data\n")

# 1. JSON
with open("populartimes_data.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("💾 populartimes_data.json")

# 2. CSV 矩阵
with open("populartimes_matrix.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["place", "day"] + [f"{h}:00" for h in range(24)])
    for name, data in results.items():
        pt = data.get("populartimes")
        if not pt:
            continue
        for day in pt:
            writer.writerow([name, day["name"]] + day.get("data", [0]*24))
print("💾 populartimes_matrix.csv")

# 3. 打印成功地点的摘要
print("\n" + "=" * 60)
print("📋 SUMMARY")
print("=" * 60)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
BAR_WIDTH = 30

for name, data in results.items():
    pt = data.get("populartimes")
    if not pt:
        print(f"\n  ❌ {name}: No data")
        continue

    print(f"\n  📍 {name}")
    current = data.get("current_popularity")
    if current:
        print(f"     🔴 Live now: {current}/100")
    time_spent = data.get("time_spent")
    if time_spent:
        print(f"     ⏱️  Avg visit: {time_spent[0]}-{time_spent[1]} min")

    # 每天的峰值
    for day in pt:
        day_data = day.get("data", [])
        if not day_data or max(day_data) == 0:
            print(f"     {day['name']:9s} │ (closed)")
            continue
        peak_hour = day_data.index(max(day_data))
        peak_val = max(day_data)
        bar_len = int(peak_val / 100 * BAR_WIDTH)
        bar = "█" * bar_len + "░" * (BAR_WIDTH - bar_len)
        print(f"     {day['name']:9s} │ {bar} peak {peak_val} @ {peak_hour}:00")

print(f"\n✅ Done! Check populartimes_data.json and populartimes_matrix.csv")