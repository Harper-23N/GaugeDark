"""Figures for the GaugeDark guide. Run: python -I code/make_figures.py  (from the bundle root)."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D, F = os.path.join(ROOT, "data"), os.path.join(ROOT, "figs")
os.makedirs(F, exist_ok=True)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "Inter", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})


def hm(s):  # "HH:MM" UTC -> hours CDT (UTC-5)
    h, m = map(int, s.split(":")); return h + m / 60 - 5


# 1. Guadalupe hydrographs
H = json.load(open(os.path.join(D, "guadalupe_4jul2025_hydrographs.json")))
CP_LIVE = [("11:15",6.16),("11:30",14.25),("11:45",18.75),("12:00",20.74),("12:15",21.28),("12:30",30.51),("12:45",21.03),("13:00",20.59),
           ("13:15",20.15),("13:30",19.75),("13:45",19.49),("14:00",19.49),("14:15",19.42),("14:30",19.61),("14:45",19.08),("15:00",17.97)]  # IEM HADS GCTT2
fig, ax = plt.subplots(figsize=(6.6, 3.1))
def series(key, cut=None):
    pts = H[key]; return [hm(t) for t, v in pts[:cut]], [v for t, v in pts[:cut]]
x, y = series("hunt_08165500", -1); ax.plot(x, y, color=BLUE, lw=2)
ax.scatter([hm("10:10")], [37.52], s=36, facecolor=SURF, edgecolor=BLUE, lw=1.6, zorder=5)
ax.text(hm("10:10") - 0.15, 37.52, "Hunt crest 37.52 ft (added later from a survey)", ha="right", va="center", color=INK2, fontsize=7.5)
ax.annotate("Hunt: last reading 29.45 ft at 4:35 am,\nthen silent for 35 hours", (hm("09:35"), 29.45), (0.2, 27.5), color=INK, fontsize=8,
            arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
x, y = series("kerrville_08166200"); ax.plot(x, y, color=ORANGE, lw=2)
ax.text(8.05, 21.5, "Kerrville: complete record", color=INK, fontsize=8)
x, y = series("centerpoint_08166250", -1); ax.plot(x, y, color=AQUA, lw=2)
ax.plot([hm(t) for t, v in CP_LIVE], [v for t, v in CP_LIVE], color=AQUA, lw=1.4, ls=(0, (3, 2)))
ax.scatter([hm("12:30")], [39.61], s=36, facecolor=SURF, edgecolor=AQUA, lw=1.6, zorder=5)
ax.text(hm("12:30") + 0.15, 39.61, "Center Point crest 39.61 ft (survey)", va="center", color=INK2, fontsize=7.5)
ax.text(7.2, 1.0, "Center Point: archive ends at 6.16 ft\n(6:15 am). The live feed (dashed) kept\nsending ~21 ft near the crest; USGS\nlater deleted those readings.", color=INK, fontsize=7.5)
ax.set_xlim(0, 10.2); ax.set_ylim(0, 42)
ax.set_xticks(range(0, 11, 2)); ax.set_xticklabels(["midnight", "2 am", "4 am", "6 am", "8 am", "10 am"])
ax.set_ylabel("gage height (ft)"); ax.set_title("Guadalupe River gauges, 4 July 2025 (local time)", loc="left", fontsize=10, color=INK, fontweight="semibold")
fig.tight_layout(); fig.savefig(os.path.join(F, "f1_guadalupe.png"), dpi=220); plt.close(fig)

# 2. dose-response
d = pd.read_csv(os.path.join(D, "stations_7floods_v3.csv"), dtype={"site": str})
d["bin"] = pd.cut(d.rise_ft, [-1, 5, 10, 20, 1e9], right=False, labels=["under 5 ft", "5-10 ft", "10-20 ft", "20 ft or more"])
g = d.groupby("bin", observed=True).agg(n=("site", "size"), dark=("dark1h", "sum"))
g["pct"] = 100 * g.dark / g.n
fig, ax = plt.subplots(figsize=(4.6, 2.6))
bars = ax.bar(g.index.astype(str), g.pct, color=BLUE, width=0.55)
for b, (n, k, p) in zip(bars, g[["n", "dark", "pct"]].values):
    ax.text(b.get_x() + b.get_width() / 2, p + 0.8, f"{p:.0f}%\n{int(k)} of {int(n)}", ha="center", va="bottom", fontsize=8, color=INK)
ax.set_ylim(0, 32); ax.set_ylabel("gauges dark 1 h+ (%)"); ax.set_xlabel("how far the river rose during the flood")
ax.set_title("Archive outages by size of rise, 7 floods, 387 gauges", loc="left", fontsize=10, color=INK, fontweight="semibold")
fig.tight_layout(); fig.savefig(os.path.join(F, "f2_dose.png"), dpi=220); plt.close(fig)

# 3. live classes
c = pd.read_csv(os.path.join(D, "live_feed_dark_gauges_classified.csv"), dtype={"site": str})
order = ["SILENT", "FROZEN", "UNDER_READ", "IMPLAUSIBLE", "LIVE_PRESENT", "NO_LIVE_DATA"]
lab = {"SILENT": "silent live too", "FROZEN": "frozen (stuck value)", "UNDER_READ": "kept sending, far too low", "IMPLAUSIBLE": "impossible numbers",
       "LIVE_PRESENT": "plausible live, deleted later", "NO_LIVE_DATA": "no live record found"}
k = c.live_class.value_counts().reindex(order).fillna(0)
fig, ax = plt.subplots(figsize=(5.6, 2.5))
ax.barh([lab[o] for o in order][::-1], k.values[::-1], color=BLUE, height=0.55)
for i, v in enumerate(k.values[::-1]):
    ax.text(v + 0.2, i, str(int(v)), va="center", fontsize=8, color=INK)
ax.set_xlim(0, 14); ax.grid(axis="y", visible=False); ax.set_xlabel("gauges (of 36 dark in the archive)")
ax.set_title("Live feed during the 36 archive gaps", loc="left", fontsize=10, color=INK, fontweight="semibold")
fig.tight_layout(); fig.savefig(os.path.join(F, "f3_live.png"), dpi=220); plt.close(fig)

# 4. alarm vs baseline
R = json.load(open(os.path.join(D, "pilot_results_round55.json")))["P4_silence_alarm_replay"]
fig, ax = plt.subplots(figsize=(4.6, 2.4))
names = ["plain 'no data' flag", "silence alarm (rise 0.5 ft/h)", "silence alarm (rise 1 ft/h)"]
hits = [R["baseline_every_gap"]["hits"], R["X_0.5ft"]["hits"], R["X_1ft"]["hits"]]
fa = [R["baseline_every_gap"]["false_alarms"], R["X_0.5ft"]["false_alarms"], R["X_1ft"]["false_alarms"]]
y = range(len(names))
ax.barh([i + 0.17 for i in y], hits, height=0.32, color=BLUE, label="dangerous outages caught (of 28)")
ax.barh([i - 0.17 for i in y], fa, height=0.32, color=ORANGE, label="false alarms")
for i in y:
    ax.text(hits[i] + 1.5, i + 0.17, str(hits[i]), va="center", fontsize=8, color=INK)
    ax.text(fa[i] + 1.5, i - 0.17, str(fa[i]), va="center", fontsize=8, color=INK)
ax.set_yticks(list(y)); ax.set_yticklabels(names); ax.invert_yaxis(); ax.grid(axis="y", visible=False); ax.set_xlim(0, 145)
ax.legend(frameon=False, fontsize=7.5, loc="lower right")
ax.set_title("Replay on 157 archive gaps (in-sample)", loc="left", fontsize=10, color=INK, fontweight="semibold")
fig.tight_layout(); fig.savefig(os.path.join(F, "f4_alarm.png"), dpi=220); plt.close(fig)

# 5. virtual gauge
V = json.load(open(os.path.join(D, "pilot_results_round55.json")))["P5_virtual_gauge_blankout"]["rows"]
fig, ax = plt.subplots(figsize=(5.6, 2.5))
xs = range(len(V))
ax.bar([i - 0.18 for i in xs], [r["rmse"]["persist"] for r in V], width=0.34, color=ORANGE, label="hold last value")
ax.bar([i + 0.18 for i in xs], [r["rmse"]["transfer"] for r in V], width=0.34, color=BLUE, label="copy upstream change")
ax.set_xticks(list(xs)); ax.set_xticklabels([r["pair"].replace(" (TX)", "\nTX").replace(" (NC)", "\nNC").replace("->", " to\n") for r in V], fontsize=6.5)
ax.set_ylabel("error on hidden rise (RMSE, ft)"); ax.legend(frameon=False, fontsize=7.5)
ax.set_title("Blank-out test on 6 healthy gauge pairs", loc="left", fontsize=10, color=INK, fontweight="semibold")
fig.tight_layout(); fig.savefig(os.path.join(F, "f5_virtual.png"), dpi=220); plt.close(fig)
print("figures written to", F)


# 6. P8: equipment limit vs failure (big-rise gauges with a published operational maximum)
fig, ax = plt.subplots(figsize=(3.3, 2.6))
cats = ["Crest reached\nequipment limit", "Crest stayed\nbelow limit"]
rate, n, k = [7 / 13, 20 / 92], [13, 92], [7, 20]
lo, hi = [0.29, 0.15], [0.77, 0.31]
ax.bar([0, 1], [r * 100 for r in rate], width=0.5, color=[ORANGE, BLUE], zorder=2)
ax.errorbar([0, 1], [r * 100 for r in rate], yerr=[[(r - l) * 100 for r, l in zip(rate, lo)], [(h - r) * 100 for r, h in zip(rate, hi)]],
            fmt="none", ecolor=INK2, elinewidth=0.8, capsize=3, zorder=3)
for i in range(2):
    ax.text(i, hi[i] * 100 + 4, f"{k[i]} of {n[i]}", ha="center", color=INK, fontsize=8)
ax.set_xticks([0, 1]); ax.set_xticklabels(cats, fontsize=8); ax.set_ylim(0, 90); ax.set_ylabel("Went dark (%)")
ax.set_title("But 23 of 27 dark gauges stopped below their limit", fontsize=8, color=INK2, loc="left")
ax.grid(axis="x", visible=False)
fig.tight_layout(); fig.savefig(os.path.join(F, "f6_limits.png"), dpi=220); plt.close(fig)

# 7. P9: live-feed rules, share of target failures caught vs share of healthy gauges alarmed
fig, ax = plt.subplots(figsize=(3.3, 2.6))
rules = ["Silence", "Impossible\nvalue", "Flat line"]
caught = [9 / 12, 6 / 6, 4 / 8]; fa = [1 / 81, 3 / 81, 24 / 81]
xs = range(3); w = 0.34
ax.bar([x - w / 2 - 0.01 for x in xs], [c * 100 for c in caught], width=w, color=BLUE, zorder=2, label="Failures caught")
ax.bar([x + w / 2 + 0.01 for x in xs], [f * 100 for f in fa], width=w, color=ORANGE, zorder=2, label="Healthy gauges alarmed")
for x, c, lab in zip(xs, caught, ["9/12", "6/6", "4/8"]):
    ax.text(x - w / 2, c * 100 + 2, lab, ha="center", fontsize=7.5, color=INK)
for x, f, lab in zip(xs, fa, ["1/81", "3/81", "24/81"]):
    ax.text(x + w / 2, f * 100 + 2, lab, ha="center", fontsize=7.5, color=INK)
ax.set_xticks(list(xs)); ax.set_xticklabels(rules, fontsize=8); ax.set_ylim(0, 110); ax.set_ylabel("%")
ax.legend(frameon=False, fontsize=7, loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=2, handlelength=1); ax.grid(axis="x", visible=False)
fig.tight_layout(); fig.savefig(os.path.join(F, "f7_detector.png"), dpi=220); plt.close(fig)
print("figures 6-7 written")
