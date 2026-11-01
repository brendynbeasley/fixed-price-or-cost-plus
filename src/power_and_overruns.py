"""Laffont and Tirole (1993) on NASA and Department of Energy contracts: does the power of the
contract predict how far the bill grows after signing?

In the Laffont-Tirole procurement model the government pays a lump sum a plus a share b of any
cost overrun: payment = a + b (C - C_target). b = 0 is a fixed-price contract, b = 1 is cost-plus.
The firm's cost-reducing effort satisfies psi'(e) = 1 - b, so effort falls as b rises, and the
government's overrun payment b (C - C_target) rises in b twice over: it pays a larger share of a
larger overrun. Its variance, b^2 Var(C), rises too.

The test groups every completed NASA and DOE contract awarded in fiscal 2010-2019 with an initial
value of at least $1 million by its FPDS pricing type, ordered by the share of overruns the
government pays, and compares growth in the contract's value after award.

Extension (Bajari and Tadelis 2001, and Laffont-Tirole's own self-selection result): the pricing
type is chosen, not assigned. Cost-plus is used for harder, less predictable work, and the menu of
contracts sorts firms by type. The same comparison is rerun within product-and-service code,
within contractor, and within contractor and product code.

Input: data/derived/awards.csv (built by src/build_awards.py from USAspending archives).
Run from the repository root:
    python src/power_and_overruns.py
"""

from pathlib import Path

import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

# Fixed-effect dummies are collinear with each other (never with the contract-type terms), which
# statsmodels handles with a pseudo-inverse; silence its warning about that.
warnings.filterwarnings("ignore", message="The design matrix is rank-deficient")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "derived" / "awards.csv"
OUT = ROOT / "results"

AWARD_FROM, AWARD_TO = "2009-10-01", "2019-09-30"  # fiscal 2010-2019 awards
COMPLETED_BY = "2025-09-30"                         # performance period must end by FY2025
MIN_CEILING = 1_000_000                             # initial value incl. options; small buys are noise
WINSOR = 0.01                                       # trim growth at the 1st and 99th percentiles
BIG_CONTRACT = 500_000_000                          # threshold for the table of named contracts
# NASA's sponsoring contracts with Caltech for the Jet Propulsion Laboratory, a federally funded
# research center (NAS7-03001 to 2012, NNN12AA01C to 2018, 80NM0018D0004 from 2018). Task orders
# under them record each year's funding as the order's value, so their "growth" is a funding
# schedule, not a change in price.
LAB_PARENTS = {"NAS703001", "NNN12AA01C", "80NM0018D0004"}
LETTER_CONTRACT = {"A", "B"}  # FPDS undefinitized-action codes: price not yet agreed at award

# FPDS "type of contract pricing" codes, ordered by the share of a cost overrun the government pays.
# Fixed price (J firm fixed price, K with economic price adjustment, M with award fee): the
# contractor keeps every saved dollar and pays every extra one, b = 0. Incentive (L fixed-price
# incentive, V cost-plus-incentive-fee): overruns are split by a negotiated share ratio, 0 < b < 1.
# Cost-plus (R award fee, U fixed fee, S cost with no fee): the government reimburses allowable
# cost, b = 1. Time and materials (Y) and labor hours (Z) pay per hour worked, also b near 1.
TIERS = {
    "J": "Fixed price", "K": "Fixed price", "M": "Fixed price",
    "L": "Incentive", "V": "Incentive",
    "R": "Cost-plus", "U": "Cost-plus", "S": "Cost-plus",
    "Y": "Time and materials", "Z": "Time and materials",
}
TIER_ORDER = ["Fixed price", "Incentive", "Cost-plus", "Time and materials"]
POWER_RANK = {"Fixed price": 0, "Incentive": 1, "Cost-plus": 2, "Time and materials": 2}
CODE_NAMES = {
    "J": "Firm fixed price", "K": "Fixed price, economic price adjustment", "M": "Fixed price award fee",
    "L": "Fixed price incentive", "V": "Cost plus incentive fee", "R": "Cost plus award fee",
    "U": "Cost plus fixed fee", "S": "Cost, no fee", "Y": "Time and materials", "Z": "Labor hours",
}


def load():
    a = pd.read_csv(DATA, dtype={"pricing": str, "psc": str, "naics": str, "research": str,
                                 "competed": str, "award_type": str, "last_pricing": str,
                                 "undefinitized": str, "parent_piid": str})
    print(f"loaded {DATA.relative_to(ROOT)}: {len(a):,} contracts")
    return a


