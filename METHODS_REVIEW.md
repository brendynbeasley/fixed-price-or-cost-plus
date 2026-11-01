# Methods review: Laffont and Tirole (1993)

**Paper.** Jean-Jacques Laffont and Jean Tirole, *A Theory of Incentives in Procurement and Regulation*.
Cambridge, MA: MIT Press, 1993 (ISBN 978-0-262-12174-3).

**Statistical focus.** The book is theory, so its "statistics" are its formal results. This review concentrates on
the two that carry the procurement chapters and that the repository tests: (1) the optimal payment rule is a menu of
linear cost-sharing contracts in which the most efficient firm gets a fixed-price contract and every other type
shares overruns with the government, so that effort falls as the government's share of overruns rises; (2) the
self-selection property, by which more efficient firms choose higher-powered contracts.

**Review standard.** Internal consistency of the formal results, explicitness of assumptions, and the testability of
the predictions with data that exist.

**What was read.** I did not read the book itself, which is not freely available. I read the full text of the
Royal Swedish Academy of Sciences' *Scientific Background on the Sveriges Riksbank Prize in Economic Sciences in
Memory of Alfred Nobel 2014, "Jean Tirole: Market Power and Regulation"* (13 October 2014), whose Section 2 presents
the Laffont-Tirole model, the book's chapters on quality, access pricing and dynamics, and the empirical work the
committee cites; the Academy's 2014 press release; and the Toulouse School of Economics tribute to Laffont. Every
statement below about the book's content comes from those sources, and page references are to the Scientific
Background.

---

## Methods summary

The book is a unified principal-agent treatment of regulation and procurement. The government (principal) buys a
good, or regulates a monopolist, whose cost is

```math
C = \beta - e,
```

where $`\beta`$ is the firm's efficiency type, known only to the firm, and $`e`$ is unobserved cost-reducing effort
with convex disutility $`\psi(e)`$. Realized cost $`C`$ is observed and can be contracted on. Public funds carry a
shadow cost $`1+\lambda`$ with $`\lambda>0`$, so rents left to the firm are socially costly. Using the revelation
principle, the authors derive the optimal mechanism, which can be written as a menu of contracts: the firm announces
its expected cost $`c^a`$ and is paid a lump sum plus a share $`b(c^a)`$ of any overrun (Scientific Background, p. 7).
The most efficient type receives $`b=0`$, a fixed-price contract, and supplies first-best effort,
$`\psi'(e^*)=1`$; all other types receive $`0<b<1`$, supply less than first-best effort and, except the least
efficient, earn an information rent (pp. 7-8). The book extends this core to multi-product firms and Ramsey pricing,
unverifiable quality (Chapter 4), access pricing (Chapter 5), dynamics with limited commitment and the ratchet effect
(Chapters 1, 9, 10 and 16), franchise auctions, and regulatory capture.

Several of the standard reporting headings do not apply to a theory book, and I say so under each.

### Research design
Deductive mechanism design. No data are collected or analyzed in the parts of the book described by the sources I
read.

### Sampling strategy
Not applicable; there is no sample.

### Sample size
Not applicable.

### Inclusion and exclusion criteria
Not applicable. The analogous choice is the class of environments: risk-neutral parties (so a random cost disturbance
can be added without changing results, footnote 8, p. 7), a type distribution with the monotone hazard-rate property,
and voluntary participation.

### Independent and dependent variables
In the model, the contract's power ($`1-b`$, the share of an overrun borne by the firm) is the policy variable, and
effort, realized cost and the firm's rent are the outcomes. The type $`\beta`$ is the unobserved confounder, which
matters for any empirical use (see Interpretation notes).

### Statistical methods
None. The "methods" are optimization under incentive-compatibility and participation constraints.

### Reported effect sizes
None in the empirical sense. The formal results are qualitative signs and orderings (for example, $`b=0`$ at the
top, effort strictly below first best elsewhere).

### Confidence intervals
Not applicable.

### p-values
Not applicable.

### Missing data treatment
Not applicable.

### Stated limitations
The Scientific Background records the main ones the authors and committee acknowledge: the optimal static mechanism
is complex and needs knowledge of the type distribution (p. 9); with short-run contracts the regulator cannot commit,
which produces the ratchet effect and makes full separation of types impossible (pp. 13-14); with renegotiable
long-run contracts full separation is feasible but not optimal (pp. 15-16); and empirical comparisons of contract
types are subject to selection, because more efficient firms choose more high-powered contracts (footnote 12, p. 9).

---

## Statistics extraction table

