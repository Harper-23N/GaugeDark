"""GaugeDark gap detector (Python port of the rule used in the Round 55 pilot).

Input: a list of (time_utc_ms, value_ft, qualifier_string) for ONE gauge and ONE flood window.
Output: a dict describing the gauge's flood rise and every "dark" gap.

Rule (fixed before looking at results; change it only with a logbook entry):
  1. Keep numeric values; drop values whose USGS code contains 'e' (estimated).
  2. Median reporting interval = median spacing of the remaining readings.
  3. "Inserted" point = a reading that (a) is cut off from BOTH neighbours by >= max(3*median, 45 min), or
     (b) is followed by a gap >= that threshold, arrives off-schedule (>= 1.5*median after the previous reading)
     and is higher than the previous reading. These are usually crests added later from high-water marks
     (USGS memo SW 2006.05 tells offices to insert surveyed peaks into the unit values).
  4. A gap = spacing between consecutive regular readings >= 60 min AND >= 3.5 * median interval.
  5. A gap is DARK if the stage rose > 0.3 ft in the 30 min before it began, OR the event maximum
     (including inserted crests) falls inside it.
  6. deficit_ft = event maximum - last regular reading before the gap ("how far below the crest it went silent").
"""
from __future__ import annotations
from dataclasses import dataclass, field
from statistics import median

MIN = 60_000


@dataclass
class Gap:
    start: int
    end: int
    hours: float
    v_before: float
    v_after: float
    rising: bool
    spans_peak: bool
    deficit_ft: float
    rate30_ft: float | None
    n_inserted_inside: int


@dataclass
class GaugeResult:
    n: int
    median_interval_min: float
    rise_ft: float
    max_ft: float
    t_max: int
    inserted: list = field(default_factory=list)
    dark_gaps: list = field(default_factory=list)
    all_gaps: int = 0

    @property
    def dark1(self):
        return len(self.dark_gaps) > 0

    @property
    def dark3(self):
        return any(g.hours >= 3 for g in self.dark_gaps)


def regular_series(recs):
    """Return (regular readings, inserted readings, median interval) from (t, v, code) tuples."""
    num = [(t, v, c or "") for t, v, c in recs if v is not None]
    tel = [r for r in num if "e" not in r[2]]
    tel.sort()
    if len(tel) < 3:
        return tel, [], 15.0
    med = median((tel[i][0] - tel[i - 1][0]) / MIN for i in range(1, len(tel)))
    thr = max(3 * med, 45)
    keep, ins = [], []
    for i, r in enumerate(tel):
        dp = (r[0] - tel[i - 1][0]) / MIN if i > 0 else 1e9
        dn = (tel[i + 1][0] - r[0]) / MIN if i < len(tel) - 1 else 1e9
        isolated = dp >= thr and dn >= thr
        offgrid = dn >= thr and i > 0 and dp >= 1.5 * med and r[1] >= tel[i - 1][1]
        (ins if (isolated or offgrid) else keep).append(r)
    return keep, ins, med


def analyze(recs) -> GaugeResult | None:
    num = [(t, v, c) for t, v, c in recs if v is not None]
    if len(num) < 10:
        return None
    vmax = max(v for _, v, _ in num)
    vmin = min(v for _, v, _ in num)
    tmax = next(t for t, v, _ in num if v == vmax)
    reg, ins, med = regular_series(recs)
    res = GaugeResult(n=len(num), median_interval_min=med, rise_ft=round(vmax - vmin, 2), max_ft=vmax, t_max=tmax, inserted=ins)
    for i in range(1, len(reg)):
        g = (reg[i][0] - reg[i - 1][0]) / MIN
        if not (g >= 60 and g >= 3.5 * med):
            continue
        res.all_gaps += 1
        a, b = reg[i - 1], reg[i]
        prev = next((reg[j] for j in range(i - 1, -1, -1) if a[0] - reg[j][0] >= 30 * MIN), None)
        rate30 = (a[1] - prev[1]) if prev else None
        rising = rate30 is not None and rate30 > 0.3
        spans = a[0] < tmax < b[0]
        if rising or spans:
            res.dark_gaps.append(Gap(a[0], b[0], round(g / 60, 2), a[1], b[1], rising, spans,
                                     round(vmax - a[1], 2), None if rate30 is None else round(rate30, 2),
                                     sum(1 for p in ins if a[0] < p[0] < b[0])))
    return res


def max_rise_1h(recs) -> float:
    reg, _, _ = regular_series(recs)
    best, j = 0.0, 0
    for i in range(len(reg)):
        while j < i and reg[i][0] - reg[j][0] > 60 * MIN:
            j += 1
        if reg[i][0] - reg[j][0] >= 45 * MIN:
            best = max(best, reg[i][1] - reg[j][1])
    return round(best, 2)
