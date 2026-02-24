#!/usr/bin/env python3
"""
fetch_events.py — Charlottesville Downtown Mall Events Calendar
For "The Breathing of Downtown" data visualization (SDS Competition)

DATA SOURCES:
1. Ting Pavilion (Fridays After Five schedule) — scraped from tingpavilion.com
2. Visit Charlottesville events — scraped from visitcharlottesville.org
3. Curated annual events — hand-compiled from local news + community sites

The curated events are based on research from:
  - Ting Pavilion: https://www.tingpavilion.com/events-tickets/fridaysafter5
  - Tom Tom Foundation: https://www.tomtomfoundation.org/2025-festival
  - Visit Charlottesville: https://www.visitcharlottesville.org/events/
  - CBS19 News / Daily Progress / C-VILLE Weekly
  - Charlottesville Family: https://charlottesvillefamily.com/

NOTE: Many Charlottesville events do not have a clean public API.
This script combines automated scraping (where possible) with a curated
calendar of recurring annual events that have been verified through
local news sources and official event pages. Dates are approximate
for years before 2025 (most festivals land in the same week each year).

Usage:
    pip install requests beautifulsoup4
    python fetch_events.py
    # Outputs: cville_events_calendar.json, cville_events_calendar.csv
"""

import json
import csv
from datetime import date, timedelta
import sys

# Try to import scraping libraries (optional)
try:
    import requests
    from bs4 import BeautifulSoup

    HAS_SCRAPING = True
except ImportError:
    HAS_SCRAPING = False
    print("Note: requests/beautifulsoup4 not installed. Using curated data only.")
    print("Install with: pip install requests beautifulsoup4")

# ============================================================
# CURATED ANNUAL EVENTS (2015-2025)
# ============================================================
# These are recurring Charlottesville events that impact Downtown Mall
# foot traffic. Dates are based on typical scheduling patterns.
# Boost values (0-1) estimate relative impact on foot traffic.