| Statistic | Value and unit | Source location | What it measures | What it does not establish |
|---|---|---|---|---|
| Optimal transfer rule | Lump sum $`a(c^a)`$ plus share $`b(c^a)`$ of the overrun $`C-c^a`$ | Scientific Background, Sec. 2.2, p. 7 | That the optimal mechanism with observed cost can be implemented as a menu of linear cost-sharing contracts | That real procurement contracts are written this way, or what values of $`b`$ are optimal in any market |
| Share for the most efficient type | $`b=0`$ (fixed price) | Sec. 2.2, p. 7 | "No distortion at the top": the best type bears all of its cost and supplies first-best effort | That fixed-price contracts are optimal for typical firms; every other type gets $`b>0`$ |
| Effort of other types | $`e<e^*`$ for all $`\beta>\underline{\beta}`$ | Sec. 2.2, property S2, p. 8 | The rent-extraction versus cost-reduction trade-off | The size of the effort shortfall in dollars |
| Information rent | $`U>0`$ for all but the least efficient type | Sec. 2.2, property S3, p. 8 | The cost of high-powered incentives when types are hidden | How large rents are in practice |
| Self-selection | Truthful announcement of $`c^a`$ | Sec. 2.2, property S1, p. 8 | Firms sort into contracts by type | That observed contract choice can be treated as exogenous; it implies the reverse |
| Quality and power | Low-powered schemes optimal for experience goods when quality matters | Book Ch. 4, per Sec. 2.3, p. 11 | When cost-plus can be the right choice | Any magnitude, or the result for search goods, where it does not hold |
| No-separation result | No period-1 mechanism fully separates types under short-run contracting | Laffont and Tirole (1988a) and book Chs. 9-10, per Sec. 2.4, p. 14 | The ratchet effect | How fast information is revealed in real regulatory cycles |
| Simple two-contract menu (Rogerson 2003, cited) | At least three quarters of the optimal mechanism's surplus, under quadratic disutility and uniform types | Sec. 2.2, p. 9 | That a fixed-price versus cost-reimbursement menu can approximate the optimum | That the bound holds outside those functional forms; it is a later paper's result, not the book's |

---

## Interpretation notes

- The model's sharpest testable implication is directional: holding the firm's type fixed, a higher government share
  of overruns lowers effort and raises realized cost. The committee's own note (footnote 12, p. 9) warns that
  comparisons across contract types confound this with selection, since efficient firms choose high-powered
  contracts. Both forces push observed cost growth the same way, so a raw gap between fixed-price and cost-plus
  contracts is an upper bound on the incentive effect, not an estimate of it.
- The model takes the good as given. Real contract types are also chosen for what is bought (Bajari and Tadelis 2001
  argue cost-plus is chosen for complex, uncertain projects where fixed-price renegotiation is costly). That is an
  additional confounder the book's menu does not address.
- The book's empirical support, as presented by the committee, is indirect and comes from other authors: price-cap
  telephone companies offering lower rates (Mathios and Rogers 1989) and reporting higher profits (Ai and Sappington
  2002), and a structural model of French urban transit (Gagnepain and Ivaldi 2002). These are consistent with the
  theory but are not tests of the optimal menu itself.
- The reporting gap here is the usual one for theory: there is no calibration in the sources I read that would let a
  reader translate $`b`$ into dollars. That is a limit on testability, not an error.
- No published correction or documented analytical error concerning the results reviewed here came up in the
  sources I read.

---

## Unanswered questions

- What share of overruns do real incentive contracts actually assign to the firm, and how does that compare with the
  optimal $`b`$ implied by plausible type distributions?
- How much of the cost difference between contract types is effort and how much is selection on type or on the
  difficulty of the work?
- Do agencies offer anything resembling a menu, or is contract type set by regulation and custom before the firm
  speaks?
- How does the ratchet effect show up in follow-on procurement, where the same contractor's past costs inform the
  next price?

---

## Items requiring expert verification

- The chapter attributions above (Chapter 4 on quality, Chapter 5 on access pricing, Chapters 1, 9, 10 and 16 on
  dynamics) are taken from the Scientific Background and should be checked against the book's table of contents.
- Whether the book itself presents any numerical calibration or empirical illustration of defense or space
  procurement that the committee did not summarize.
- Whether FPDS pricing-type codes map onto the model's $`b`$ as cleanly as the repository assumes, in particular for
  fixed-price incentive and cost-plus-incentive-fee contracts, whose share ratios are negotiated contract by contract.

---

## How this repository relates

The repository does not reproduce anything in the book, which has no data to reproduce. It takes the
direction-of-effect prediction and the selection caveat above and confronts them with completed NASA and Department
of Energy contracts from USAspending, comparing growth in contract value after award across pricing types, first
across all contracts and then within product code and within contractor. See [README.md](README.md) and
[TECHNICAL.md](TECHNICAL.md).
