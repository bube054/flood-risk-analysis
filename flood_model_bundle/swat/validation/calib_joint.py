"""
Multi-variable (discharge + ET) calibration probe for the Ogun SWAT+ model.
==========================================================================

This is the multi-variable data-scarce calibration of Odusanya et al. (2019):
score the model against TWO independent variables at once, so a parameter set
cannot win by fitting streamflow while getting the water balance wrong.

  discharge -> GEOGLOWS reach 140585128, monthly, at outlet cha01
  ET        -> TerraClimate basin-mean AET, monthly (see et_validation.py for
               why this stands in for MOD16)

Each run writes calibration.cal, executes the SWAT+ engine, and reports NSE /
R2 / PBIAS for BOTH variables. Nothing is auto-accepted -- this reports, you
decide. The existing calibrated set is the incumbent and must be beaten on ET
WITHOUT dropping discharge below the thesis thresholds (NSE>=0.50, R2>=0.60,
|PBIAS|<=25%).

Usage:
    python calib_joint.py                      # score the incumbent set
    python calib_joint.py '[["petco","absval",1.4]]'   # try a variant
"""

import collections
import csv
import json
import math
import os
import subprocess
import sys
from pathlib import Path

TXT = Path(r"C:\SWAT_Ogun\OgunModel2\Scenarios\Default\TxtInOut")
EXE = Path(
    r"C:\Users\bube\SWATPlus\SWATPlusEditor\resources\app.asar.unpacked"
    r"\static\swat_exe\swatplus-62-ifo-win_amd64-Rel.exe"
)
HERE = Path(__file__).resolve().parent
GEO = HERE.parent / "geoglows_ogun_kara_140585128_monthly.csv"
ET_REF = HERE / "et_monthly_comparison.csv"

INCUMBENT = [
    ["perco", "absval", 0.30],
    ["petco", "absval", 1.20],
    ["canmx", "absval", 12.0],
    ["alpha", "absval", 0.022],
    ["flo_min", "absval", 10.0],
    ["bf_max", "absval", 0.55],
]


def stats(obs, sim):
    n = len(obs)
    mo, ms = sum(obs) / n, sum(sim) / n
    nse = 1 - sum((o - s) ** 2 for o, s in zip(obs, sim)) / sum((o - mo) ** 2 for o in obs)
    pb = 100 * sum(o - s for o, s in zip(obs, sim)) / sum(obs)
    soo = sum((o - mo) ** 2 for o in obs)
    sss = sum((s - ms) ** 2 for s in sim)
    sos = sum((o - mo) * (s - ms) for o, s in zip(obs, sim))
    r2 = (sos / math.sqrt(soo * sss)) ** 2 if soo * sss > 0 else 0.0
    return nse, r2, pb


def write_cal(ps):
    L = ["calibration.cal: auto", str(len(ps)),
         "name           chg_typ         chg_val  conds   lyr1   lyr2  "
         "year1  year2   day1   day2 obj_tot"]
    for nm, ct, cv in ps:
        L.append(f"{nm:<15}{ct:<12}{cv:>9.5f}      0      0      0      0      0      0      0      0")
    (TXT / "calibration.cal").write_text("\n".join(L) + "\n", newline="\n")


def ensure_cio():
    p = TXT / "file.cio"
    Ls = p.read_text().splitlines()
    for i, ln in enumerate(Ls):
        t = ln.split()
        if t and t[0] == "chg":
            if "calibration.cal" not in t:
                for j in range(1, len(t)):
                    if t[j] == "null":
                        t[j] = "calibration.cal"
                        break
                Ls[i] = "".join(f"{x:<18}" for x in t)
            break
    p.write_text("\n".join(Ls) + "\n", newline="\n")


def score_discharge():
    lines = (TXT / "channel_sd_mon.txt").read_text().splitlines()
    hdr = lines[1].split()
    fi = hdr.index("flo_out")
    ch = collections.defaultdict(dict)
    for ln in lines[3:]:
        p = ln.split()
        if len(p) > fi:
            ch[p[6]][(int(p[3]), int(p[1]))] = float(p[fi])
    m = {k: sum(v.values()) / len(v) for k, v in ch.items()}
    sim = ch[max(m, key=m.get)]
    obs = {}
    for r in csv.reader(open(GEO)):
        if r[0] != "month":
            y, mo = r[0].split("-")
            obs[(int(y), int(mo))] = float(r[1])
    pr = [(obs[k], sim[k]) for k in sorted(sim) if k in obs and k[0] >= 2011]
    return stats([a for a, _ in pr], [b for _, b in pr])


def score_et():
    ref = {}
    with open(ET_REF) as f:
        for row in csv.DictReader(f):
            y, m = row["month"].split("-")
            ref[(int(y), int(m))] = float(row["terraclimate_aet_mm"])
    lines = (TXT / "basin_wb_mon.txt").read_text().splitlines()
    hdr = lines[1].split()
    ei = hdr.index("et")
    sim = {}
    for ln in lines[3:]:
        p = ln.split()
        if len(p) > ei:
            sim[(int(p[3]), int(p[1]))] = float(p[ei])
    pr = [(ref[k], sim[k]) for k in sorted(sim) if k in ref]
    return stats([a for a, _ in pr], [b for _, b in pr])


def main():
    ps = json.loads(sys.argv[1]) if len(sys.argv) > 1 else INCUMBENT
    write_cal(ps)
    ensure_cio()
    subprocess.run([str(EXE)], cwd=str(TXT), capture_output=True, timeout=600)

    q = score_discharge()
    e = score_et()
    pass_q = q[0] >= 0.50 and q[1] >= 0.60 and abs(q[2]) <= 25

    print(f"params   : {[(a, c) for a, _, c in ps]}")
    print(f"DISCHARGE: NSE {q[0]:+.3f}  R2 {q[1]:.3f}  PBIAS {q[2]:+.1f}%   "
          f"{'PASS' if pass_q else 'FAIL'} (thesis thresholds)")
    print(f"ET       : NSE {e[0]:+.3f}  R2 {e[1]:.3f}  PBIAS {e[2]:+.1f}%")
    return {"params": ps, "discharge": q, "et": e, "discharge_passes": pass_q}


if __name__ == "__main__":
    main()