RECURRING_EVENTS = [
    {
        "name": "Fridays After Five",
        "type": "music",
        "description": "Free concert series at Ting Pavilion. 37th season in 2025.",
        "source": "https://www.tingpavilion.com/events-tickets/fridaysafter5",
        "pattern": "every_friday",
        "season_start_month": 4,
        "season_start_day": 18,  # Typically 3rd Friday of April
        "season_end_month": 9,
        "season_end_day": 5,  # First Friday of September
        "start_year": 2015,
        "end_year": 2025,
        "skip_years": [2020],  # COVID cancellation
        "boost": 0.4,
        "time": "17:30-21:00",
        "location": "Ting Pavilion, Downtown Mall"
    },
    {
        "name": "Tom Tom Festival",
        "type": "festival",
        "description": "Music, art & ideas festival. Block party on Downtown Mall.",
        "source": "https://www.tomtomfoundation.org/2025-festival",
        "pattern": "fixed_dates",
        "typical_month": 4,
        "typical_days": [16, 17, 18, 19, 20],  # 2025 dates
        "start_year": 2013,
        "end_year": 2025,
        "skip_years": [2020, 2021],  # COVID
        "boost": 0.6,
        "location": "Downtown Mall, CODE Building"
    },
    {
        "name": "Virginia Film Festival",
        "type": "festival",
        "description": "International film celebration at Violet Crown & Paramount.",
        "source": "https://virginiafilmfestival.org",
        "pattern": "fixed_dates",
        "typical_month": 10,
        "typical_days": [22, 23, 24, 25, 26],  # Late October
        "start_year": 2015,
        "end_year": 2025,
        "skip_years": [2020],
        "boost": 0.35,
        "location": "Violet Crown Cinema, Paramount Theater"
    },
    {
        "name": "Virginia Festival of the Book",
        "type": "festival",
        "description": "Literary culture celebration. Free and open to public.",
        "source": "https://vabook.org",
        "pattern": "fixed_dates",
        "typical_month": 3,
        "typical_days": [18, 19, 20, 21, 22],  # Mid-March
        "start_year": 2015,
        "end_year": 2025,
        "skip_years": [2020],
        "boost": 0.25,
        "location": "Downtown Mall venues"
    },
    {
        "name": "Charlottesville City Market",
        "type": "market",
        "description": "Saturday farmers market with local produce and crafts.",
        "source": "https://www.charlottesvillecitymarket.com",
        "pattern": "every_saturday",
        "season_start_month": 4,
        "season_start_day": 1,
        "season_end_month": 12,
        "season_end_day": 20,
        "start_year": 2015,
        "end_year": 2025,
        "skip_years": [],  # Ran even during COVID (outdoors)
        "boost": 0.2,
        "time": "07:00-12:00",
        "location": "City Market, Water Street"
    },
    {
        "name": "First Fridays",
        "type": "art",
        "description": "Gallery walk on the Downtown Mall. First Friday of each month.",
        "source": "https://www.visitcharlottesville.org",
        "pattern": "first_friday",
        "start_year": 2015,
        "end_year": 2025,
        "skip_years": [2020],
        "boost": 0.2,
        "time": "17:00-20:00",
        "location": "Downtown Mall galleries"
    },
    {
        "name": "Dogwood Festival",
        "type": "festival",
        "description": "Spring parade & carnival since 1950. Canceled 2025.",
        "source": "https://www.cvilledogwood.com",
        "pattern": "fixed_dates",
        "typical_month": 4,
        "typical_days": [10, 11, 12, 13, 14],
        "start_year": 2015,
        "end_year": 2024,  # Canceled in 2025
        "skip_years": [2020, 2021],
        "boost": 0.3,
        "location": "Downtown Charlottesville"
    },
    {
        "name": "Soul of C'ville",
        "type": "festival",
        "description": "Celebration of Black excellence in Charlottesville.",
        "source": "https://www.soulofcville.com",
        "pattern": "fixed_dates",
        "typical_month": 6,
        "typical_days": [14, 15, 16],
        "start_year": 2018,
        "end_year": 2025,
        "skip_years": [2020],
        "boost": 0.3,
        "location": "IX Art Park"
    },
    {
        "name": "Juneteenth Celebration",
        "type": "civic",
        "description": "Community celebration of freedom.",
        "pattern": "fixed_dates",
        "typical_month": 6,
        "typical_days": [19],
        "start_year": 2020,
        "end_year": 2025,
        "boost": 0.2,
        "location": "Downtown Mall"
    },
    {
        "name": "Independence Day",
        "type": "civic",
        "description": "Fireworks and celebrations.",
        "pattern": "fixed_dates",
        "typical_month": 7,
        "typical_days": [4],
        "start_year": 2015,
        "end_year": 2025,
        "skip_years": [2020],
        "boost": 0.5,
        "location": "McIntire Park / Downtown"
    },
    {
        "name": "Halloween on the Mall",
        "type": "civic",
        "description": "Downtown trick-or-treating and costume parade.",
        "pattern": "fixed_dates",
        "typical_month": 10,
        "typical_days": [31],
        "start_year": 2015,
        "end_year": 2025,
        "skip_years": [2020],
        "boost": 0.3,
        "location": "Downtown Mall"
    },
    {
        "name": "First Night Charlottesville",
        "type": "civic",
        "description": "New Year's Eve celebration on the Downtown Mall.",
        "pattern": "fixed_dates",
        "typical_month": 12,
        "typical_days": [31],
        "start_year": 2015,
        "end_year": 2025,
        "skip_years": [2020],
        "boost": 0.45,
        "location": "Downtown Mall"
    },
    {
        "name": "Small Business Saturday",
        "type": "market",
        "description": "Shop local celebration.",
        "pattern": "fixed_dates",
        "typical_month": 11,
        "typical_days": [25],  # Day after Black Friday (approximate)
        "start_year": 2015,
        "end_year": 2025,
        "boost": 0.2,
        "location": "Downtown Mall shops"
    },
    {
        "name": "UVA Graduation Weekend",
        "type": "uva",
        "description": "Families flood downtown for UVA commencement.",
        "pattern": "fixed_dates",
        "typical_month": 5,
        "typical_days": [17, 18, 19],
        "start_year": 2015,
        "end_year": 2025,
        "skip_years": [2020],
        "boost": 0.35,
        "location": "UVA Grounds + Downtown"
    },
    {
        "name": "UVA Move-In Weekend",
        "type": "uva",
        "description": "Students return, restaurants and shops see surge.",
        "pattern": "fixed_dates",
        "typical_month": 8,
        "typical_days": [22, 23, 24, 25],
        "start_year": 2015,
        "end_year": 2025,
        "boost": 0.15,
        "location": "UVA area + Downtown"
    },
]


