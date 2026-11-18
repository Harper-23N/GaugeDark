"""Virtual-gauge baselines for a blanked rising limb (the "blank-out test").

Given an upstream gauge U and a downstream target D during one flood, hide D's rising limb and estimate it.
Estimators (all real-time-legal except the oracle):
  persist   : D(t) = D(t0)                                   (what a stale display shows)
  transfer  : D(t) = D(t0) + [U(t - lag) - U(t0 - lag)]        (naive: same stage change, shifted by travel time)
  regress   : D(t) = a + b * U(t - lag), fitted on PREVIOUS floods at the same pair  <-- you build this (Hours 99-104)
  interp    : straight line from D(t0) to the true crest       (ORACLE: uses the future; an upper bound, never deploy)
Round 55 pilot (6 usable pairs, lag picked by cross-correlation of 15-min changes over the same event):
  transfer beat persistence on RMSE in 6/6 pairs, but missed the Texas crests by -9.2, -19.9 and +13.9 ft.
  A 2-ft crest error target therefore needs a fitted stage-to-stage relation (regress) from earlier floods.
"""
from __future__ import annotations
import math


def to_grid(series, t0, t1, step_ms=15 * 60_000, max_gap_ms=90 * 60_000):
    out, j = [], 0
    s = sorted(series)
    t = t0
    while t <= t1:
        while j < len(s) - 2 and s[j + 1][0] < t:
            j += 1
        v = None
        if j + 1 < len(s):
            (ta, va), (tb, vb) = s[j][:2], s[j + 1][:2]
            if ta <= t <= tb and tb - ta <= max_gap_ms:
                v = va + (vb - va) * (t - ta) / max(1, tb - ta)
        out.append(v)
        t += step_ms
    return out


def best_lag(u, d, max_steps=48):
    best, lag = -2.0, 0
    for L in range(max_steps + 1):
        sxy = sxx = syy = 0.0
        for i in range(L + 1, len(d)):
            if None in (u[i - L], u[i - L - 1], d[i], d[i - 1]):
                continue
            x, y = u[i - L] - u[i - L - 1], d[i] - d[i - 1]
            sxy += x * y; sxx += x * x; syy += y * y
        if sxx and syy and sxy / math.sqrt(sxx * syy) > best:
            best, lag = sxy / math.sqrt(sxx * syy), L
    return lag, best


def rmse(est, truth):
    e = [a - b for a, b in zip(est, truth) if a is not None and b is not None]
    return math.sqrt(sum(x * x for x in e) / len(e)) if e else float("nan")


def blank_out(u, d, lag, start_idx, peak_idx, a=None, b=None):
    win = range(start_idx + 1, peak_idx + 1)
    d0, u0 = d[start_idx], u[start_idx - lag]
    truth = [d[i] for i in win]
    est = {
        "persist": [d0 for _ in win],
        "transfer": [d0 + (u[i - lag] - u0) if u[i - lag] is not None else d0 for i in win],
        "interp": [d0 + (d[peak_idx] - d0) * (i - start_idx) / (peak_idx - start_idx) for i in win],
    }
    if a is not None and b is not None:
        est["regress"] = [a + b * u[i - lag] if u[i - lag] is not None else None for i in win]
    return {k: dict(rmse=round(rmse(v, truth), 2), crest_error_ft=round(v[-1] - truth[-1], 2) if v[-1] is not None else None)
            for k, v in est.items()}