def build_sample(a):
    steps = [
        ("original award in FY2010-FY2019", (a["award_date"] >= AWARD_FROM) & (a["award_date"] <= AWARD_TO)),
        (f"initial value of at least ${MIN_CEILING:,}", a["initial_ceiling"] >= MIN_CEILING),
        ("pricing type is one of the ten ordered codes", a["pricing"].isin(TIERS)),
        ("price agreed at award (not a letter contract)", ~a["undefinitized"].isin(LETTER_CONTRACT)),
        ("not a Jet Propulsion Laboratory task order", ~a["parent_piid"].isin(LAB_PARENTS)),
        (f"performance period ended by {COMPLETED_BY}", a["end_date"].notna() & (a["end_date"] <= COMPLETED_BY)),
        ("value not cancelled to zero (final value > 0)", a["final_ceiling"] > 0),
    ]
    keep = pd.Series(True, index=a.index)
    for label, cond in steps:
        dropped = (keep & ~cond).sum()
        keep &= cond
        print(f"  keep if {label}: dropped {dropped:,}, {keep.sum():,} remain")
    s = a[keep].copy()
    s["tier"] = s["pricing"].map(TIERS)
    s["power_rank"] = s["tier"].map(POWER_RANK)
    s["award_fy"] = pd.to_datetime(s["award_date"]).dt.year + (pd.to_datetime(s["award_date"]).dt.month >= 10)
    s["contractor"] = s["parent"].fillna(s["recipient"]).fillna("UNKNOWN").str.upper().str.strip()
    s["psc4"] = s["psc"].fillna("NONE").str[:4]
    s["psc_group"] = s["psc"].fillna("N").str[:1].map(
        lambda c: "R&D" if c == "A" else ("Product" if c.isdigit() else "Service"))
    s["growth"] = s["final_ceiling"] / s["initial_ceiling"] - 1
    lo, hi = s["growth"].quantile([WINSOR, 1 - WINSOR])
    s["growth_w"] = s["growth"].clip(lo, hi)
    s["raised"] = (s["growth"] > 0.001).astype(int)
    s["overspent"] = (s["final_obligated"] > s["initial_ceiling"] * 1.001).astype(int)
    s["log_size"] = np.log(s["initial_ceiling"])
    print(f"sample: {len(s):,} completed contracts, {s['contractor'].nunique():,} contractors; "
          f"growth winsorized at {lo:.3f} and {hi:.3f}")
    return s


def tier_table(s, by):
    g = s.groupby(by)
    t = pd.DataFrame({
        "contracts": g.size(),
        "initial_value_bn": g["initial_ceiling"].sum() / 1e9,
        "final_value_bn": g["final_ceiling"].sum() / 1e9,
        "share_raised_pct": 100 * g["raised"].mean(),
        "share_overspent_pct": 100 * g["overspent"].mean(),
        "mean_growth_pct": 100 * g["growth_w"].mean(),
        "median_growth_pct": 100 * g["growth"].median(),
        "p90_growth_pct": 100 * g["growth"].quantile(0.9),
        "sd_growth_pct": 100 * g["growth_w"].std(),
    })
    t["dollar_growth_pct"] = 100 * (t["final_value_bn"] / t["initial_value_bn"] - 1)
    return t


TIER_TERMS = [t for t in TIER_ORDER[1:]]


def fit(formula, s):
    return smf.ols(formula, data=s).fit(cov_type="cluster", cov_kwds={"groups": s["contractor"]})


def absorb(d, cols, fes, tol=1e-10, max_iter=500):
    """Sweep out several sets of fixed effects by alternating projections (repeated group demeaning).

    Singleton groups carry no within information, so they are dropped first, repeatedly, until
    every remaining observation shares each fixed-effect group with at least one other."""
    d = d.copy()
    while True:
        single = np.zeros(len(d), dtype=bool)
        for fe in fes:
            single |= d.groupby(fe)[fe].transform("size").values == 1
        if not single.any():
            break
        d = d[~single]
    x = d[cols].astype(float).copy()
    for _ in range(max_iter):
        before = x.values.copy()
        for fe in fes:
            x = x - x.groupby(d[fe].values).transform("mean")
        if np.abs(x.values - before).max() < tol:
            break
    return d, x


def fe_regression(d, outcome, fes, spec):
    for tier in TIER_TERMS:
        d["T_" + tier] = (d["tier"] == tier).astype(float)
    regs = ["T_" + t for t in TIER_TERMS if d["T_" + t].sum() > 0] + ["log_size"]
    used, x = absorb(d, [outcome] + regs, fes)
    m = sm.OLS(x[outcome].values, x[regs].values).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(used["contractor"])[0]})
    ci = m.conf_int()
    rows = []
    for i, name in enumerate(regs[:-1]):
        rows.append(dict(spec=spec, outcome=outcome, tier=name[2:], coef=m.params[i], se=m.bse[i],
                         ci_lo=ci[i, 0], ci_hi=ci[i, 1], p=m.pvalues[i], n=len(used),
                         clusters=used["contractor"].nunique()))
    return rows


