"""Silence alarm vs plain missing-data flag, replayed on archived flood records.

For every gap (>= 60 min and >= 3.5x the gauge's usual interval) between regular readings:
  truth  "dangerous"  = the event crest falls inside the gap and is >= 1 ft above the last reading,
                         OR the first reading after the gap is >= 2 ft above the last reading before it.
  baseline flag       = fires on every gap (what a generic "no data" indicator does).
  silence alarm       = fires only if the stage rose >= X ft in the ~60 min before the gauge went quiet.
The alarm uses ONLY information available when the gauge goes quiet; the truth label uses the future.
Pilot result (Round 55, 387 gauges, 157 gaps, 28 dangerous), X = 0.5 ft:
  silence alarm 19 hits / 9 misses / 10 false alarms (precision 0.66, recall 0.68);
  baseline flag 28 hits / 0 misses / 129 false alarms (precision 0.18).
These thresholds were tuned on the same 7 floods: you must re-test them on floods NOT used to choose them.
"""
from gd_gaps import regular_series, MIN


def evaluate(recs, X=0.5, K=2):
    reg, _, med = regular_series(recs)
    num = [(t, v) for t, v, _ in recs if v is not None]
    if len(reg) < 3 or not num:
        return []
    vmax = max(v for _, v in num); tmax = next(t for t, v in num if v == vmax)
    out = []
    for i in range(1, len(reg)):
        g = (reg[i][0] - reg[i - 1][0]) / MIN
        if not (g >= 60 and g >= 3.5 * med):
            continue
        a, b = reg[i - 1], reg[i]
        p60 = next((reg[j] for j in range(i - 1, -1, -1) if a[0] - reg[j][0] >= 55 * MIN), None)
        rise60 = (a[1] - p60[1]) if p60 else 0.0
        danger = (a[0] < tmax < b[0] and vmax - a[1] >= 1) or (b[1] - a[1] >= 2)
        out.append(dict(start=a[0], gap_h=g / 60, rise60=rise60, danger=danger,
                        silence_alarm=rise60 >= X, alarm_time=a[0] + K * med * MIN))
    return out


def score(all_gaps):
    tp = sum(g["danger"] and g["silence_alarm"] for g in all_gaps)
    fn = sum(g["danger"] and not g["silence_alarm"] for g in all_gaps)
    fp = sum((not g["danger"]) and g["silence_alarm"] for g in all_gaps)
    base_fp = sum(not g["danger"] for g in all_gaps)
    d = tp + fn
    return dict(gaps=len(all_gaps), dangerous=d, hits=tp, misses=fn, false_alarms=fp,
                precision=round(tp / (tp + fp), 3) if tp + fp else None, recall=round(tp / d, 3) if d else None,
                baseline_false_alarms=base_fp, baseline_precision=round(d / len(all_gaps), 3) if all_gaps else None)