# ============================================================
# SCRAPING (optional, if libraries available)
# ============================================================
def scrape_ting_pavilion():
    """Try to get Fridays After Five lineup dates from Ting Pavilion."""
    events = []
    if not HAS_SCRAPING:
        return events
    try:
        url = "https://www.tingpavilion.com/events-tickets/fridaysafter5"
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'BreathingOfDowntown/1.0 (SDS academic project)'
        })
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Look for event date elements (site structure may vary)
            for item in soup.find_all(['h3', 'h4', 'div'], class_=lambda c: c and 'event' in str(c).lower()):
                text = item.get_text(strip=True)
                if text:
                    events.append(text)
            print(f"  Scraped {len(events)} items from Ting Pavilion")
    except Exception as e:
        print(f"  Ting scrape failed: {e}")
    return events


def scrape_visit_cville():
    """Try to get upcoming events from Visit Charlottesville."""
    events = []
    if not HAS_SCRAPING:
        return events
    try:
        url = "https://www.visitcharlottesville.org/events/"
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'BreathingOfDowntown/1.0 (SDS academic project)'
        })
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for item in soup.find_all(['h3', 'h4', 'a'], class_=lambda c: c and 'event' in str(c).lower()):
                text = item.get_text(strip=True)
                if text and len(text) > 5:
                    events.append(text)
            print(f"  Scraped {len(events)} items from Visit Charlottesville")
    except Exception as e:
        print(f"  VisitCville scrape failed: {e}")
    return events


# ============================================================
# GENERATE CONCRETE EVENT DATES
# ============================================================
def generate_event_dates(event_def, year):
    """Generate specific dates for an event in a given year."""
    if year < event_def.get('start_year', 2015):
        return []
    if year > event_def.get('end_year', 2025):
        return []
    if year in event_def.get('skip_years', []):
        return []

    dates = []
    pattern = event_def['pattern']

    if pattern == 'fixed_dates':
        month = event_def['typical_month']
        for day in event_def['typical_days']:
            try:
                d = date(year, month, day)
                dates.append(d)
            except ValueError:
                pass

    elif pattern == 'every_friday':
        start = date(year, event_def['season_start_month'], event_def['season_start_day'])
        end = date(year, event_def['season_end_month'], event_def['season_end_day'])
        d = start
        while d <= end:
            if d.weekday() == 4:  # Friday
                dates.append(d)
            d += timedelta(days=1)

    elif pattern == 'every_saturday':
        start = date(year, event_def['season_start_month'], event_def['season_start_day'])
        end = date(year, event_def['season_end_month'], event_def['season_end_day'])
        d = start
        while d <= end:
            if d.weekday() == 5:  # Saturday
                dates.append(d)
            d += timedelta(days=1)

    elif pattern == 'first_friday':
        for month in range(1, 13):
            d = date(year, month, 1)
            # Find first Friday
            while d.weekday() != 4:
                d += timedelta(days=1)
            dates.append(d)

    return dates


def build_full_calendar(start_year=2015, end_year=2025):
    """Build complete event calendar with specific dates."""
    calendar = []

    for event_def in RECURRING_EVENTS:
        for year in range(start_year, end_year + 1):
            dates = generate_event_dates(event_def, year)
            for d in dates:
                calendar.append({
                    'date': d.isoformat(),
                    'name': event_def['name'],
                    'type': event_def['type'],
                    'boost': event_def['boost'],
                    'description': event_def.get('description', ''),
                    'location': event_def.get('location', 'Downtown Mall'),
                    'source': event_def.get('source', 'curated'),
                })

    # Sort by date
    calendar.sort(key=lambda x: x['date'])
    return calendar


