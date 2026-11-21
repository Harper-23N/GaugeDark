import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gd_fetch

GAUGES = {
    "15485500": "Tanana River at Fairbanks, AK",
    "05082500": "Red River at Grand Forks, ND",
    "06342500": "Missouri River at Bismarck, ND",
    "06214500": "Yellowstone River at Billings, MT",
    "05331000": "Mississippi River at St. Paul, MN",
}
START, END = "2024-01-01T00:00:00Z", "2024-01-15T00:00:00Z"

for site, name in GAUGES.items():
    for param in ("00065", "00060"):          # gage height, discharge
        try:
            rows = gd_fetch.usgs_continuous(site, START, END, param)
            codes = sorted(set(r[2] for r in rows))
            print(f"{site} {name} [{param}] {len(rows)} rows: {codes}")
        except Exception as e:
            print(f"{site} [{param}] error: {e}")