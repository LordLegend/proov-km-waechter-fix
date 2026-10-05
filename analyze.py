# analyze.py
# SUMMARY (from the numbers below, same 120 cars used to build and check the score):
# km_since_service (gap/std=0.98), avg_daily_km (0.61), and load_factor (0.52) separate the groups;
# odometer_km and age_years do not (<0.01). At top-32 all three methods catch 17/26 (65%); at top-40
# the combined score reaches 20/26 (77%) vs 18/26 (69%) for km_since_service alone.

# Make KM-Waechter smarter. The 80% rule only warns you once a car is nearly worn. Here you find
# which cars are most likely to break down SOON, from their history, and rank them by risk, so the
# fleet team fixes the risky ones first.
#
# fleet_history.csv has one row per car (120 of them) and a "broke_down" column (1 = it later
# broke down).

import pandas as pd
from km_wachter import SERVICE_INTERVAL_KM, WARN_AT_PERCENT

# ── 1. Load data ──────────────────────────────────────────────────────────────
df = pd.read_csv("fleet_history.csv")
print(f"Loaded {len(df)} cars, {df['broke_down'].sum()} broke down.\n")

# ── 2. Column-by-column comparison: gap measured in standard deviations ───────
numeric_cols = [c for c in df.columns if c not in ("car_id", "broke_down")]

broke = df[df["broke_down"] == 1]
ok    = df[df["broke_down"] == 0]

# Separation criterion: |mean(broke) - mean(ok)| / whole-fleet std >= 0.30
# Using the whole-fleet std as a simple, single-number measure of spread.
SEPARATION_THRESHOLD = 0.30   # gap must be at least 0.3 std-devs to matter

print("=" * 76)
print(f"{'Column':<20} {'mean(broke)':>12} {'mean(ok)':>10} "
      f"{'gap/range':>10} {'gap/std':>8}  separates?")
print("-" * 76)

separating  = []   # columns that pass the threshold
gap_in_stds = {}   # weight for the combined score

for col in numeric_cols:
    m_broke = broke[col].mean()
    m_ok    = ok[col].mean()
    col_std = df[col].std()
    col_rng = df[col].max() - df[col].min()
    gap     = abs(m_broke - m_ok)
    r_range = gap / col_rng if col_rng > 0 else 0
    r_std   = gap / col_std if col_std > 0 else 0
    does_sep = r_std >= SEPARATION_THRESHOLD
    mark     = "YES" if does_sep else "no"
    print(f"  {col:<18} {m_broke:>12.2f} {m_ok:>10.2f} "
          f"{r_range:>10.3f} {r_std:>8.3f}  {mark}")
    if does_sep:
        separating.append(col)
        gap_in_stds[col] = r_std

print("=" * 76)
print()

# Explicit check for the two obvious candidates
for col in ("odometer_km", "age_years"):
    m_b     = broke[col].mean()
    m_o     = ok[col].mean()
    col_std = df[col].std()
    r_std   = abs(m_b - m_o) / col_std if col_std > 0 else 0
    verdict = "SEPARATES" if col in separating else "does NOT separate"
    print(f"Explicit check -- {col}: broke mean={m_b:.1f}, ok mean={m_o:.1f}, "
          f"gap/std={r_std:.3f} -> {verdict}")
print()

print(f"Columns that separate (gap/std >= {SEPARATION_THRESHOLD}): {separating}")
print()

# ── 3. Two scores: km_since_service alone, and the combined weighted score ────
#
# Both scores: for each contributing column, min-max normalise to [0,1].
# If the broke group has a HIGHER mean the raw normalised value = contribution.
# If the broke group has a LOWER  mean invert (1 - normalised) so high = risky.
# Combined score weights each column by its gap_in_stds; result scaled to 0-100.

def make_score(
    cols: list[str],
    weights: dict[str, float],
    data: "pd.DataFrame",
    broke_df: "pd.DataFrame",
    ok_df: "pd.DataFrame",
) -> "pd.Series":
    """Return a Series of scores 0-100 built from cols, weighted by weights dict."""
    contribs = pd.DataFrame(index=data.index)
    for col in cols:
        lo, hi = data[col].min(), data[col].max()
        normed = (data[col] - lo) / (hi - lo) if hi > lo else pd.Series(0.5, index=data.index)
        if broke_df[col].mean() >= ok_df[col].mean():
            contribs[col] = normed * weights.get(col, 1.0)
        else:
            contribs[col] = (1 - normed) * weights.get(col, 1.0)
    total_weight = sum(weights.get(c, 1.0) for c in cols)
    return (contribs.sum(axis=1) / total_weight * 100).round(1)


