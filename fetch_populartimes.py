"""
Downtown Mall Popular Times 数据爬取脚本
========================================
使用方法:
  1. pip install git+https://github.com/m-wrzr/populartimes.git
  2. python fetch_populartimes.py

输出:
  - populartimes_data.json  (完整原始数据)
  - populartimes_summary.csv (7x24 热度矩阵，方便分析)
"""

import populartimes
import json
import csv
import time
import os
from dotenv import load_dotenv

load_dotenv()  # 加载 .env 文件中的变量
API_KEY = os.getenv("GOOGLE_API_KEY")


PLACES = {
    "The Paramount Theater":              "ChIJ-3GDKCSGs4kRNNtfmVvjw_I",
    "Downtown Mall":                      "ChIJ____7yaGs4kR1BhvIOFlBlY",
    "Ting Pavilion":                      "ChIJvcWRGyeGs4kRlAVVn6a4V1o",
    "The Whiskey Jar":                    "ChIJRxkLrSWGs4kRUySqS8deLBg",
    "McGuffey Art Center":                "ChIJA3xKwCWGs4kR3K3Ox66eWzs",
    "Citizen Burger Bar":                 "ChIJ_VpDnCaGs4kRGdjWndt1uIA",
    "The Jefferson Theater":              "ChIJZUuDKySGs4kR5DJF7Yt4wtM",
    "The Southern Café and Music Hall":   "ChIJsX4SMSSGs4kRVmtAg0ahe2A",
    "The Inn at Court Square":            "ChIJva7FTSaGs4kRP8lZBXgVDVI",
    "Chaps Ice Cream":                    "ChIJX7tYiCaGs4kRsW1_HVeOKTI",
    "Miller's Downtown":                  "ChIJ13muzCWGs4kRsN2z4eq3h58",
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def fetch_all():
    results = {}
    for name, pid in PLACES.items():
        print(f"📍 Fetching: {name} ...", end=" ")
        try:
            data = populartimes.get_id(API_KEY, pid)
            has_data = data.get("populartimes") is not None
            results[name] = {
                "place_id": pid,
                "address": data.get("address", ""),
                "populartimes": data.get("populartimes", None),
                "current_popularity": data.get("current_popularity", None),
                "time_spent": data.get("time_spent", None),
            }
            print("✅" if has_data else "⚠️  No populartimes data")
        except Exception as e:
            print(f"❌ Error: {e}")
            results[name] = {"place_id": pid, "error": str(e)}
        time.sleep(1)

    return results


def save_json(results, filename="populartimes_data.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 JSON saved to: {filename}")


def save_csv(results, filename="populartimes_summary.csv"):
    """
    输出格式:
    Place, Day, 0, 1, 2, ..., 23
    Citizen Burger Bar, Monday, 0, 0, 0, ..., 12
    """
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["Place", "Day"] + [f"{h}:00" for h in range(24)]
        writer.writerow(header)

        for name, data in results.items():
            pt = data.get("populartimes")
            if not pt:
                continue
            for day in pt:
                row = [name, day["name"]] + day["data"]
                writer.writerow(row)

    print(f"📊 CSV saved to: {filename}")


def print_summary(results):
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, data in results.items():
        pt = data.get("populartimes")
        if not pt:
            print(f"  {name}: No data available")
            continue

        # 找到全周最热的时段
        max_val, max_day, max_hour = 0, "", 0
        for day in pt:
            for h, val in enumerate(day["data"]):
                if val > max_val:
                    max_val, max_day, max_hour = val, day["name"], h

        current = data.get("current_popularity")
        time_spent = data.get("time_spent")

        print(f"\n  📍 {name}")
        print(f"     Peak: {max_day} {max_hour}:00 (popularity {max_val}/100)")
        if current is not None:
            print(f"     Current: {current}/100")
        if time_spent:
            print(f"     Avg visit: {time_spent[0]}-{time_spent[1]} min")


if __name__ == "__main__":
    print("🔍 Fetching Popular Times for Downtown Mall locations...\n")
    results = fetch_all()
    save_json(results)
    save_csv(results)
    print_summary(results)
    print("\n✅ All done!")