def regressions(s):
    s = s.copy()
    s["agency_fy"] = s["agency"] + s["award_fy"].astype(str)
    s["contractor_group"] = s["contractor"] + "|" + s["psc_group"]
    base = ["agency_fy", "award_type"]
    specs = {
        "1 Agency x year": base,
        "2 + product code": base + ["psc4"],
        "3 + contractor": base + ["psc4", "contractor"],
        "4 contractor x product group": base + ["psc4", "contractor_group"],
    }
    rows = []
    for outcome in ["raised", "overspent", "growth_w"]:
        d = s.copy()
        d[outcome] = 100 * d[outcome]
        for spec, fes in specs.items():
            r = fe_regression(d, outcome, fes, spec)
            rows += r
            cp = [x for x in r if x["tier"] == "Cost-plus"][0]
            print(f"  {outcome:9s} {spec:30s} N={cp['n']:5d}  cost-plus minus fixed price "
                  f"{cp['coef']:7.2f} (se {cp['se']:.2f})")
    return pd.DataFrame(rows)


def power_trend(s):
    """Monotonicity: one slope on the ordinal power rank (0 fixed, 1 incentive, 2 cost-plus)."""
    d = s[s["tier"] != "Time and materials"].copy()
    rows = []
    for outcome in ["raised", "overspent", "growth_w"]:
        d["y"] = 100 * d[outcome]
        m = fit("y ~ power_rank + log_size + C(award_type) + C(agency):C(award_fy)", d)
        lo, hi = m.conf_int().loc["power_rank"]
        rows.append(dict(outcome=outcome, slope_per_rank=m.params["power_rank"], se=m.bse["power_rank"],
                         ci_lo=lo, ci_hi=hi, p=m.pvalues["power_rank"], n=int(m.nobs)))
    return pd.DataFrame(rows)


def variance_test(s):
    groups = [s.loc[s["tier"] == t, "growth_w"].values for t in TIER_ORDER]
    w, p = stats.levene(*groups, center="median")
    fp = s.loc[s["tier"] == "Fixed price", "growth_w"]
    cp = s.loc[s["tier"] == "Cost-plus", "growth_w"]
    w2, p2 = stats.levene(fp, cp, center="median")
    return pd.DataFrame([
        dict(test="Brown-Forsythe, all four tiers", statistic=w, p=p, sd_fixed_pct=100 * fp.std(),
             sd_costplus_pct=100 * cp.std(), variance_ratio=(cp.var() / fp.var())),
        dict(test="Brown-Forsythe, fixed price vs cost-plus", statistic=w2, p=p2, sd_fixed_pct=100 * fp.std(),
             sd_costplus_pct=100 * cp.std(), variance_ratio=(cp.var() / fp.var())),
    ])


def named_contracts(a):
    """Largest contracts awarded FY2010-FY2019, finished or not, with growth to date (JPL orders excluded)."""
    w = a[(a["award_date"] >= AWARD_FROM) & (a["award_date"] <= AWARD_TO) &
          (a["initial_ceiling"] >= BIG_CONTRACT) & a["pricing"].isin(TIERS) &
          ~a["parent_piid"].isin(LAB_PARENTS) & (a["final_ceiling"] > 0)].copy()  # drop awards cancelled or replaced (value written down to zero)
    w["pricing_type"] = w["pricing"].map(CODE_NAMES)
    w["growth_pct"] = 100 * (w["final_ceiling"] / w["initial_ceiling"] - 1)
    w["obligated_pct_of_initial"] = 100 * w["final_obligated"] / w["initial_ceiling"]
    w["initial_value_m"] = w["initial_ceiling"] / 1e6
    w["final_value_m"] = w["final_ceiling"] / 1e6
    w["obligated_m"] = w["final_obligated"] / 1e6
    w["description"] = w["description"].fillna("").str.slice(0, 110)
    cols = ["agency", "piid", "recipient", "parent", "pricing", "pricing_type", "award_date", "end_date",
            "initial_value_m", "final_value_m", "obligated_m", "growth_pct", "obligated_pct_of_initial",
            "n_mods", "description"]
    return w.sort_values("initial_ceiling", ascending=False)[cols]


