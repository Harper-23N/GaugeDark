import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
from gd_gaps import analyze, is_estimated

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def load(name):
    """Read one of my USGS downloads. Handles both UTF-8 and UTF-16 files."""
    path = os.path.join(DATA, name)
    for enc in ("utf-8-sig", "utf-16"):
        try:
            with open(path, encoding=enc, newline="") as f:
                rows = list(csv.DictReader(f))
            break
        except UnicodeError:
            continue
    return [(int(datetime.fromisoformat(r["time_utc"]).timestamp() * 1000),
             float(r["value_ft"]) if r["value_ft"] else None,
             r["code"]) for r in rows]


def test_is_estimated():
    assert not is_estimated("Approved")
    assert not is_estimated("Approved|DAYUNKNOWN")
    assert not is_estimated("Provisional")
    assert is_estimated("A e")
    assert is_estimated("Approved|ESTIMATED")


def test_hunt_new_api():
    g = max(analyze(load("mine_hunt.csv")).dark_gaps, key=lambda g: g.hours)
    assert abs(g.hours - 35.0) < 0.01 and abs(g.deficit_ft - 8.07) < 0.01


def test_center_point_new_api():
    g = max(analyze(load("mine_cp_usgs.csv")).dark_gaps, key=lambda g: g.hours)
    assert abs(g.hours - 81.0) < 0.01 and abs(g.deficit_ft - 33.45) < 0.01


if __name__ == "__main__":
    test_is_estimated(); test_hunt_new_api(); test_center_point_new_api(); print("new tests passed")