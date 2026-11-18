"""DarkWatch: a live logger that records, every 15 minutes, the newest reading of each gauge on a watch list,
so you capture REAL-TIME outages (what forecasters actually saw) instead of the repaired archive.

Run it either
  (a) on your own computer:   python -I darkwatch.py watchlist.csv log.csv      (leave it running, or use cron / Task Scheduler)
  (b) free, in the cloud:      GitHub Actions workflow in .github/workflows/darkwatch.yml (runs every 15 min, commits log.csv)

watchlist.csv columns: site,nwsli,name   (start with ~150 flood-prone gauges in states with winter storms:
CA, OR, WA, plus your region; add gauges inside any active NWS flood warning).
log.csv gets one row per gauge per poll: poll_time_utc, site, latest_obs_time_utc, latest_value_ft, minutes_since_obs.
A gauge is "silent" when minutes_since_obs > 3x its usual interval. The alarm rule is in gd_alarm.py.
"""
from __future__ import annotations
import csv, json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

LATEST = "https://api.waterdata.usgs.gov/ogcapi/v1/collections/latest-continuous/items"


def latest(sites: list[str]) -> dict[str, tuple[str, float]]:
    key = os.environ.get("USGS_API_KEY")
    hdr = {"User-Agent": "GaugeDark DarkWatch (student project)", **({"X-Api-Key": key} if key else {})}
    out = {}
    for i in range(0, len(sites), 50):                     # small batches keep URLs short
        chunk = sites[i:i + 50]
        q = {"monitoring_location_id": ",".join(f"USGS-{s}" for s in chunk), "parameter_code": "00065", "f": "json", "limit": "500"}
        req = urllib.request.Request(LATEST + "?" + urllib.parse.urlencode(q), headers=hdr)
        with urllib.request.urlopen(req, timeout=120) as r:
            for f in json.loads(r.read()).get("features", []):
                p = f["properties"]; s = p["monitoring_location_id"].replace("USGS-", "")
                out[s] = (p["time"], float(p["value"]) if p.get("value") not in (None, "") else None)
        time.sleep(1)
    return out


def poll_once(watchlist: str, log: str):
    sites = [r["site"] for r in csv.DictReader(open(watchlist))]
    now = datetime.now(timezone.utc)
    vals = latest(sites)
    new = not os.path.exists(log)
    with open(log, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["poll_time_utc", "site", "latest_obs_time_utc", "latest_value_ft", "minutes_since_obs"])
        for s in sites:
            t, v = vals.get(s, (None, None))
            age = round((now - datetime.fromisoformat(t)).total_seconds() / 60, 1) if t else None
            w.writerow([now.isoformat(timespec="minutes"), s, t, v, age])


if __name__ == "__main__":
    wl, lg = sys.argv[1], sys.argv[2]
    once = "--once" in sys.argv
    while True:
        try:
            poll_once(wl, lg)
        except Exception as e:                              # never crash the logger; record the failure
            with open(lg + ".errors", "a") as fh:
                fh.write(f"{datetime.now(timezone.utc).isoformat()} {e!r}\n")
        if once:
            break
        time.sleep(15 * 60)