def worked_example(s):
    """The median-sized completed cost-plus and fixed-price contracts, for the README's arithmetic."""
    rows = []
    for tier in ["Fixed price", "Cost-plus"]:
        t = s[s["tier"] == tier].sort_values("initial_ceiling")
        r = t.iloc[len(t) // 2]
        rows.append(dict(tier=tier, piid=r["piid"], recipient=r["recipient"], agency=r["agency"],
                         initial_value=r["initial_ceiling"], final_value=r["final_ceiling"],
                         obligated=r["final_obligated"], growth_pct=100 * r["growth"]))
    return pd.DataFrame(rows)


def figure_tiers(t):
    t = t.loc[TIER_ORDER]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    colors = ["#2b6cb0", "#6b8fc4", "#c05621", "#dd8f5a"]
    axes[0].bar(range(4), t["share_raised_pct"], color=colors)
    axes[0].set_title("Share of contracts whose value was raised after award", fontsize=10)
    axes[0].set_ylabel("percent of contracts")
    axes[1].bar(range(4), t["mean_growth_pct"], color=colors)
    axes[1].set_title("Average growth in contract value after award", fontsize=10)
    axes[1].set_ylabel("percent of initial value (winsorized mean)")
    for ax, col in zip(axes, ["share_raised_pct", "mean_growth_pct"]):
        ax.set_xticks(range(4))
        ax.set_xticklabels([f"{x.replace(' and ', ' & ')}\n(N = {n:,})" for x, n in zip(TIER_ORDER, t["contracts"])],
                           fontsize=8)
        for i, v in enumerate(t[col]):
            ax.text(i, v, f"{v:.0f}%", ha="center", va="bottom", fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Completed NASA and DOE contracts awarded FY2010-2019, by who pays an overrun", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "growth_by_contract_type.png", dpi=150)
    plt.close(fig)


def figure_ladder(reg):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    panels = [("raised", "Value raised after award\n(percentage points)"),
              ("growth_w", "Growth in contract value\n(percentage points of initial value)")]
    for ax, (outcome, label) in zip(axes, panels):
        d = reg[(reg["outcome"] == outcome) & (reg["tier"] == "Cost-plus")].reset_index(drop=True)
        y = np.arange(len(d))[::-1]
        ax.errorbar(d["coef"], y, xerr=[d["coef"] - d["ci_lo"], d["ci_hi"] - d["coef"]], fmt="o",
                    color="#c05621", capsize=4)
        ax.axvline(0, color="grey", lw=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels([f"{s[2:]}\n(N = {n:,})" for s, n in zip(d["spec"], d["n"])], fontsize=8)
        ax.set_xlabel(label, fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Cost-plus minus fixed price, comparing ever more similar contracts (95% CI)", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "within_contractor_ladder.png", dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    a = load()
    s = build_sample(a)

    t = tier_table(s, "tier").loc[TIER_ORDER]
    t.round(2).to_csv(OUT / "growth_by_tier.csv")
    print("\nBy contract power:\n" + t.round(1).to_string())
    c = tier_table(s, "pricing")
    c.insert(0, "pricing_type", c.index.map(CODE_NAMES))
    c.insert(1, "tier", c.index.map(TIERS))
    c.sort_values("contracts", ascending=False).round(2).to_csv(OUT / "growth_by_pricing_code.csv")
    ta = tier_table(s, ["agency", "tier"]).round(2)
    ta.to_csv(OUT / "growth_by_agency_tier.csv")
    tg = tier_table(s, ["psc_group", "tier"]).round(2)
    tg.to_csv(OUT / "growth_by_category_tier.csv")
    print("\nBy what is bought:\n" + tg[["contracts", "share_raised_pct", "mean_growth_pct"]].round(1).to_string())

    print("\nRegressions (cluster by contractor):")
    reg = regressions(s)
    reg.round(4).to_csv(OUT / "regressions.csv", index=False)
    trend = power_trend(s)
    trend.round(4).to_csv(OUT / "power_trend.csv", index=False)
    print(trend.round(3).to_string(index=False))
    var = variance_test(s)
    var.round(4).to_csv(OUT / "variance_test.csv", index=False)
    print(var.round(3).to_string(index=False))

    names = named_contracts(a)
    names.round(1).to_csv(OUT / "named_contracts.csv", index=False)
    print(f"\nnamed contracts over ${BIG_CONTRACT/1e6:,.0f}M: {len(names)}, of which cost-plus "
          f"{names['pricing'].map(TIERS).eq('Cost-plus').sum()}")
    worked_example(s).round(2).to_csv(OUT / "worked_example.csv", index=False)

    summary = pd.DataFrame([dict(
        contracts=len(s), contractors=s["contractor"].nunique(), initial_value_bn=s["initial_ceiling"].sum() / 1e9,
        nasa=(s["agency"] == "NASA").sum(), doe=(s["agency"] == "DOE").sum(),
        share_fixed_price_pct=100 * (s["tier"] == "Fixed price").mean(),
        share_cost_plus_pct=100 * (s["tier"] == "Cost-plus").mean(),
        winsor_lo=s["growth"].quantile(WINSOR), winsor_hi=s["growth"].quantile(1 - WINSOR))])
    summary.round(3).to_csv(OUT / "sample_summary.csv", index=False)

    figure_tiers(t)
    figure_ladder(reg)
    print(f"\nwrote CSVs and PNGs to {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