if not separating:
    print("No separating columns found -- cannot build a meaningful score.")
else:
    kms_cols    = ["km_since_service"]
    kms_weights = {"km_since_service": gap_in_stds["km_since_service"]}

    df["score_kms"]      = make_score(kms_cols, kms_weights, df, broke, ok)
    df["score_combined"] = make_score(separating, gap_in_stds, df, broke, ok)

    # ── 4. Ranked list (combined score, first 30 rows shown) ─────────────────
    # Build 1-based ranked DataFrames; never mutate them after construction.
    ranked_comb = df.sort_values("score_combined", ascending=False).reset_index(drop=True)
    ranked_comb.index += 1   # 1-based

    ranked_kms = df.sort_values("score_kms", ascending=False).reset_index(drop=True)
    ranked_kms.index += 1    # 1-based

    kms_rank_map  = {row["car_id"]: rank for rank, row in ranked_kms.iterrows()}
    comb_rank_map = {row["car_id"]: rank for rank, row in ranked_comb.iterrows()}

    sep_header = "  ".join(f"{c:>14}" for c in separating)
    print("Cars ranked by combined risk score (highest first):")
    print(f"  {'Rank':<5} {'Car ID':<12} {'Comb':>6}  {'KMS':>6}  "
          f"{'Broke?':>6}  {sep_header}")
    print("  " + "-" * (40 + 16 * len(separating)))
    for rank, row in ranked_comb.iterrows():
        flag     = "  ***" if row["broke_down"] == 1 else ""
        cols_str = "  ".join(f"{row[c]:>14.1f}" for c in separating)
        print(f"  {rank:<5} {row['car_id']:<12} {row['score_combined']:>6.1f}  "
              f"{row['score_kms']:>6.1f}  "
              f"{'YES' if row['broke_down'] else 'no':>6}  {cols_str}{flag}")
    print()

    # ── 5. Validation: both scores at N = 26, 32, 40 ─────────────────────────
    total_broke = int(df["broke_down"].sum())

    for label, score_col, rank_df in [
        ("km_since_service alone", "score_kms",      ranked_kms),
        ("combined score",         "score_combined",  ranked_comb),
    ]:
        avg_b = df[df["broke_down"] == 1][score_col].mean()
        avg_o = df[df["broke_down"] == 0][score_col].mean()
        print(f"[{label}]")
        print(f"  avg score: broke={avg_b:.1f}  ok={avg_o:.1f}  "
              f"(gap={avg_b - avg_o:.1f})")
        for n in (26, 32, 40):
            in_topn = int((rank_df.head(n)["broke_down"] == 1).sum())
            print(f"  broke-down cars in top-{n:<2}: {in_topn} of {total_broke} "
                  f"({100 * in_topn / total_broke:.0f}%)")
    print()

    # ── 6. 80%-rule analysis ──────────────────────────────────────────────────
    RULE_THRESHOLD = int(SERVICE_INTERVAL_KM * WARN_AT_PERCENT / 100)

    rule_flagged   = df[df["km_since_service"] >= RULE_THRESHOLD]
    rule_and_broke = rule_flagged[rule_flagged["broke_down"] == 1]
    rule_and_ok    = rule_flagged[rule_flagged["broke_down"] == 0]

    print(f"80%-rule (km_since_service >= {RULE_THRESHOLD:,}):")
    print(f"  flags {len(rule_flagged)} cars total -- "
          f"{len(rule_and_broke)} broke down, {len(rule_and_ok)} did not")
    print()

    # Cars that broke down but the 80% rule missed
    missed = df[(df["broke_down"] == 1) & (df["km_since_service"] < RULE_THRESHOLD)]
    print(f"Broke-down cars the 80%-rule missed ({len(missed)} cars):")
    print(f"  {'Car ID':<12} {'km_since_svc':>14}  {'avg_daily_km':>13}  "
          f"{'rank(kms)':>10}  {'rank(combined)':>15}")
    print("  " + "-" * 70)
    for _, row in missed.sort_values("km_since_service", ascending=False).iterrows():
        cid = row["car_id"]
        print(f"  {cid:<12} {int(row['km_since_service']):>14,}  "
              f"{int(row['avg_daily_km']):>13,}  "
              f"{kms_rank_map[cid]:>10}  {comb_rank_map[cid]:>15}")
    print()
