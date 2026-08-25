"""
AHP weight derivation and consistency ratio (thesis sec.3.6.3).
===============================================================

WHY THIS EXISTS
---------------
The bundle records only the eight FINAL weights (`models/core/ahp_weights.txt`).
The pairwise comparison matrix that produced them is not stored anywhere in the
project, so the Consistency Ratio required by sec.3.6.3 (CR <= 0.10) could not
be reported in Chapter Four.

Two matrices are evaluated below.

MATRIX A - the one printed in thesis Table 3.4.
    It is real, it is perfectly reciprocal, and it is CONSISTENT (CR = 0.0074).
    But it is labelled "illustrative" in the thesis and it describes a DIFFERENT
    factor set from the delivered model: it contains Soil and SWAT but no TWI,
    while the delivered index has TWI as its second-heaviest factor (0.18) and
    no soil factor at all. Its weights therefore do not reproduce the delivered
    weights and it cannot be cited as their source.

MATRIX B - a candidate matrix over the eight DELIVERED factors, whose entries
    are Saaty-scale integers chosen to approximate the delivered weights.

READ THIS BEFORE USING MATRIX B
-------------------------------
Matrix B was constructed by rounding the ratios w_i/w_j of the delivered weights
onto Saaty's scale. That makes it a plausible reconstruction, NOT a record of
judgements anyone actually made. AHP's consistency check tests whether a set of
human pairwise judgements is coherent; running it on a matrix reverse-engineered
from the answers tests nothing.

So do not paste Matrix B's CR into the thesis and move on. Either:

  (a) recover the pairwise matrix you actually built, put it in the script, and
      report its CR - this is the correct route; or
  (b) treat Matrix B as a starting point, review every entry against your own
      reasoning about Lagos flood processes, change what you disagree with,
      re-run, and report the result as your matrix.

Note what happens if you skip the rounding: a matrix built as exactly
a_ij = w_i/w_j is perfectly consistent by construction, giving CR = 0.000 for
ANY weight vector whatsoever. The script prints this case too, to show why it
is not evidence of anything.

Run:  python ahp_consistency.py
"""

import numpy as np

RI = {3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

# ── Matrix A: thesis Table 3.4, as printed ─────────────────────────────────
A_FACTORS = ["Elev", "Slope", "FlowAcc", "DistRiv", "LandCov", "Soil", "Rain", "SWAT"]
A = np.array([
    [1, 2, 2, 1 / 2, 3, 3, 2, 2],
    [1 / 2, 1, 1, 1 / 3, 2, 2, 1, 1],
    [1 / 2, 1, 1, 1 / 2, 2, 2, 1, 1],
    [2, 3, 2, 1, 3, 4, 2, 3],
    [1 / 3, 1 / 2, 1 / 2, 1 / 3, 1, 1, 1 / 2, 1 / 2],
    [1 / 3, 1 / 2, 1 / 2, 1 / 4, 1, 1, 1 / 2, 1 / 2],
    [1 / 2, 1, 1, 1 / 2, 2, 2, 1, 1],
    [1 / 2, 1, 1, 1 / 3, 2, 2, 1, 1],
], dtype=float)

# ── Delivered weights (models/core/ahp_weights.txt) ────────────────────────
B_FACTORS = ["Elevation", "TWI", "DistRivers", "FlowAccum", "Runoff", "Slope",
             "Rainfall", "LULC"]
B_TARGET = np.array([0.20, 0.18, 0.15, 0.12, 0.12, 0.10, 0.08, 0.05])

# ── Matrix B: Saaty-scale integers approximating those ratios ──────────────
# Upper triangle only; the lower triangle is filled by reciprocity.
# REVIEW THESE. Each entry says "how many times more important is the row
# factor than the column factor" on Saaty's 1-9 scale.
B_UPPER = {
    (0, 1): 1, (0, 2): 1, (0, 3): 2, (0, 4): 2, (0, 5): 2, (0, 6): 3, (0, 7): 4,
    (1, 2): 1, (1, 3): 2, (1, 4): 2, (1, 5): 2, (1, 6): 2, (1, 7): 4,
    (2, 3): 1, (2, 4): 1, (2, 5): 2, (2, 6): 2, (2, 7): 3,
    (3, 4): 1, (3, 5): 1, (3, 6): 2, (3, 7): 2,
    (4, 5): 1, (4, 6): 2, (4, 7): 2,
    (5, 6): 1, (5, 7): 2,
    (6, 7): 2,
}


def build(n, upper):
    M = np.ones((n, n))
    for (i, j), v in upper.items():
        M[i, j] = v
        M[j, i] = 1 / v
    return M


def analyse(M, factors, label):
    n = len(M)
    recip = float(np.max(np.abs(M * M.T - 1)))
    # geometric mean method - the approximation sec.3.6.3 specifies
    gm = np.prod(M, axis=1) ** (1 / n)
    w = gm / gm.sum()
    lam = float(np.mean((M @ w) / w))
    ci = (lam - n) / (n - 1)
    cr = ci / RI[n]

    print(f"\n{'=' * 62}\n{label}\n{'=' * 62}")
    print(f"  reciprocity error : {recip:.6f}  (0 = perfectly reciprocal)")
    print(f"  lambda_max        : {lam:.4f}   (n = {n})")
    print(f"  CI                : {ci:.4f}")
    print(f"  CR = CI / {RI[n]}   : {cr:.4f}   "
          f"{'ACCEPTABLE (<= 0.10)' if cr <= 0.10 else 'NOT ACCEPTABLE (> 0.10)'}")
    print("\n  derived weights:")
    for f, x in zip(factors, w):
        print(f"     {f:<12}{x:.4f}")
    return w, cr


def main():
    analyse(A, A_FACTORS, "MATRIX A - thesis Table 3.4 as printed "
                          "(illustrative; different factor set)")

    B = build(8, B_UPPER)
    wB, crB = analyse(B, B_FACTORS,
                      "MATRIX B - candidate matrix over the DELIVERED factors "
                      "(REQUIRES YOUR REVIEW)")

    print("\n  agreement with the delivered weights:")
    print(f"     {'factor':<12}{'target':>9}{'matrix B':>10}{'diff':>8}")
    for f, t, d in zip(B_FACTORS, B_TARGET, wB):
        print(f"     {f:<12}{t:>9.3f}{d:>10.3f}{d - t:>+8.3f}")
    print(f"     max absolute difference: {float(np.max(np.abs(wB - B_TARGET))):.3f}")

    # The degenerate case, shown to demonstrate why it proves nothing.
    exact = B_TARGET[:, None] / B_TARGET[None, :]
    n = 8
    gm = np.prod(exact, axis=1) ** (1 / n)
    w = gm / gm.sum()
    lam = float(np.mean((exact @ w) / w))
    cr0 = ((lam - n) / (n - 1)) / RI[n]
    print(f"\n{'=' * 62}\nDEGENERATE CASE - matrix built as exactly a_ij = w_i/w_j"
          f"\n{'=' * 62}")
    print(f"  CR = {cr0:.6f}")
    print("  A matrix reverse-engineered from the weights is perfectly consistent")
    print("  by construction, for ANY weights at all. It is not evidence that the")
    print("  underlying judgements were coherent. Do not report this number.")


if __name__ == "__main__":
    main()
