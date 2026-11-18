"""Tests for gd_gaps.py using the real Hunt, TX record (USGS 08165500 / NWS HNTT2), 4-5 July 2025,
as served by the Iowa Environmental Mesonet HADS archive on 16 Nov 2026 (values identical to the USGS archive).
Run:  python -I -m pytest code/test_gd_gaps.py   (or just: python -I code/test_gd_gaps.py)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime, timezone
from gd_gaps import analyze, max_rise_1h

def ms(s):
    return int(datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)

HUNT = [("2025-07-04 06:00",7.68),("2025-07-04 06:05",7.68),("2025-07-04 06:10",7.69),("2025-07-04 06:15",7.69),
("2025-07-04 06:20",7.7),("2025-07-04 06:25",7.71),("2025-07-04 06:30",7.71),("2025-07-04 06:35",7.72),("2025-07-04 06:40",7.75),
("2025-07-04 06:45",7.78),("2025-07-04 06:50",7.83),("2025-07-04 06:55",7.89),("2025-07-04 07:00",7.98),("2025-07-04 07:05",8.13),
("2025-07-04 07:10",8.27),("2025-07-04 07:15",8.4),("2025-07-04 07:20",8.54),("2025-07-04 07:25",8.7),("2025-07-04 07:30",8.82),
("2025-07-04 07:35",8.93),("2025-07-04 07:40",9.0),("2025-07-04 07:45",9.06),("2025-07-04 07:50",9.15),("2025-07-04 07:55",9.41),
("2025-07-04 08:00",10.1),("2025-07-04 08:05",11.03),("2025-07-04 08:10",11.93),("2025-07-04 08:15",13.03),("2025-07-04 08:20",13.99),
("2025-07-04 08:25",14.94),("2025-07-04 08:30",15.9),("2025-07-04 08:35",16.81),("2025-07-04 08:40",17.52),("2025-07-04 08:45",18.39),
("2025-07-04 08:50",19.35),("2025-07-04 08:55",20.3),("2025-07-04 09:00",21.11),("2025-07-04 09:05",21.99),("2025-07-04 09:10",22.85),
("2025-07-04 09:15",23.73),("2025-07-04 09:20",24.7),("2025-07-04 09:25",26.92),("2025-07-04 09:30",28.21),("2025-07-04 09:35",29.45),
("2025-07-04 10:10",37.52),
("2025-07-05 20:35",8.89),("2025-07-05 20:45",8.89),("2025-07-05 20:50",8.88),("2025-07-05 20:55",8.88),("2025-07-05 21:00",8.87),
("2025-07-05 21:05",8.87),("2025-07-05 21:10",8.87),("2025-07-05 21:15",8.87),("2025-07-05 21:20",8.86),("2025-07-05 21:25",8.86)]

RECS = [(ms(t), v, "A") for t, v in HUNT]

def test_hunt():
    r = analyze(RECS)
    assert r is not None and r.dark1 and r.dark3
    g = max(r.dark_gaps, key=lambda g: g.hours)
    assert g.v_before == 29.45                       # last real reading, 4:35 am CDT
    assert abs(g.hours - 35.0) < 0.01                # 09:35Z 4 Jul -> 20:35Z 5 Jul
    assert abs(g.deficit_ft - 8.07) < 0.01           # 37.52 crest - 29.45
    assert g.spans_peak and g.n_inserted_inside == 1 # 37.52 crest sits inside the gap
    assert len(r.inserted) == 1 and r.inserted[0][1] == 37.52
    assert max_rise_1h(RECS) == 12.64                # 09:35 29.45 - 08:35 16.81 (inserted crest excluded)

def test_estimated_values_do_not_hide_gap():
    recs = RECS + [(ms("2025-07-04 15:00"), 20.0, "A e")]
    r = analyze(recs)
    assert r.dark1                                    # estimated fill does not count as a live reading

if __name__ == "__main__":
    test_hunt(); test_estimated_values_do_not_hide_gap(); print("all tests passed")
