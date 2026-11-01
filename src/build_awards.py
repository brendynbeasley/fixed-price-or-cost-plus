"""Build one row per NASA and Department of Energy contract from USAspending transaction files.

Every federal contract action (the award itself and each later modification) is a row in the
USAspending award data archive. This script reads the yearly "Contracts_Full" archives for NASA
(agency code 080) and the Department of Energy (089), fiscal 2008 to 2026, and collapses them to
one row per contract with:

    initial ceiling : base-and-all-options value written into the original award (modification 0)
    final ceiling   : the same value after every later modification has been added
    final obligated : dollars actually obligated over the life of the contract
    pricing type    : the FPDS "type of contract pricing" code on the original award

The archives are about 20 MB each zipped (38 files, roughly 400 MB). They are fetched into
data/raw/usaspending/ if missing and are not committed. The output, data/derived/awards.csv, is
committed so the analysis script runs offline.

Run from the repository root:
    python src/build_awards.py
"""

from pathlib import Path
import time
import urllib.request
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "usaspending"
OUT = ROOT / "data" / "derived" / "awards.csv"

ARCHIVE_URL = "https://files.usaspending.gov/award_data_archive/"
ARCHIVE_DATE = "20261006"           # the monthly archive release used here (6 October 2026)
FISCAL_YEARS = range(2008, 2027)    # FY2008 is the first year with a full modern record for both agencies
AGENCIES = {"080": "NASA", "089": "DOE"}
MIN_INITIAL_CEILING = 1_000_000     # small buys are noise; keeps the committed file small
DESCRIBE_FROM = 500_000_000         # keep the free-text description only for contracts this large

COLUMNS = [
    "contract_award_unique_key", "award_id_piid", "parent_award_id_piid", "modification_number",
    "federal_action_obligation", "base_and_all_options_value", "action_date",
    "period_of_performance_start_date", "period_of_performance_current_end_date",
    "awarding_sub_agency_name", "recipient_name", "recipient_parent_name", "award_or_idv_flag",
    "award_type_code",
    "type_of_contract_pricing_code", "product_or_service_code", "naics_code",
    "extent_competed_code", "number_of_offers_received", "research_code",
    "prime_award_base_transaction_description", "undefinitized_action_code",
]
NUMERIC = ["federal_action_obligation", "base_and_all_options_value"]

# Parent names recorded as full legal titles, shortened (by prefix) to the name the company trades under.
PARENT_PREFIX_ALIASES = {
    "L'AIR LIQUIDE SOCIETE ANONYME": "L'AIR LIQUIDE S.A.",
}


def fetch(name):
    """Download one archive into data/raw/usaspending/ unless it is already there."""
    path = RAW / name
    if path.exists():
        return path
    RAW.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    print(f"  downloading {name}")
    urllib.request.urlretrieve(ARCHIVE_URL + name, tmp)
    tmp.rename(path)
    time.sleep(2)
    return path


def read_archive(path, agency):
    frames = []
    with zipfile.ZipFile(path) as z:
        for member in z.namelist():
            if not member.endswith(".csv"):
                continue
            df = pd.read_csv(z.open(member), usecols=COLUMNS, dtype=str, low_memory=False)
            frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["agency"] = agency
    for prefix, short in PARENT_PREFIX_ALIASES.items():
        hit = df["recipient_parent_name"].fillna("").str.startswith(prefix)
        df.loc[hit, "recipient_parent_name"] = short
    return df


def is_base(mod):
    """Modification '0' (sometimes written '00' or '0000') is the original award."""
    m = mod.fillna("").str.strip().str.lstrip("0")
    return m == ""


def collapse(tx):
    tx = tx.sort_values(["contract_award_unique_key", "action_date"])
    tx["is_base"] = is_base(tx["modification_number"])

    base = tx[tx["is_base"]]
    first = base.groupby("contract_award_unique_key").agg(
        piid=("award_id_piid", "first"),
        parent_piid=("parent_award_id_piid", "first"),
        agency=("agency", "first"),
        sub_agency=("awarding_sub_agency_name", "first"),
        award_date=("action_date", "min"),
        start_date=("period_of_performance_start_date", "first"),
        recipient=("recipient_name", "first"),
        parent=("recipient_parent_name", "first"),
        award_or_idv=("award_or_idv_flag", "first"),
        award_type=("award_type_code", "first"),
        pricing=("type_of_contract_pricing_code", "first"),
        psc=("product_or_service_code", "first"),
        naics=("naics_code", "first"),
        competed=("extent_competed_code", "first"),
        offers=("number_of_offers_received", "first"),
        research=("research_code", "first"),
        description=("prime_award_base_transaction_description", "first"),
        undefinitized=("undefinitized_action_code", "first"),
        initial_ceiling=("base_and_all_options_value", "sum"),
        initial_obligated=("federal_action_obligation", "sum"),
    )
    totals = tx.groupby("contract_award_unique_key").agg(
        final_ceiling=("base_and_all_options_value", "sum"),
        final_obligated=("federal_action_obligation", "sum"),
        n_actions=("action_date", "size"),
        last_action=("action_date", "max"),
        end_date=("period_of_performance_current_end_date", "last"),
        last_pricing=("type_of_contract_pricing_code", "last"),
    )
    awards = first.join(totals, how="inner")
    awards["n_mods"] = awards["n_actions"] - 1
    return awards.reset_index()


def main():
    frames = []
    for fy in FISCAL_YEARS:
        for code, agency in AGENCIES.items():
            name = f"FY{fy}_{code}_Contracts_Full_{ARCHIVE_DATE}.zip"
            df = read_archive(fetch(name), agency)
            print(f"loaded {name}: {len(df):,} contract actions")
            frames.append(df)
    tx = pd.concat(frames, ignore_index=True)
    print(f"all actions: {len(tx):,}")

    n0 = len(tx)
    tx = tx.drop_duplicates()
    print(f"dropped {n0 - len(tx):,} exact duplicate rows")

    awards = collapse(tx)
    print(f"contracts whose original award falls in FY{FISCAL_YEARS[0]}-FY{FISCAL_YEARS[-1]}: {len(awards):,}")
    no_base = tx.loc[~tx["contract_award_unique_key"].isin(awards["contract_award_unique_key"]),
                     "contract_award_unique_key"].nunique()
    print(f"dropped {no_base:,} contracts whose original award predates the archive (no modification 0)")

    # Indefinite-delivery vehicles are umbrella agreements; their "ceiling" is a cap on future orders,
    # not a price for work. The orders placed under them are kept as their own contracts.
    idv = awards["award_or_idv"].fillna("").str.upper().eq("IDV")
    print(f"dropped {idv.sum():,} indefinite-delivery umbrella records (orders under them are kept)")
    awards = awards[~idv]

    keep = awards["initial_ceiling"] >= MIN_INITIAL_CEILING
    print(f"dropped {(~keep).sum():,} contracts with initial ceiling under ${MIN_INITIAL_CEILING:,}")
    awards = awards[keep].copy()
    awards.loc[awards["initial_ceiling"] < DESCRIBE_FROM, "description"] = ""
    awards["description"] = awards["description"].fillna("").str.slice(0, 110)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    awards.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(awards):,} contracts")


if __name__ == "__main__":
    main()
