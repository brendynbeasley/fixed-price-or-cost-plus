# Technical notes

This is the technical companion to the [README](README.md). It covers the original study, the data, the method, the
full set of test statistics and how to reproduce everything. Every table the scripts write is collected in
[results/FINDINGS.md](results/FINDINGS.md), and the original book is reviewed in
[METHODS_REVIEW.md](METHODS_REVIEW.md).

## The original study

Jean-Jacques Laffont and Jean Tirole, *A Theory of Incentives in Procurement and Regulation*, MIT Press, 1993. The
book has no data. Its core result (from Laffont and Tirole 1986, as summarized in Section 2.2 of the Royal Swedish
Academy of Sciences' 2014 scientific background) is that when a buyer observes cost $`C = \beta - e`$ but not the
firm's type $`\beta`$ or effort $`e`$, the optimal contract pays a lump sum plus a share $`b`$ of any overrun, chosen
from a menu. The most efficient type gets $`b = 0`$ (fixed price) and first-best effort; every other type gets
$`0 < b < 1`$, less effort and a smaller information rent. The headline "number" is therefore a sign: effort falls
and the government's overrun payment rises as $`b`$ rises. The committee's footnote 12 warns that because efficient
firms choose high-powered contracts, cross-contract comparisons are confounded by selection.

## Headline results

Completed NASA and DOE contracts awarded FY2010 to FY2019, initial value of at least $1 million.

| Tier | Contracts | Raised after award | Median growth | Mean growth (winsorized) | Dollar-weighted growth | SD of growth |
|---|---|---|---|---|---|---|
| Fixed price | 2,347 | 55.5% | 1.85% | 29.2% | 25.2% | 99.8 |
| Incentive | 16 | 75.0% | 23.6% | 100.2% | 46.5% | 203.9 |
| Cost-plus | 913 | 61.7% | 8.3% | 70.0% | 63.8% | 168.5 |
| Time and materials | 665 | 50.2% | 0.1% | 48.3% | 38.6% | 143.1 |

Cost-plus minus fixed price, percentage points, standard errors clustered by contractor:

| Fixed effects | Raised | Overspent | Growth | N |
|---|---|---|---|---|
| Agency × year, award type, log size | 1.6 (3.0) | 0.3 (3.1) | 41.0 (11.3) | 3,941 |
| + product or service code | 11.0 (3.2) | 10.3 (3.2) | 32.6 (8.9) | 3,759 |
| + contractor | 12.5 (4.6) | 11.7 (4.8) | 23.6 (11.8) | 2,940 |
| + contractor × product group | 15.4 (5.1) | 13.9 (5.3) | 28.7 (13.4) | 2,811 |

## Data

All from the USAspending award data archive, release dated 6 October 2026,
`https://files.usaspending.gov/award_data_archive/`, downloaded 1 November 2026. Files
`FY{2008..2026}_080_Contracts_Full_20261006.zip` (NASA) and `FY{2008..2026}_089_Contracts_Full_20261006.zip` (DOE),
38 files, roughly 400 MB zipped. Each row is one contract action (award or modification) as reported to the
Federal Procurement Data System. The files are fetched by `src/build_awards.py` into `data/raw/usaspending/`
(ignored by git). The collapsed contract-level file, `data/derived/awards.csv` (one row per contract with initial
value of at least $1 million, 10,035 contracts, 2.9 MB), is committed.

The Boeing figures in the README ($523 million and $288 million of Commercial Crew losses in 2024 and 2023, and
$5.0 billion of 2024 losses on five fixed-price development programs) are quoted from Boeing's Form 10-K for fiscal
2024 and are not computed here.

## Method

Rules fixed before estimating the regressions:

1. **Contract.** One USAspending `contract_award_unique_key`. Initial value $`V_0`$ is the sum of
   `base_and_all_options_value` on modification 0; final value $`V_T`$ is the sum over all actions. Obligations are
   the sum of `federal_action_obligation`.
2. **Sample.** Original award dated FY2010 to FY2019; $`V_0 \ge`$ $1 million; pricing code among the ten ordered
   codes; not an undefinitized (letter) contract; not an indefinite-delivery umbrella record; not a task order under
   NASA's Jet Propulsion Laboratory sponsoring agreements (`NAS703001`, `NNN12AA01C`, `80NM0018D0004`); period of performance ended
   by 30 September 2025; final value above zero.
3. **Tiers.** Fixed price = J, K, M; incentive = L, V; cost-plus = R, U, S; time and materials = Y, Z. Codes A, B,
   T and 1 to 3 (redetermination, level of effort, cost sharing, order-dependent, combination, other) are dropped.
4. **Outcomes.** Raised = $`g > 0.001`$; overspent = obligations above $`1.001\,V_0`$; growth
   $`g = (V_T - V_0)/V_0`$, winsorized at the 1st and 99th percentiles (−0.715 and 8.656).
5. **Estimation.** For contract $`i`$,

```math
\begin{aligned}
y_i = {} & \sum_{k} \beta_k D_{ik} + \gamma \ln V_{0i} + \alpha_{a(i),t(i)} + \delta_{\tau(i)} \\
         & + \mu_{p(i)} + \eta_{f(i)} + \varepsilon_i ,
\end{aligned}
```

   with fixed effects absorbed by alternating projections after dropping singletons, and standard errors clustered by
   contractor parent; the small-sample correction counts the tier dummies and log size, not the absorbed
   effects. $`H_0: \beta_{\text{cost-plus}} = 0`$. In the last specification $`\eta`$ is a contractor-by-product-group
   effect. Product groups are R&D (PSC beginning with A),
   products (numeric PSC) and services (other letters).
6. **Monotonicity.** Excluding time and materials, the tier rank $`r \in \{0,1,2\}`$ replaces the dummies.
7. **Spread.** Brown-Forsythe (median-centered Levene) test on winsorized growth.

Two of these rules were set after a first look at the data, and I note them so a reader can judge. The JPL exclusion
followed from finding that the largest growth rates in the sample were JPL task orders whose recorded value is each
year's funding; the letter-contract exclusion followed from the same inspection. Both were set before any
regression was run. A first version of the JPL rule listed only the two older agreements; orders under the third
(`80NM0018D0004`, from 2018) were added later so that the rule covers every JPL order. That change took the
remaining JPL orders out of the cost-plus tier and lowered the raw cost-plus growth gap.

## Full test statistics

Monotone trend in tier rank (N = 3,276):

| Outcome | Slope per rank | SE | 95% CI | p |
|---|---|---|---|---|
| Raised | 0.71 | 1.51 | [−2.25, 3.67] | 0.64 |
| Overspent | −0.19 | 1.58 | [−3.28, 2.91] | 0.91 |
| Growth | 20.91 | 5.75 | [9.65, 32.18] | 0.0003 |

Spread of growth: SD 99.8 (fixed price) and 168.5 (cost-plus), variance ratio 2.85; Brown-Forsythe statistic 80.3
for fixed price versus cost-plus and 29.7 across all four tiers, both p < 0.001.

The main within-contractor estimate is

```math
\hat\beta_{\text{cost-plus}}^{\,\text{raised}} = 15.4 \;(5.1),\quad 95\%\ \text{CI}\ [5.4,\ 25.4],\quad N = 2{,}811 .
```

Incentive and time-and-materials coefficients, all outcomes and all specifications, are in `results/regressions.csv`.
The incentive tier (16 contracts) has standard errors between 9 and 57 points and is uninformative.

## Reproducing the results

```bash
pip install -r requirements.txt
python src/build_awards.py        # downloads ~400 MB of archives if missing, writes data/derived/awards.csv
python src/power_and_overruns.py  # writes every CSV and PNG in results/
```

The second command alone reproduces every result from the committed `data/derived/awards.csv`.

## Repository layout

| Path | What it is |
|---|---|
| `src/build_awards.py` | Downloads the archives and collapses actions to contracts |
| `src/power_and_overruns.py` | Sample, tier tables, regressions, trend and spread tests, figures |
| `data/derived/awards.csv` | One row per NASA or DOE contract of $1 million or more, FY2008 to FY2026 awards |
| `results/` | All CSVs and PNGs, plus FINDINGS.md |

## References

- Bajari, P. & Tadelis, S. (2001). Incentives versus transaction costs: a theory of procurement contracts. *RAND
  Journal of Economics* 32(3), 387-407.
- The Boeing Company (2025). Form 10-K for the fiscal year ended December 31, 2024.
- Laffont, J.-J. & Tirole, J. (1986). Using cost observation to regulate firms. *Journal of Political Economy*
  94(3), 614-641.
- Laffont, J.-J. & Tirole, J. (1993). *A Theory of Incentives in Procurement and Regulation*. MIT Press.
- Royal Swedish Academy of Sciences (2014). Scientific background on the Sveriges Riksbank Prize in Economic Sciences
  in Memory of Alfred Nobel 2014, Jean Tirole, Market Power and Regulation.
- USAspending.gov, award data archive, Contracts_Full files for agencies 080 and 089, release of 6 October 2026.