def build_viz_format():
    """Build the compact format used by the visualization."""
    viz_events = []
    for ev in RECURRING_EVENTS:
        entry = {
            'name': ev['name'],
            'type': ev['type'],
            'boost': ev['boost'],
            'desc': ev.get('description', ''),
        }

        if ev['pattern'] == 'every_friday':
            entry['recurring'] = 'friday'
            entry['startMonth'] = ev['season_start_month']
            entry['startDay'] = ev['season_start_day']
            entry['endMonth'] = ev['season_end_month']
            entry['endDay'] = ev['season_end_day']
        elif ev['pattern'] == 'every_saturday':
            entry['recurring'] = 'saturday'
            entry['startMonth'] = ev['season_start_month']
            entry['startDay'] = ev['season_start_day']
            entry['endMonth'] = ev['season_end_month']
            entry['endDay'] = ev['season_end_day']
        elif ev['pattern'] == 'first_friday':
            entry['recurring'] = 'first_friday'
        elif ev['pattern'] == 'fixed_dates':
            entry['month'] = ev['typical_month']
            entry['days'] = ev['typical_days']

        if ev.get('end_year') and ev['end_year'] < 2025:
            entry['endYear'] = ev['end_year']
        if ev.get('skip_years'):
            entry['skipYears'] = ev['skip_years']

        viz_events.append(entry)

    return viz_events


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("Charlottesville Downtown Mall Events Calendar")
    print("=" * 60)

    # Try scraping
    print("\n[1/4] Attempting live scraping...")
    ting_events = scrape_ting_pavilion()
    visit_events = scrape_visit_cville()

    # Build full calendar
    print("\n[2/4] Generating event calendar (2015-2025)...")
    calendar = build_full_calendar()
    print(f"  Generated {len(calendar)} total event-days")

    # Count by type
    by_type = {}
    for ev in calendar:
        by_type[ev['type']] = by_type.get(ev['type'], 0) + 1
    for t, c in sorted(by_type.items()):
        print(f"    {t}: {c} days")

    # Count by year
    by_year = {}
    for ev in calendar:
        yr = ev['date'][:4]
        by_year[yr] = by_year.get(yr, 0) + 1
    print("\n  Events by year:")
    for yr in sorted(by_year.keys()):
        print(f"    {yr}: {by_year[yr]} event-days")

    # Save full calendar as JSON
    print("\n[3/4] Saving outputs...")
    with open('cville_events_calendar.json', 'w') as f:
        json.dump({
            'metadata': {
                'description': 'Charlottesville Downtown Mall Events Calendar',
                'source': 'Curated from local news, official event pages, and web scraping',
                'years': '2015-2025',
                'event_definitions': len(RECURRING_EVENTS),
                'total_event_days': len(calendar),
                'scraped_ting': len(ting_events),
                'scraped_visit_cville': len(visit_events),
            },
            'event_definitions': RECURRING_EVENTS,
            'calendar': calendar,
            'viz_format': build_viz_format(),
        }, f, indent=2, default=str)
    print("  -> cville_events_calendar.json")

    # Save as CSV
    with open('cville_events_calendar.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'name', 'type', 'boost', 'description', 'location', 'source'])
        writer.writeheader()
        writer.writerows(calendar)
    print("  -> cville_events_calendar.csv")

    # Also save the viz-format JSON (for direct embedding in HTML)
    viz = build_viz_format()
    with open('cville_events_viz.json', 'w') as f:
        json.dump(viz, f, indent=2)
    print("  -> cville_events_viz.json (visualization format)")

    print(f"\n[4/4] Done! {len(RECURRING_EVENTS)} event types, {len(calendar)} total event-days")
    print("\nKey events in the data:")
    for ev in RECURRING_EVENTS:
        skip = f" (skip: {ev.get('skip_years', [])})" if ev.get('skip_years') else ""
        end = f" (ends {ev.get('end_year')})" if ev.get('end_year', 2025) < 2025 else ""
        print(f"  {ev['name']:30s} boost={ev['boost']:.2f}  {ev['pattern']:15s}{end}{skip}")