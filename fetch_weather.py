"""
Charlottesville 2025 历史天气数据获取脚本
==========================================
使用 Open-Meteo Historical Weather API（免费，无需 API Key）

使用方法:
  python3 fetch_weather.py

输出:
  - charlottesville_weather_2025.csv
"""

import urllib.request
import json
import csv
import sys

# Charlottesville 经纬度
LAT = 38.0293
LON = -78.4767

# 构造 API URL
# 注意：Open-Meteo 的 archive API 数据有约 5 天延迟
# 2025 年数据如果还没完整到 12/31，会自动返回到可用日期
API_URL = (
    f"https://archive-api.open-meteo.com/v1/archive"
    f"?latitude={LAT}&longitude={LON}"
    f"&start_date=2015-01-01&end_date=2025-12-31"
    f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
    f"precipitation_sum,weather_code"
    f"&timezone=America/New_York"
    f"&temperature_unit=fahrenheit"
    f"&precipitation_unit=inch"
)

print(f"🌤️  Fetching Charlottesville 2025 weather data from Open-Meteo...")
print(f"   URL: {API_URL}\n")

try:
    req = urllib.request.Request(API_URL)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
except Exception as e:
    print(f"❌ Error fetching data: {e}")
    sys.exit(1)

# 检查是否有错误
if data.get("error"):
    print(f"❌ API Error: {data.get('reason', 'Unknown')}")
    sys.exit(1)

daily = data["daily"]
dates = daily["time"]
temp_max = daily["temperature_2m_max"]
temp_min = daily["temperature_2m_min"]
temp_mean = daily["temperature_2m_mean"]
precip = daily["precipitation_sum"]
weather_code = daily["weather_code"]

# WMO Weather Code 映射（简化版）
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm w/ slight hail", 99: "Thunderstorm w/ heavy hail",
}

# 保存 CSV
OUTPUT = "charlottesville_weather_2025.csv"
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "date", "temp_max_F", "temp_min_F", "temp_mean_F",
        "precipitation_inch", "weather_code", "weather_description"
    ])
    for i in range(len(dates)):
        wc = weather_code[i] if weather_code[i] is not None else ""
        desc = WMO_CODES.get(wc, str(wc)) if wc != "" else ""
        writer.writerow([
            dates[i],
            temp_max[i],
            temp_min[i],
            temp_mean[i],
            precip[i],
            wc,
            desc,
        ])

print(f"✅ Done! {len(dates)} days of data saved to: {OUTPUT}")
print(f"\n📊 Quick Stats:")
print(f"   Date range: {dates[0]} to {dates[-1]}")

# 过滤掉 None 值计算统计
valid_max = [t for t in temp_max if t is not None]
valid_min = [t for t in temp_min if t is not None]
valid_precip = [p for p in precip if p is not None]

if valid_max:
    print(f"   Hottest day:  {max(valid_max):.1f}°F on {dates[temp_max.index(max(valid_max))]}")
if valid_min:
    print(f"   Coldest day:  {min(valid_min):.1f}°F on {dates[temp_min.index(min(valid_min))]}")
if valid_precip:
    print(f"   Wettest day:  {max(valid_precip):.2f}\" on {dates[precip.index(max(valid_precip))]}")
    print(f"   Total precip: {sum(valid_precip):.2f}\"")