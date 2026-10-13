"""
Euronext Equity & Index Derivatives: delayed post-trade analysis
================================================================
Reads manually downloaded Euronext MiFIR/MiFID II delayed post-trade CSVs,
validates them, combines them, and describes published-record activity,
instrument concentration, notional coverage and market-mechanism patterns.
Tables are then exported for a Power BI report.

Note: these are published report rows, not guaranteed unique economic trades.
Nothing here is a trading signal, liquidity model or market-power analysis.
"""

# =============================================================================
# SECTION 1: SETUP AND SETTINGS
# =============================================================================

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# --- Folders ----------------------------------------------------------------
# Paths are built relative to this script, so the project runs on any machine.
# Expected layout:
#   project/
#     eid_analysis.py
#     data/raw/        <- daily Euronext CSVs go here (not committed to Git)
#     output/tables/   <- created automatically
#     output/figures/  <- created automatically


from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Project folders
project_folder = Path(r"C:\Users\sudha\Desktop\Python Projects")

raw_data_folder = project_folder / "data" / "raw"
tables_folder = project_folder / "output" / "tables"
figures_folder = project_folder / "output" / "figures"

# Path objects only describe where files live. They do not read or move data.
# mkdir() creates the output folders if they are missing.

tables_folder.mkdir(parents=True, exist_ok=True)
figures_folder.mkdir(parents=True, exist_ok=True)

# --- CSV reading settings ---------------------------------------------------
# Applied to every Euronext source file.
#   skiprows=1    -> the first line of each file is not the column header
#   sep=","       -> comma-separated
#   dtype="string"-> read everything as text first, so no value is silently
#                    converted (IDs keep their form, blanks stay missing).
#                    Numbers are converted later, on purpose, in Section 3.


csv_setting = {
    "skiprows": 1,
    "sep": ",",
    "dtype": "string",
}

# --- Project purpose --------------------------------------------------------

project_title = (
    "Euronext Equity & Index Derivatives "
    "Published Post-Trade Activity and Data Quality"
)

main_business_question = (
    "How do published post-trade records vary across dates, hours, "
    "instruments, and selected data-quality dimensions in Euronext "
    "Equity & Index Derivatives data?"
)

supporting_questions = {
    "trading_activity": (
        "How does the number of published post-trade records vary across "
        "the trading day, and how does this pattern differ by date?"
    ),
    "instrument_concentration": (
        "How concentrated are published post-trade records among the most "
        "active instruments, and does the concentration change by date?"
    ),
    "missing_notional": (
        "Are missing MifidNotionalAmount values broadly distributed or "
        "concentrated in particular instruments, dates, or patterns?"
    ),
    "market_mechanism": (
        "Where and when do the observed market-mechanism codes appear, "
        "especially codes 4, 5 and 8, without assuming their cause?"
    ),
}

# Quick confirmation that paths and settings are what we expect
print("Raw-data folder:", raw_data_folder)
print("Tables folder:  ", tables_folder)
print("Figures folder: ", figures_folder)
print("CSV settings:   ", csv_setting)
print("Main question:  ", main_business_question)

# =============================================================================
# SECTION 2: DATA IMPORT PIPELINE
# =============================================================================
# Step 1: define what a valid file looks like
# Step 2: write two small reusable functions (validate, load)
# Step 3: loop over every CSV in data/raw/
# Step 4: combine only the files that passed validation

# --- Step 1: expected source structure ---------------------------------------
# Euronext EID files must have exactly these 27 columns, in this order.


expected_eid_columns = [
    "TradingDateTime",
    "PublicationDateTime",
    "MifidInstrumentID",
    "MifidPrice",
    "MifidQuantity",
    "MifidPriceNotation",
    "MifidCurrency",
    "MifidQtyInMeasurementUnitNotation",
    "MifidQuantityMeasurementUnit",
    "MifidNotionalAmount",
    "NotionalCurrency",
    "MifidClearingFlag",
    "MmtPostTradeDeferral",
    "NumberOfTransactions",
    "MmtMarketMechanism",
    "MmtNegotiationIndicator",
    "MmtModificationIndicator",
    "MmtBenchMarkIndicator",
    "MmtContributionToPrice",
    "MmtAlgorithmicIndicator",
    "MmtPublicationMode",
    "Venue",
    "ThirdCountryTradingVenueExecution",
    "TradeUniqueIdentifier",
    "MissingPrice",
    "MmtContingentTransactionIndicator",
    "VenueOfPublication",
]


# --- Step 2a: validation function --------------------------------------------
def validate_eid_columns(dataframe, expected_columns):
    """Compare a file's columns with the expected structure.

    Returns a small dictionary describing what matched and what did not,
    so the caller can decide what to do with the file.
    """
    actual_columns = dataframe.columns.tolist()

    missing_columns = [c for c in expected_columns if c not in actual_columns]
    extra_columns = [c for c in actual_columns if c not in expected_columns]

    return {
        # same set of names (ignores order)
        "columns_match": not missing_columns and not extra_columns,
        "missing_columns": missing_columns,
        "extra_columns": extra_columns,
        # same names in the same order
        "order_matches": actual_columns == expected_columns,
    }


# --- Step 2b: loading function -----------------------------------------------
def load_eid_file(file_path, expected_columns, csv_settings):
    """Read one daily CSV and validate it. Returns (dataframe, validation)."""
    dataframe = pd.read_csv(file_path, **csv_settings)
    validation = validate_eid_columns(dataframe, expected_columns)
    return dataframe, validation


# --- Step 3: discover and load every file ------------------------------------
source_files = sorted(raw_data_folder.glob("*.csv"))

if not source_files:
    raise FileNotFoundError(f"No CSV files found in {raw_data_folder}")

print(f"CSV files found: {len(source_files)}")

validated_eid_raw_dataframes = []   # files that passed -> will be combined
eid_file_validation_results = []    # one audit row per file (pass or fail)
rejected_files = []                 # names of files that failed validation

for file_path in source_files:
    df_daily, validation = load_eid_file(
        file_path, expected_eid_columns, csv_setting
    )

    # Keep an audit record for EVERY file, including rejected ones
    eid_file_validation_results.append({
        "filename": file_path.name,
        "rows": df_daily.shape[0],
        "columns": df_daily.shape[1],
        "columns_match": validation["columns_match"],
        "missing_columns": validation["missing_columns"],
        "extra_columns": validation["extra_columns"],
        "order_matches": validation["order_matches"],
    })

    # Accept the file only if names AND order match exactly
    if validation["columns_match"] and validation["order_matches"]:
        validated_eid_raw_dataframes.append(df_daily)
        status = "OK"
    else:
        rejected_files.append(file_path.name)
        status = "REJECTED"

    print(f"{status:9} {file_path.name}  shape={df_daily.shape}")

# A rejected file is never silently ignored
if rejected_files:
    print("\nWARNING - files excluded from the pipeline:", rejected_files)

if not validated_eid_raw_dataframes:
    raise ValueError("No file passed column validation. Nothing to combine.")

# --- Step 4: combine validated files -----------------------------------------
# ignore_index=True renumbers rows 0..n-1 across the stacked files.
df_eid_raw_combined = pd.concat(
    validated_eid_raw_dataframes, ignore_index=True
)

print("\nValidated files combined:", len(validated_eid_raw_dataframes))
print("Combined raw shape:", df_eid_raw_combined.shape)

# The raw combined frame is never edited again.
# All cleaning in Section 3 happens on a separate working copy.


# =============================================================================
# SECTION 3: CLEANING AND PREPARATION
# =============================================================================
# Rule for this section: df_eid_raw_combined is never modified.
# We copy it into df_eid_working_combined and only change the copy.
# Original text columns stay as published; new columns are added beside them.

# --- Step 1: drop columns that are completely empty --------------------------
# A column with no non-missing value in ANY file carries no information.


empty_columns = [
    column for column in df_eid_raw_combined.columns
    if df_eid_raw_combined[column].dropna().empty
]
print("Empty columns to drop:", empty_columns)

# Safety check: the columns the analysis relies on must not be in that list.
required_columns = [
    "TradingDateTime", "PublicationDateTime", "MifidInstrumentID",
    "MifidPrice", "MifidQuantity", "MifidNotionalAmount",
    "NotionalCurrency", "MmtMarketMechanism",
    "MmtModificationIndicator", "TradeUniqueIdentifier",
]
dropped_but_required = [c for c in required_columns if c in empty_columns]
if dropped_but_required:
    raise ValueError(f"Required columns are empty: {dropped_but_required}")

df_eid_working_combined = (
    df_eid_raw_combined.drop(columns=empty_columns).copy()
)
print("Raw shape:    ", df_eid_raw_combined.shape)
print("Working shape:", df_eid_working_combined.shape)

# --- Step 2: parse the execution timestamp -----------------------------------
# utc=True makes every timestamp timezone-aware in UTC.
# If any value cannot be parsed, pandas raises an error: we want to know,
# not silently lose rows.
df_eid_working_combined["TradingDateTime_dt"] = pd.to_datetime(
    df_eid_working_combined["TradingDateTime"], utc=True
)

# --- Step 3: date and hour for grouping --------------------------------------
# Both are in UTC, not Paris local time.
df_eid_working_combined["trade_date"] = (
    df_eid_working_combined["TradingDateTime_dt"].dt.date
)
df_eid_working_combined["trade_hour"] = (
    df_eid_working_combined["TradingDateTime_dt"].dt.hour
)

# --- Step 4: numeric versions of price, quantity and notional ----------------
# The source columns are text. We convert once here and reuse the result
# in every later section.
#   errors="coerce" turns anything that is not a number into NaN.
# The original text columns are kept unchanged.
# A blank notional stays NaN. It is NOT turned into zero.
numeric_fields = {
    "MifidPrice": "price_num",
    "MifidQuantity": "quantity_num",
    "MifidNotionalAmount": "notional_num",
}

for source_column, numeric_column in numeric_fields.items():
    df_eid_working_combined[numeric_column] = pd.to_numeric(
        df_eid_working_combined[source_column], errors="coerce"
    )

# --- Step 5: profile of the prepared data ------------------------------------
total_records = len(df_eid_working_combined)

print("\n--- Prepared data profile ---")
print("Total published records:", f"{total_records:,}")
print("Distinct instrument IDs:",
      f"{df_eid_working_combined['MifidInstrumentID'].nunique():,}")
print("Observed trade dates:   ",
      df_eid_working_combined["trade_date"].nunique())
print("Date range (UTC):       ",
      df_eid_working_combined["trade_date"].min(), "to",
      df_eid_working_combined["trade_date"].max())
print("Hour range (UTC):       ",
      df_eid_working_combined["trade_hour"].min(), "to",
      df_eid_working_combined["trade_hour"].max())

# Missing vs unparseable: these are two different situations.
#   missing      = the source cell was blank
#   unparseable  = the cell had text, but it was not a number
for source_column, numeric_column in numeric_fields.items():
    source_blank = df_eid_working_combined[source_column].isna()
    not_numeric = df_eid_working_combined[numeric_column].isna()
    unparseable = not_numeric & ~source_blank

    print(f"{source_column:22} blank: {source_blank.sum():>8,}"
          f"   unparseable: {unparseable.sum():>6,}"
          f"   numeric: {(~not_numeric).sum():>8,}")


# =============================================================================
# SECTION 4: INSTRUMENT CONCENTRATION
# =============================================================================
# Question: how concentrated are published records among the most active
# instruments, and does that change by date?
#
# Important: these are descriptive RECORD-COUNT measures. They do not measure
# market power, competition, liquidity or trading value.
# `total_records` comes from Section 3 and is reused here as the denominator.

# --- Step 1: records per instrument, whole period ----------------------------
# groupby + size() counts rows per instrument.
# Sorting by count (then ID) gives a stable, repeatable ranking.
instrument_counts = (
    df_eid_working_combined
    .groupby("MifidInstrumentID")
    .size()
    .reset_index(name="record_count")
    .sort_values(["record_count", "MifidInstrumentID"],
                 ascending=[False, True])
    .reset_index(drop=True)
)

instrument_counts["pct_of_total"] = (
    instrument_counts["record_count"] / total_records * 100
)

top3_total = instrument_counts["record_count"].head(3).sum()
top3_pct = top3_total / total_records * 100

print("Top 10 instruments by published records:")
print(instrument_counts.head(10).to_string(
    index=False, formatters={"pct_of_total": "{:.2f}".format}
))
print(f"\nTop 3 instruments: {top3_total:,} records "
      f"({top3_pct:.2f}% of all records)")

# --- Step 2: records per instrument, per date --------------------------------
# An instrument can dominate the full period yet vary from day to day,
# so we repeat the count inside each date.
eid_instrument_by_date = (
    df_eid_working_combined
    .groupby(["trade_date", "MifidInstrumentID"])
    .size()
    .reset_index(name="record_count")
)

# transform("sum") puts each date's total on every row of that date,
# so we can divide row by row without a merge.
eid_daily_totals = (
    eid_instrument_by_date
    .groupby("trade_date")["record_count"]
    .transform("sum")
)

eid_instrument_by_date["pct_of_daily_records"] = (
    eid_instrument_by_date["record_count"] / eid_daily_totals * 100
)
eid_instrument_by_date["pct_of_all_records"] = (
    eid_instrument_by_date["record_count"] / total_records * 100
)

# --- Step 3: rank instruments within each date -------------------------------
# Sort by date, then by count (largest first). Ties are broken by instrument
# ID so the ranking is the same on every run.
# cumcount() numbers rows 0,1,2... inside each date; +1 makes rank 1,2,3...
eid_ranked_instruments = (
    eid_instrument_by_date
    .sort_values(
        ["trade_date", "record_count", "MifidInstrumentID"],
        ascending=[True, False, True],
    )
    .copy()
)
eid_ranked_instruments["instrument_rank"] = (
    eid_ranked_instruments.groupby("trade_date").cumcount() + 1
)

eid_top3_instruments_by_date = (
    eid_ranked_instruments[eid_ranked_instruments["instrument_rank"] <= 3]
)

# --- Step 4: daily totals and active instruments -----------------------------
eid_daily_concentration = (
    eid_instrument_by_date
    .groupby("trade_date")
    .agg(
        total_records=("record_count", "sum"),
        active_instruments=("MifidInstrumentID", "nunique"),
    )
    .reset_index()
)

# --- Step 5: CR1 - share of the leading instrument ---------------------------
# CR1 = records of the #1 instrument on a date / all records that date x 100
eid_cr1_by_date = (
    eid_ranked_instruments
    .loc[eid_ranked_instruments["instrument_rank"] == 1,
         ["trade_date", "MifidInstrumentID", "pct_of_daily_records"]]
    .rename(columns={
        "MifidInstrumentID": "top_instrument",
        "pct_of_daily_records": "CR1_pct",
    })
)

# --- Step 6: CR3 - combined share of the three leading instruments -----------
# CR3 = records of the top 3 instruments on a date / all records that date x 100
eid_cr3_by_date = (
    eid_top3_instruments_by_date
    .groupby("trade_date")["pct_of_daily_records"]
    .sum()
    .reset_index(name="CR3_pct")
)

# --- Step 7: one summary row per date ----------------------------------------
eid_daily_concentration = (
    eid_daily_concentration
    .merge(eid_cr1_by_date, on="trade_date", how="left")
    .merge(eid_cr3_by_date, on="trade_date", how="left")
)

print("\nDaily concentration:")
print(eid_daily_concentration.to_string(
    index=False,
    formatters={"CR1_pct": "{:.2f}".format, "CR3_pct": "{:.2f}".format},
))


# =============================================================================
# SECTION 5: NOTIONAL COVERAGE
# =============================================================================
# Background:
#   MifidNotionalAmount is the notional Euronext published for each record.
#   For many derivatives, notional = price x quantity x multiplier, but the
#   ESMA formula differs by product type (options use strike, not premium).
#   So we do NOT impute missing notionals and we do NOT treat price x quantity
#   as a universal notional. We only describe what is reported.
#
# "Missing" here means the source cell was blank (MifidNotionalAmount is NA).
# The numeric column notional_num (from Section 3) is used for any sums.


# -----------------------------------------------------------------------------
# 5A. Missing notional: broad or concentrated?
# -----------------------------------------------------------------------------
eid_notional_by_instrument = (
    df_eid_working_combined
    .groupby("MifidInstrumentID")
    .agg(
        total_records=("MifidInstrumentID", "size"),
        missing_notional_records=(
            "MifidNotionalAmount", lambda s: s.isna().sum()
        ),
    )
    .reset_index()
)

eid_notional_by_instrument["reported_notional_records"] = (
    eid_notional_by_instrument["total_records"]
    - eid_notional_by_instrument["missing_notional_records"]
)
eid_notional_by_instrument["missing_notional_pct"] = (
    eid_notional_by_instrument["missing_notional_records"]
    / eid_notional_by_instrument["total_records"] * 100
)

eid_total_missing_notional = (
    eid_notional_by_instrument["missing_notional_records"].sum()
)
eid_notional_by_instrument["share_of_all_missing_pct"] = (
    eid_notional_by_instrument["missing_notional_records"]
    / eid_total_missing_notional * 100
)

# Classify each instrument: all blank, none blank, or a mix
fully_missing = (eid_notional_by_instrument["missing_notional_pct"] == 100).sum()
fully_reported = (eid_notional_by_instrument["missing_notional_pct"] == 0).sum()
partial = len(eid_notional_by_instrument) - fully_missing - fully_reported

print("Instruments with 100% missing notional:", fully_missing)
print("Instruments with 0% missing notional:  ", fully_reported)
print("Instruments with partial missingness:  ", partial)

# Only instruments that have at least one missing notional, largest first
eid_missing_notional_summary = (
    eid_notional_by_instrument
    [eid_notional_by_instrument["missing_notional_records"] > 0]
    .sort_values("missing_notional_records", ascending=False)
    .reset_index(drop=True)
)

print("\nTop 10 instruments by missing-notional records:")
print(eid_missing_notional_summary.head(10).to_string(
    index=False,
    formatters={
        "missing_notional_pct": "{:.2f}".format,
        "share_of_all_missing_pct": "{:.2f}".format,
    },
))

# Reading the result: if "partial" is 0, missingness is instrument-level
# (an instrument either always reports notional or never does). That points
# to a structural reporting convention, but the data alone cannot say why.

# Focus instrument: look at one heavily affected ID in detail
focus_instrument_id = "4275399742"

df_focus = df_eid_working_combined[
    df_eid_working_combined["MifidInstrumentID"] == focus_instrument_id
]

focus_total = len(df_focus)
focus_missing = df_focus["MifidNotionalAmount"].isna().sum()

print(f"\nFocus instrument {focus_instrument_id}:")
print("  Records:", f"{focus_total:,}")
print("  Missing notional:", f"{focus_missing:,}",
      f"({focus_missing / focus_total * 100:.2f}%)")
for column in ["price_num", "quantity_num"]:
    print(f"  {column} min / median / max:",
          df_focus[column].min(),
          df_focus[column].median(),
          df_focus[column].max())


# -----------------------------------------------------------------------------
# 5B. Implied ratio: notional / (price x quantity)
# -----------------------------------------------------------------------------
# For each row with a reported notional we compute the ratio. If it is the
# same for every row of an instrument, it behaves like a fixed multiplier.
# It is a DIAGNOSTIC only - not a verified contract multiplier and not a
# rule for filling in missing notionals.

denominator = (
    df_eid_working_combined["price_num"]
    * df_eid_working_combined["quantity_num"]
)

# .where() keeps the ratio only where the denominator is not zero
# (a zero denominator would otherwise give infinity).
df_eid_working_combined["implied_ratio"] = (
    df_eid_working_combined["notional_num"] / denominator
).where(denominator != 0)

# One row per instrument: how many ratios, and how much do they vary?
eid_implied_ratio_summary = (
    df_eid_working_combined
    .dropna(subset=["implied_ratio"])
    .groupby("MifidInstrumentID")
    .agg(
        records_with_reported_notional=("implied_ratio", "size"),
        median_implied_ratio=("implied_ratio", "median"),
        minimum_implied_ratio=("implied_ratio", "min"),
        maximum_implied_ratio=("implied_ratio", "max"),
    )
    .reset_index()
)

eid_implied_ratio_summary["implied_ratio_range"] = (
    eid_implied_ratio_summary["maximum_implied_ratio"]
    - eid_implied_ratio_summary["minimum_implied_ratio"]
)

# "Stable" = the spread is smaller than 0.000001
eid_implied_ratio_summary["appears_stable"] = (
    eid_implied_ratio_summary["implied_ratio_range"].abs() < 0.000001
)

eid_implied_ratio_summary = eid_implied_ratio_summary.sort_values(
    "records_with_reported_notional", ascending=False
)

print("\nImplied ratio - 20 instruments with most reported notionals:")
print(eid_implied_ratio_summary.head(20).to_string(index=False))
print("Instruments with a stable ratio:",
      eid_implied_ratio_summary["appears_stable"].sum(),
      "of", len(eid_implied_ratio_summary))


# -----------------------------------------------------------------------------
# 5C. Top-10 instruments: notional coverage and reported sums
# -----------------------------------------------------------------------------
# Before ranking anything by notional, check that notional EXISTS for the
# instruments we compare. An ID with many records but no reported notional
# would look "small" in a notional ranking only because it was never reported.
# The Top 10 is chosen by RECORD COUNT (Section 4), not by notional.

eid_top10_record_ids = instrument_counts["MifidInstrumentID"].head(10).tolist()

df_top10 = df_eid_working_combined[
    df_eid_working_combined["MifidInstrumentID"].isin(eid_top10_record_ids)
]

# Coverage: reported + missing must equal published
eid_top10_notional_coverage = (
    df_top10
    .groupby("MifidInstrumentID")
    .agg(
        published_records=("MifidInstrumentID", "size"),
        reported_notional_rows=("MifidNotionalAmount", lambda v: v.notna().sum()),
        missing_notional_rows=("MifidNotionalAmount", lambda v: v.isna().sum()),
    )
    .reindex(eid_top10_record_ids)          # keep record-count order
)

print("\nTop 10 by published records - notional coverage:")
print(eid_top10_notional_coverage.to_string())

# Sum of reported notional by instrument AND currency.
# Currencies are never added together. dropna=False keeps rows whose
# currency is blank instead of dropping them.
eid_top10_reported_notional = (
    df_top10
    .dropna(subset=["notional_num"])
    .groupby(["MifidInstrumentID", "NotionalCurrency"],
             dropna=False, as_index=False)
    .agg(
        reported_notional_rows=("notional_num", "size"),
        sum_of_reported_notional=("notional_num", "sum"),
    )
)

# Merge back so IDs with NO reported notional still appear (as missing, not 0)
eid_top10_notional_result = (
    eid_top10_notional_coverage
    .reset_index()
    .merge(eid_top10_reported_notional, on="MifidInstrumentID",
           how="left", suffixes=("_coverage", ""))
    [["MifidInstrumentID", "published_records",
      "reported_notional_rows_coverage", "missing_notional_rows",
      "NotionalCurrency", "sum_of_reported_notional"]]
)

print("\nTop 10 - reported notional by currency:")
print(eid_top10_notional_result.to_string(index=False))

# Same sums, split by observed date
# sum(min_count=1) returns NaN (not 0) when a group has no reported notional.
eid_top10_notional_by_date = (
    df_top10
    .groupby(["trade_date", "MifidInstrumentID", "NotionalCurrency"],
             dropna=False, as_index=False)
    .agg(
        published_records=("MifidInstrumentID", "size"),
        reported_notional_rows=("notional_num", "count"),
        sum_of_reported_notional=("notional_num",
                                  lambda v: v.sum(min_count=1)),
    )
)

eid_top10_notional_by_date["missing_notional_rows"] = (
    eid_top10_notional_by_date["published_records"]
    - eid_top10_notional_by_date["reported_notional_rows"]
)

# Mean reported notional per row that HAS a notional (zero rows -> NA)
eid_top10_notional_by_date["mean_notional_per_covered_row"] = (
    eid_top10_notional_by_date["sum_of_reported_notional"]
    / eid_top10_notional_by_date["reported_notional_rows"].replace(0, pd.NA)
)

# One-line-per-ID review: dates seen, records, coverage, total reported notional
eid_top10_daily_review = (
    eid_top10_notional_by_date
    .groupby("MifidInstrumentID")
    .agg(
        observed_dates=("trade_date", "nunique"),
        published_records=("published_records", "sum"),
        reported_notional_rows=("reported_notional_rows", "sum"),
        missing_notional_rows=("missing_notional_rows", "sum"),
        sum_of_reported_notional=("sum_of_reported_notional",
                                  lambda v: v.sum(min_count=1)),
    )
    .reindex(eid_top10_record_ids)
    .reset_index()
)

print("\nTop 10 - one-line review across all dates:")
print(eid_top10_daily_review.to_string(index=False))


# =============================================================================
# SECTION 6: MARKET MECHANISM PATTERNS
# =============================================================================
# Question: where and when do the observed mechanism codes appear,
# especially the less common codes 4, 5 and 8?
#
# Scope: we DESCRIBE patterns only. A mechanism code does not explain why a
# price or quantity event happened, and co-occurrence is not causation.
# Codes are text ("1", "4", "5", "8") because Section 2 read everything as text.


# -----------------------------------------------------------------------------
# 6A. Overall mechanism counts
# -----------------------------------------------------------------------------
# dropna=False keeps blank mechanisms visible instead of hiding them.
eid_mechanism_counts = (
    df_eid_working_combined["MmtMarketMechanism"]
    .value_counts(dropna=False)
    .rename_axis("market_mechanism")
    .reset_index(name="record_count")
)

eid_mechanism_counts["pct_of_total"] = (
    eid_mechanism_counts["record_count"] / total_records * 100
)

print("Records by market mechanism:")
print(eid_mechanism_counts.to_string(
    index=False, formatters={"pct_of_total": "{:.2f}".format}
))


# -----------------------------------------------------------------------------
# 6B. Mechanism by date
# -----------------------------------------------------------------------------
# Does every code appear on every date, or only on some?
eid_mechanism_by_date = (
    df_eid_working_combined
    .groupby(["trade_date", "MmtMarketMechanism"])
    .size()
    .reset_index(name="record_count")
    .sort_values(["trade_date", "MmtMarketMechanism"])
)

print("\nMechanism codes seen per date:")
print(
    eid_mechanism_by_date
    .groupby("trade_date")["MmtMarketMechanism"]
    .nunique()
    .to_string()
)


# -----------------------------------------------------------------------------
# 6C. The less common codes: 4, 5 and 8
# -----------------------------------------------------------------------------
# For each rare code: how many records, how many different instruments,
# on how many dates, and between which UTC hours.
eid_less_common_mechanisms = ["4", "5", "8"]

eid_focused_mechanisms = (
    df_eid_working_combined
    [df_eid_working_combined["MmtMarketMechanism"]
     .isin(eid_less_common_mechanisms)]
    .groupby("MmtMarketMechanism")
    .agg(
        record_count=("MmtMarketMechanism", "size"),
        instrument_count=("MifidInstrumentID", "nunique"),
        date_count=("trade_date", "nunique"),
        earliest_trade_hour=("trade_hour", "min"),
        latest_trade_hour=("trade_hour", "max"),
    )
    .reset_index()
    .rename(columns={"MmtMarketMechanism": "market_mechanism"})
)

eid_focused_mechanisms["pct_of_all_records"] = (
    eid_focused_mechanisms["record_count"] / total_records * 100
)

print("\nLess common mechanisms (4, 5, 8):")
print(eid_focused_mechanisms.to_string(
    index=False, formatters={"pct_of_all_records": "{:.2f}".format}
))


# -----------------------------------------------------------------------------
# 6D. Which codes does each instrument use?
# -----------------------------------------------------------------------------
# For every instrument, list the distinct codes it appears with, sorted and
# joined into one label (for example "1", or "1 + 4 + 5").
# Then count how many instruments share each combination.
eid_mechanism_codes_by_instrument = (
    df_eid_working_combined
    .groupby("MifidInstrumentID")["MmtMarketMechanism"]
    .agg(lambda codes: " + ".join(sorted(codes.dropna().unique())))
    .reset_index(name="mechanism_combination")
)

eid_mechanism_combination_counts = (
    eid_mechanism_codes_by_instrument["mechanism_combination"]
    .value_counts()
    .rename_axis("mechanism_combination")
    .reset_index(name="instrument_count")
    .sort_values(["instrument_count", "mechanism_combination"],
                 ascending=[False, True])
    .reset_index(drop=True)
)

print("\nInstruments by mechanism combination:")
print(eid_mechanism_combination_counts.to_string(index=False))


# -----------------------------------------------------------------------------
# 6E. Optional: share of quantity versus share of records, by mechanism
# -----------------------------------------------------------------------------
# Do codes with very few records carry a much larger share of summed quantity?
# This is a descriptive sum of reported quantities, not economic volume, and
# it includes cancellation-marked records.
eid_mechanism_quantity = (
    df_eid_working_combined
    .groupby("MmtMarketMechanism", dropna=False)
    .agg(
        record_count=("MmtMarketMechanism", "size"),
        reported_quantity=("quantity_num", "sum"),
    )
    .reset_index()
)

eid_mechanism_quantity["pct_of_records"] = (
    eid_mechanism_quantity["record_count"] / total_records * 100
)
eid_mechanism_quantity["pct_of_reported_quantity"] = (
    eid_mechanism_quantity["reported_quantity"]
    / eid_mechanism_quantity["reported_quantity"].sum() * 100
)

print("\nShare of records versus share of reported quantity:")
print(eid_mechanism_quantity.to_string(
    index=False,
    formatters={
        "pct_of_records": "{:.2f}".format,
        "pct_of_reported_quantity": "{:.2f}".format,
    },
))


# =============================================================================
# SECTION 7: QUANTITY-BASED ACTIVITY
# =============================================================================
# Why this section exists:
#   Section 4 found strong concentration in RECORD COUNTS. Here we test whether
#   that finding also holds when we sum REPORTED QUANTITIES, and whether any
#   instrument repeatedly leads a particular UTC hour.
#
# Possible outcomes and what each would mean:
#   - Same instrument leads both measures -> same ID dominates both views.
#   - A different ID leads quantity       -> record count and quantity give
#                                            different activity rankings.
#   - One ID leads the same hour often    -> a repeated time-of-day pattern.
#   - Leader varies by date or one big row-> no stable hourly leader.
#
# This is a descriptive test, not a claim about total market volume or causes.
# We use quantity_num created in Section 3. Source text is unchanged.


# -----------------------------------------------------------------------------
# 7A. Quantity quality profile
# -----------------------------------------------------------------------------
source_blank = df_eid_working_combined["MifidQuantity"].isna()
not_numeric = df_eid_working_combined["quantity_num"].isna()

print("Published records:        ", f"{total_records:,}")
print("Observed trade dates:     ", df_eid_working_combined["trade_date"].nunique())
print("Blank source quantity:    ", source_blank.sum())
print("Non-numeric, non-blank:   ", (not_numeric & ~source_blank).sum())
print("Zero quantity:            ", df_eid_working_combined["quantity_num"].eq(0).sum())
print("Negative quantity:        ", df_eid_working_combined["quantity_num"].lt(0).sum())

print("\nModification indicator (all rows kept, nothing removed):")
print(df_eid_working_combined["MmtModificationIndicator"]
      .value_counts(dropna=False).to_string())
# "-" is the source's normal (non-modified) marker, not a blank.
# CANC rows are cancellations. They stay in every sum below:
# no deduplication and no cancellation removal.


# -----------------------------------------------------------------------------
# 7B. Record-count rank versus quantity rank, per instrument
# -----------------------------------------------------------------------------
eid_quantity_by_instrument = (
    df_eid_working_combined
    .groupby("MifidInstrumentID", as_index=False)
    .agg(
        published_record_count=("MifidInstrumentID", "size"),
        reported_quantity_in_published_records=("quantity_num", "sum"),
    )
)

# rank(method="min") gives tied values the same (lowest) rank
eid_quantity_by_instrument["record_count_rank"] = (
    eid_quantity_by_instrument["published_record_count"]
    .rank(method="min", ascending=False).astype("int64")
)
eid_quantity_by_instrument["reported_quantity_rank"] = (
    eid_quantity_by_instrument["reported_quantity_in_published_records"]
    .rank(method="min", ascending=False).astype("int64")
)

print("\nTop 10 instruments by reported quantity:")
print(eid_quantity_by_instrument
      .sort_values("reported_quantity_rank")
      .head(10)
      .to_string(index=False))

# Column meanings:
#   published_record_count  : how often the ID appears in the extract
#   reported_quantity_...   : sum of reported quantities for the ID
#   record_count_rank       : rank by number of rows
#   reported_quantity_rank  : rank by summed quantity
# An ID with few rows but a high quantity rank shows the two measures are
# related but not interchangeable. Do not call a leader the "largest" or
# "most liquid" product.


# -----------------------------------------------------------------------------
# 7C. Hourly quantity leaders (date x UTC hour x instrument)
# -----------------------------------------------------------------------------
# Step 1: sum quantity and count rows for every date / hour / instrument
eid_quantity_by_date_hour_instrument = (
    df_eid_working_combined
    .groupby(["trade_date", "trade_hour", "MifidInstrumentID"], as_index=False)
    .agg(
        reported_quantity_in_published_records=("quantity_num", "sum"),
        published_record_count=("MifidInstrumentID", "size"),
    )
)
print("\nRows in date x hour x instrument table:",
      f"{len(eid_quantity_by_date_hour_instrument):,}")

# Step 2: totals for each date / hour bucket (the denominator for shares)
eid_quantity_by_date_hour = (
    eid_quantity_by_date_hour_instrument
    .groupby(["trade_date", "trade_hour"], as_index=False)
    .agg(
        active_instrument_ids=("MifidInstrumentID", "nunique"),
        total_reported_quantity_in_hour=(
            "reported_quantity_in_published_records", "sum"),
        total_published_record_count=("published_record_count", "sum"),
    )
)

# Step 3: keep the top instrument in each bucket.
# Sort so the leader comes first: highest quantity, then most records, then
# lowest ID (so ties are settled the same way every run).
# drop_duplicates(keep="first") then keeps one row per date/hour.
eid_quantity_hourly_leaders = (
    eid_quantity_by_date_hour_instrument
    .sort_values(
        ["trade_date", "trade_hour",
         "reported_quantity_in_published_records",
         "published_record_count", "MifidInstrumentID"],
        ascending=[True, True, False, False, True],
    )
    .drop_duplicates(subset=["trade_date", "trade_hour"], keep="first")
    .merge(
        eid_quantity_by_date_hour,
        on=["trade_date", "trade_hour"],
        how="left",
        validate="one_to_one",   # stops the merge if a bucket appears twice
    )
)

eid_quantity_hourly_leaders["quantity_share_of_hour_pct"] = (
    eid_quantity_hourly_leaders["reported_quantity_in_published_records"]
    / eid_quantity_hourly_leaders["total_reported_quantity_in_hour"] * 100
)

print("Observed date x UTC-hour buckets:", len(eid_quantity_hourly_leaders))
print(eid_quantity_hourly_leaders
      .sort_values(["trade_date", "trade_hour"])
      .head(20)
      .to_string(index=False,
                 formatters={"quantity_share_of_hour_pct": "{:.2f}%".format}))

# Does the same instrument keep leading? Count hourly wins per instrument.
print("\nHours led, by instrument:")
print(eid_quantity_hourly_leaders["MifidInstrumentID"]
      .value_counts().head(10).to_string())


# -----------------------------------------------------------------------------
# 7D. Quantity ranking within selected dates
# -----------------------------------------------------------------------------
# For each chosen date, rank every instrument by summed quantity and show
# its share of that date's rows and of that date's quantity.
# Change this list to inspect other dates.
dates_to_check = [
    pd.Timestamp("2026-09-18").date(),
    pd.Timestamp("2026-09-22").date(),
    pd.Timestamp("2026-09-28").date(),
]

df_check_dates = df_eid_working_combined[
    df_eid_working_combined["trade_date"].isin(dates_to_check)
]

for check_date, day in df_check_dates.groupby("trade_date", sort=True):
    day_rows = len(day)
    day_quantity = day["quantity_num"].sum(min_count=1)

    by_id = (
        day.groupby("MifidInstrumentID")
        .agg(
            published_rows=("MifidInstrumentID", "size"),
            quantity_sum=("quantity_num", lambda s: s.sum(min_count=1)),
            notional_rows=("notional_num", "count"),
            notional_sum=("notional_num", lambda s: s.sum(min_count=1)),
            mean_reported_price=("price_num", "mean"),
        )
        .reset_index()
        .sort_values("quantity_sum", ascending=False)
    )

    by_id["quantity_rank_all_ids"] = (
        by_id["quantity_sum"].rank(method="min", ascending=False)
        .astype("Int64")
    )
    by_id["row_share_pct"] = by_id["published_rows"] / day_rows * 100
    by_id["quantity_share_pct"] = (
        by_id["quantity_sum"] / day_quantity * 100
        if pd.notna(day_quantity) and day_quantity > 0 else pd.NA
    )

    # Leaders that have notional reported (so notional can be compared too)
    leaders = by_id[by_id["notional_rows"] > 0].head(3)

    print(f"\n{check_date} | rows: {day_rows:,} | IDs: {len(by_id):,}")
    print(leaders.to_string(index=False))

# =============================================================================
# SECTION 8: CHECKS AND GRAPHS
# =============================================================================
# Nothing here creates new analysis. It confirms that the sections above agree
# with each other, draws the charts, and prepares the checks for Power BI.


# -----------------------------------------------------------------------------
# 8A. Reconciliation checks
# -----------------------------------------------------------------------------
check_results = []

def run_check(name, passed, detail=""):
    """Record one PASS/FAIL result and print it."""
    check_results.append({"check": name, "passed": bool(passed), "detail": detail})
    print(f"{'PASS' if passed else 'FAIL':5}{name}  {detail}")

# --- Import (Section 2) and cleaning (Section 3) ---
run_check("Every CSV passed validation",
          len(rejected_files) == 0,
          f"{len(validated_eid_raw_dataframes)} of {len(source_files)} files")
run_check("Raw rows = sum of file rows",
          len(df_eid_raw_combined)
          == sum(len(d) for d in validated_eid_raw_dataframes),
          f"{len(df_eid_raw_combined):,}")
run_check("Working rows = raw rows (no row removed)",
          len(df_eid_working_combined) == len(df_eid_raw_combined))
run_check("UTC hours inside 0-23",
          df_eid_working_combined["trade_hour"].between(0, 23).all())

# --- Concentration (Section 4) ---
run_check("Daily totals sum to working rows",
          eid_daily_concentration["total_records"].sum() == total_records)
run_check("Instrument counts sum to working rows",
          instrument_counts["record_count"].sum() == total_records)
run_check("CR3 is never below CR1",
          (eid_daily_concentration["CR3_pct"]
           >= eid_daily_concentration["CR1_pct"] - 1e-9).all())

# --- Notional (Section 5) ---
reported_notional_rows = df_eid_working_combined["MifidNotionalAmount"].notna().sum()
missing_notional_rows = df_eid_working_combined["MifidNotionalAmount"].isna().sum()
run_check("Reported + missing notional = working rows",
          reported_notional_rows + missing_notional_rows == total_records,
          f"{reported_notional_rows:,} + {missing_notional_rows:,}")
run_check("Missing-notional summary matches total missing",
          eid_missing_notional_summary["missing_notional_records"].sum()
          == missing_notional_rows)
run_check("Top-10 coverage reconciles (reported + missing = published)",
          (eid_top10_notional_coverage["reported_notional_rows"]
           + eid_top10_notional_coverage["missing_notional_rows"]
           == eid_top10_notional_coverage["published_records"]).all())
run_check("Implied-ratio rows <= numeric-notional rows",
          eid_implied_ratio_summary["records_with_reported_notional"].sum()
          <= df_eid_working_combined["notional_num"].notna().sum(),
          "(rows with zero price x quantity are excluded from the ratio)")

# --- Mechanism (Section 6) ---
run_check("Mechanism counts sum to working rows",
          eid_mechanism_counts["record_count"].sum() == total_records)
run_check("Mechanism-by-date counts sum to working rows",
          eid_mechanism_by_date["record_count"].sum() == total_records)
run_check("Mechanism combinations cover every instrument",
          eid_mechanism_combination_counts["instrument_count"].sum()
          == df_eid_working_combined["MifidInstrumentID"].nunique())

# --- Quantity (Section 7) ---
run_check("Quantity-by-instrument rows sum to working rows",
          eid_quantity_by_instrument["published_record_count"].sum() == total_records)
run_check("Date x hour x instrument rows sum to working rows",
          eid_quantity_by_date_hour_instrument["published_record_count"].sum()
          == total_records)

# Summary
failed = [c["check"] for c in check_results if not c["passed"]]
print(f"\n{len(check_results) - len(failed)} of {len(check_results)} checks passed.")
if failed:
    print("Failed checks:", failed)

# --- Information only: repeated trade IDs and cancellations ---
# We keep every published row. These counts describe, they do not filter.
trade_id_counts = df_eid_working_combined["TradeUniqueIdentifier"].value_counts()
repeated_trade_ids = trade_id_counts[trade_id_counts > 1].index

eid_trade_id_audit = (
    df_eid_working_combined[
        df_eid_working_combined["TradeUniqueIdentifier"].isin(repeated_trade_ids)
        | (df_eid_working_combined["MmtModificationIndicator"] == "CANC")
    ]
    [["TradeUniqueIdentifier", "MmtModificationIndicator", "TradingDateTime",
      "PublicationDateTime", "MifidInstrumentID", "MifidPrice",
      "MifidQuantity", "MifidNotionalAmount", "MmtMarketMechanism"]]
    .sort_values(["TradeUniqueIdentifier", "PublicationDateTime"])
)
print("\nNon-null trade IDs:", df_eid_working_combined["TradeUniqueIdentifier"].notna().sum())
print("Trade IDs appearing more than once:", len(repeated_trade_ids))
print("Cancellation (CANC) rows:",
      (df_eid_working_combined["MmtModificationIndicator"] == "CANC").sum())


# -----------------------------------------------------------------------------
# 8B. Graphs
# -----------------------------------------------------------------------------
# Each chart is saved to output/figures/ and shown at the end.

# --- Chart 1: daily concentration (CR1 and CR3) ---
cr_trend = eid_daily_concentration.sort_values("trade_date")
cr_labels = [d.strftime("%d %b") for d in cr_trend["trade_date"]]

fig1, ax = plt.subplots(figsize=(10, 5))
ax.plot(cr_labels, cr_trend["CR1_pct"], marker="o", label="CR1: leading instrument")
ax.plot(cr_labels, cr_trend["CR3_pct"], marker="o", label="CR3: leading three instruments")
ax.set_title("Daily concentration of published records by instrument")
ax.set_xlabel("Trading date (UTC)")
ax.set_ylabel("Share of that date's published records (%)")
ax.set_ylim(0, 100)
ax.grid(axis="y", alpha=0.3)
ax.legend()
fig1.autofmt_xdate()
fig1.tight_layout()
fig1.savefig(figures_folder / "01_daily_concentration_cr1_cr3.png", dpi=150)

# --- Chart 2: top-3 instruments, records versus reported quantity ---
overall_top3_ids = instrument_counts["MifidInstrumentID"].head(3).tolist()
observed_dates = sorted(df_eid_working_combined["trade_date"].dropna().unique())

top3_daily = (
    df_eid_working_combined
    [df_eid_working_combined["MifidInstrumentID"].isin(overall_top3_ids)]
    .groupby(["trade_date", "MifidInstrumentID"], as_index=False)
    .agg(published_record_count=("MifidInstrumentID", "size"),
         reported_quantity=("quantity_num", "sum"))
)

fig2, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
for instrument_id in overall_top3_ids:
    # Keep only the date and the two numeric columns before reindexing,
    # so fill_value=0 is never applied to a text column.
    daily = (
        top3_daily
        .loc[top3_daily["MifidInstrumentID"] == instrument_id,
             ["trade_date", "published_record_count", "reported_quantity"]]
        .set_index("trade_date")
        .reindex(observed_dates, fill_value=0)   # absent date -> 0 rows
    )
    axes[0].plot(range(len(observed_dates)), daily["published_record_count"],
                 marker="o", label=instrument_id)
    axes[1].plot(range(len(observed_dates)), daily["reported_quantity"],
                 marker="o", label=instrument_id)

axes[0].set_ylabel("Published records")
axes[1].set_ylabel("Reported quantity")
axes[1].set_xlabel("Observed execution date (UTC)")
axes[1].set_xticks(range(len(observed_dates)))
axes[1].set_xticklabels([d.strftime("%d %b") for d in observed_dates],
                        rotation=45, ha="right")
for axis in axes:
    axis.grid(alpha=0.25)
    axis.legend(title="MifidInstrumentID")
fig2.suptitle("Euronext Equity & Index Derivatives: top 3 IDs\n"
              "Published records versus reported quantity")
fig2.tight_layout()
fig2.savefig(figures_folder / "02_top3_records_vs_quantity.png", dpi=150)

# --- Chart 3: one instrument on one date (exploratory) ---
def plot_instrument_day(instrument_id, selected_date, start_utc=None, end_utc=None):
    """Price and quantity through one execution date for one instrument.

    Without start/end: 15-minute view of the full day.
    With start/end (UTC, end excluded): every published row in that window,
    with the largest-quantity row marked. Co-occurrence is not causation.
    """
    rows = df_eid_working_combined[
        (df_eid_working_combined["MifidInstrumentID"] == instrument_id)
        & (df_eid_working_combined["trade_date"] == selected_date)
    ].copy()
    if rows.empty:
        raise ValueError("No rows for this instrument and date.")

    rows["execution_utc"] = rows["TradingDateTime_dt"]
    windowed = start_utc is not None and end_utc is not None
    if windowed:
        if start_utc >= end_utc:
            raise ValueError("Start time must be earlier than end time.")
        rows = rows[(rows["execution_utc"] >= start_utc)
                    & (rows["execution_utc"] < end_utc)]
        if rows.empty:
            raise ValueError("No published rows in this window.")

    fig, (ax_p, ax_q) = plt.subplots(2, 1, figsize=(13, 7), sharex=True,
                                     constrained_layout=True)
    biggest = rows.loc[rows["quantity_num"].idxmax()]

    if windowed:
        ax_p.scatter(rows["execution_utc"], rows["price_num"], s=9, alpha=0.4)
        ax_q.scatter(rows["execution_utc"], rows["quantity_num"], s=9, alpha=0.4)
        for axis, column in [(ax_p, "price_num"), (ax_q, "quantity_num")]:
            axis.scatter([biggest["execution_utc"]], [biggest[column]],
                         s=85, color="crimson", marker="x", zorder=5,
                         label="Largest single-row quantity in window")
        title = f"{instrument_id} | {selected_date} | {start_utc:%H:%M}-{end_utc:%H:%M} UTC"
    else:
        rows["interval_start"] = rows["execution_utc"].dt.floor("15min")
        intervals = rows.groupby("interval_start").agg(
            mean_price=("price_num", "mean"),
            quantity_sum=("quantity_num", lambda s: s.sum(min_count=1)),
        )
        ax_p.scatter(rows["execution_utc"], rows["price_num"], s=3, alpha=0.18,
                     label="Reported price observations")
        ax_p.plot(intervals.index + pd.Timedelta(minutes=7, seconds=30),
                  intervals["mean_price"], color="darkorange",
                  label="15-minute mean price (equal weight per row)")
        ax_q.bar(intervals.index, intervals["quantity_sum"],
                 width=pd.Timedelta(minutes=13), align="edge", color="steelblue")
        ax_q.axvline(biggest["execution_utc"], color="crimson", linestyle="--",
                     label="Largest single-row quantity")
        title = f"{instrument_id} | {selected_date} | full observed day"

    ax_p.set_ylabel("Reported price")
    ax_q.set_ylabel("Reported quantity")
    ax_q.set_xlabel("Execution time (UTC)")
    ax_p.set_title(title)
    ax_p.legend()
    ax_q.legend()
    return fig

# Chart parameters: change these to look at another instrument or date
chart_instrument_id = instrument_counts["MifidInstrumentID"].iloc[0]
chart_date = pd.Timestamp("2026-09-18").date()

fig3 = plot_instrument_day(chart_instrument_id, chart_date)
fig3.savefig(figures_folder / "03_instrument_day_15min.png", dpi=150)

fig4 = plot_instrument_day(
    chart_instrument_id, chart_date,
    start_utc=pd.Timestamp("2026-09-18T13:50:00Z"),
    end_utc=pd.Timestamp("2026-09-18T14:00:00Z"),
)
fig4.savefig(figures_folder / "04_instrument_window_zoom.png", dpi=150)

plt.show()


# -----------------------------------------------------------------------------
# 8C. Power BI checks
# -----------------------------------------------------------------------------
# Python is the reference. Power BI must reproduce these numbers.
# Three parts:
#   1. Control totals       -> compare with cards in Power BI
#   2. Reference slice test -> reproduces the donut / time-window tests
#   3. Export verification  -> exported tables equal the Python tables

# --- Part 1: control totals ---
control_totals = pd.DataFrame([
    ("Published rows", total_records),
    ("Distinct instrument IDs", df_eid_working_combined["MifidInstrumentID"].nunique()),
    ("Observed execution dates", df_eid_working_combined["trade_date"].nunique()),
    ("Rows with numeric reported notional", df_eid_working_combined["notional_num"].notna().sum()),
    ("Rows without numeric reported notional", df_eid_working_combined["notional_num"].isna().sum()),
    ("Cancellation (CANC) rows", (df_eid_working_combined["MmtModificationIndicator"] == "CANC").sum()),
    ("Summed reported quantity", df_eid_working_combined["quantity_num"].sum()),
], columns=["measure", "python_value"])

control_totals.to_csv(tables_folder / "powerbi_control_totals.csv", index=False)
print("\nControl totals (compare with Power BI):")
print(control_totals.to_string(index=False))

# --- Part 2: reference slice (selected instrument vs all other instruments) ---
def powerbi_reference_slice(instrument_id, selected_date,
                            start_utc=None, end_utc=None):
    """What the Power BI quantity donut should show for one selection."""
    rows = df_eid_working_combined[
        df_eid_working_combined["trade_date"] == selected_date
    ]
    if start_utc is not None and end_utc is not None:
        rows = rows[(rows["TradingDateTime_dt"] >= start_utc)
                    & (rows["TradingDateTime_dt"] < end_utc)]

    selected = rows[rows["MifidInstrumentID"] == instrument_id]
    selected_qty = selected["quantity_num"].sum()
    all_qty = rows["quantity_num"].sum()

    return {
        "instrument_id": instrument_id,
        "date": selected_date,
        "rows_selected": len(selected),
        "rows_all_ids": len(rows),
        "quantity_selected": selected_qty,
        "quantity_all_ids": all_qty,
        "quantity_other_ids": all_qty - selected_qty,
        "selected_share_pct": selected_qty / all_qty * 100 if all_qty else None,
    }

# Full-day test. In the 3 Oct 2026 handover (11-date baseline) this gave
# 56,010 selected, 144,978 other, 200,988 total (27.87% / 72.13%).
# Compare with YOUR output; the numbers change if more files are added.
reference_full_day = powerbi_reference_slice(
    "FREX03591036", pd.Timestamp("2026-09-18").date()
)
print("\nReference slice - full day:")
for key, value in reference_full_day.items():
    print(f"  {key}: {value}")

# Window test: same function with start and end (UTC, end excluded)
reference_window = powerbi_reference_slice(
    "FREX03591036", pd.Timestamp("2026-09-18").date(),
    start_utc=pd.Timestamp("2026-09-18T13:50:00Z"),
    end_utc=pd.Timestamp("2026-09-18T14:00:00Z"),
)
print("Reference slice - 13:50 to 14:00 UTC window:")
print(f"  rows_selected: {reference_window['rows_selected']}")
print("  (compare this row count with your Power BI time-window measure)")

# --- Part 3: verify exported tables against Python tables ---
# Fill this dictionary in Section 9, once the export file names are fixed:
#   "table_name": (path_to_parquet_file, python_dataframe, [numeric columns])
exports_to_verify = {
    # "fact_example": (tables_folder / "fact_example.parquet",
    #                  df_eid_working_combined, ["quantity_num"]),
}

def verify_export(table_name, parquet_path, python_df, numeric_columns):
    """Reload an exported Parquet file and compare it with the Python table."""
    if not parquet_path.exists():
        run_check(f"Export exists: {table_name}", False, str(parquet_path))
        return
    exported = pd.read_parquet(parquet_path)          # needs pyarrow
    run_check(f"Export rows match: {table_name}",
              len(exported) == len(python_df),
              f"export {len(exported):,} vs python {len(python_df):,}")
    for column in numeric_columns:
        python_sum = pd.to_numeric(python_df[column], errors="coerce").sum()
        export_sum = pd.to_numeric(exported[column], errors="coerce").sum()
        run_check(f"Export sum matches: {table_name}.{column}",
                  abs(python_sum - export_sum) < 1e-6,
                  f"export {export_sum:,.2f} vs python {python_sum:,.2f}")

if exports_to_verify:
    for name, (path, frame, columns) in exports_to_verify.items():
        verify_export(name, path, frame, columns)
else:
    print("\nNo export tables registered yet - fill in Section 9.")


# =============================================================================
# SECTION 9: POWER BI EXPORT
# =============================================================================
# How the pipeline works:
#   1. FACT table  : one row per published report, built from the working data
#   2. DIM tables  : instrument, date and mechanism lookups
#   3. TIME tables : From / To dropdowns, one row per minute of the day (UTC)
#   4. AUDIT       : every check must pass before anything is written
#   5. WRITE       : Parquet files + export_manifest.csv
#   6. VERIFY      : reload the files and compare them with Python
#
# This section READS df_eid_working_combined and never modifies it.
# It reuses price_num, quantity_num and notional_num from Section 3, so
# Power BI and Python are built from exactly the same numbers.
# Blank values stay blank (never zero).

from datetime import datetime, timezone

try:
    import pyarrow  # noqa: F401  (needed by pandas for Parquet)
except ImportError:
    raise ImportError("pyarrow is required for Parquet export: pip install pyarrow")

# Power BI reads from this folder, so keep it fixed.
# Row-level exports stay private: this folder must be in .gitignore.
powerbi_folder = project_folder / "data" / "powerbi"
powerbi_folder.mkdir(parents=True, exist_ok=True)

w = df_eid_working_combined

# Frozen 11-date baseline (16 Sep to 1 Oct 2026). Set CHECK_FROZEN_BASELINE
# to True only to reproduce that exact extract. Adding new daily CSVs
# changes these numbers by design.
CHECK_FROZEN_BASELINE = False
frozen_baseline = {
    "rows": 435535,
    "instrument_ids": 6036,
    "execution_dates": 11,
    "rows_with_notional": 418843,
    "rows_missing_notional": 16692,
    "canc_rows": 9,
}


# -----------------------------------------------------------------------------
# 9A. Fact table: one row per published report
# -----------------------------------------------------------------------------
# TradingDateTime_dt is UTC (Section 3). tz_convert(None) drops the timezone
# label but keeps the UTC clock values, so Power BI shows UTC and does not
# shift the times into another timezone.
exec_utc = w["TradingDateTime_dt"]
exec_naive = exec_utc.dt.tz_convert(None)

fact = pd.DataFrame(index=w.index)
fact["MifidInstrumentID"] = w["MifidInstrumentID"].astype("string").str.strip()

# Timestamp split: each piece serves a different Power BI purpose
fact["exec_datetime_utc"] = exec_naive                                  # chart axis
fact["exec_date"] = exec_naive.dt.normalize()                           # date filter
fact["exec_minute_of_day_utc"] = exec_utc.dt.hour * 60 + exec_utc.dt.minute  # time filter, 0-1439
fact["exec_time_text_utc"] = exec_utc.dt.strftime("%H:%M:%S.%f")        # tooltips

# Reported values (numeric columns come from Section 3)
fact["reported_price"] = w["price_num"]
fact["reported_quantity"] = w["quantity_num"]
fact["reported_notional"] = w["notional_num"]
fact["has_reported_notional"] = fact["reported_notional"].notna()

# Mechanism and modification flags
fact["mechanism_code"] = w["MmtMarketMechanism"].astype("string").str.strip()
modification = w["MmtModificationIndicator"].astype("string").str.strip()
fact["modification_flag"] = modification
fact["modification_label"] = modification.map({
    "-": "No modification flag",
    "CANC": "Cancellation report",
    "AMND": "Amendment report",
}).fillna("Other / check")

# Optional context fields (added only if the column exists)
# notional_currency is the one addition: it lets Power BI keep currencies
# apart, as Section 5 does in Python.
for source_column, export_column in [
    ("MifidCurrency", "currency"),
    ("NotionalCurrency", "notional_currency"),
    ("MifidPriceNotation", "price_notation"),
    ("TradeUniqueIdentifier", "trade_unique_identifier"),
]:
    if source_column in w.columns:
        fact[export_column] = w[source_column].astype("string").str.strip()

if "PublicationDateTime" in w.columns:
    fact["publication_datetime_utc"] = pd.to_datetime(
        w["PublicationDateTime"], utc=True, errors="coerce"
    ).dt.tz_convert(None)

# row_key gives Power BI a simple unique key (1..N)
fact = fact.reset_index(drop=True)
fact.insert(0, "row_key", range(1, len(fact) + 1))


# -----------------------------------------------------------------------------
# 9B. Dimension tables
# -----------------------------------------------------------------------------
# dim_instrument: one row per instrument, ranked by published rows.
# Ties are broken by ID (A-Z), so the dropdown rank is unique and repeatable.
dim_instrument = (
    fact.groupby("MifidInstrumentID")
    .agg(
        published_rows=("row_key", "size"),
        observed_dates=("exec_date", "nunique"),
        price_rows=("reported_price", "count"),
        quantity_rows=("reported_quantity", "count"),
        notional_rows=("reported_notional", "count"),
    )
    .reset_index()
    .sort_values(["published_rows", "MifidInstrumentID"], ascending=[False, True])
    .reset_index(drop=True)
)
dim_instrument["instrument_dropdown_rank"] = range(1, len(dim_instrument) + 1)
dim_instrument["overall_row_rank"] = (
    dim_instrument["published_rows"].rank(method="min", ascending=False).astype(int)
)
dim_instrument["instrument_label"] = (
    dim_instrument["instrument_dropdown_rank"].astype(str)
    + " | " + dim_instrument["MifidInstrumentID"]
)
dim_instrument["notional_coverage_pct"] = (
    dim_instrument["notional_rows"] / dim_instrument["published_rows"] * 100
).round(2)

# dim_date: observed execution dates only (a date with no rows is not listed)
dim_date = (
    fact.groupby("exec_date")
    .agg(
        published_rows=("row_key", "size"),
        instrument_ids=("MifidInstrumentID", "nunique"),
    )
    .reset_index()
)
dim_date["date_label"] = dim_date["exec_date"].dt.strftime("%d %b %Y")
dim_date["date_order"] = range(1, len(dim_date) + 1)

# dim_mechanism: labels for the codes observed in the data
dim_mechanism = pd.DataFrame({
    "mechanism_code": ["1", "4", "5", "8"],
    "mechanism_label": ["Central Limit Order Book", "Off Book",
                        "Periodic Auction", "Hybrid System"],
    "label_source": ["FIX MMT v3.04", "FIX MMT v3.04", "FIX MMT v3.04",
                     "Euronext Optiq MDG spec (MMT v4.1)"],
})


# -----------------------------------------------------------------------------
# 9C. Time dropdown tables (From / To)
# -----------------------------------------------------------------------------
# One row per minute between the first and last observed minute (UTC).
# Two separate copies are exported so Power BI needs no relationships:
# the report simply reads the selected From and To values.
minute_min = int(fact["exec_minute_of_day_utc"].min())
minute_max = int(fact["exec_minute_of_day_utc"].max())

minutes = pd.DataFrame({"minute_of_day_utc": range(minute_min, minute_max + 1)})
minutes["time_label_utc"] = minutes["minute_of_day_utc"].map(
    lambda m: f"{m // 60:02d}:{m % 60:02d}"
)
dim_time_from = minutes.copy()
dim_time_to = minutes.copy()


# -----------------------------------------------------------------------------
# 9D. Audit: nothing is written unless every check passes
# -----------------------------------------------------------------------------
def audit_row(name, actual, expected):
    return {"check": name, "actual": actual, "expected": expected,
            "passed": actual == expected}

mechanism_counts_export = fact["mechanism_code"].value_counts(dropna=False)
top_instrument_id = instrument_counts["MifidInstrumentID"].iloc[0]   # Section 4

audit_rows = [
    # Structural checks: always run
    audit_row("fact rows = working rows", len(fact), len(w)),
    audit_row("row_key unique", bool(fact["row_key"].is_unique), True),
    audit_row("numeric quantity rows", int(fact["reported_quantity"].notna().sum()), len(fact)),
    audit_row("numeric price rows", int(fact["reported_price"].notna().sum()), len(fact)),
    audit_row("blank mechanism codes", int(fact["mechanism_code"].isna().sum()), 0),
    audit_row("unmapped mechanism codes",
              sorted(set(mechanism_counts_export.index.dropna())
                     - set(dim_mechanism["mechanism_code"])), []),
    audit_row("mechanism rows sum", int(mechanism_counts_export.sum()), len(fact)),
    audit_row("unmapped modification flags",
              int(fact["modification_label"].eq("Other / check").sum()), 0),
    audit_row("dim_instrument rows sum", int(dim_instrument["published_rows"].sum()), len(fact)),
    audit_row("dropdown rank unique 1..N",
              dim_instrument["instrument_dropdown_rank"].tolist()
              == list(range(1, len(dim_instrument) + 1)), True),
    audit_row("instrument labels unique", bool(dim_instrument["instrument_label"].is_unique), True),
    audit_row("dropdown rank 1 = top ID (Section 4)",
              dim_instrument.loc[0, "MifidInstrumentID"], top_instrument_id),
    audit_row("instrument IDs = Section 3 count",
              len(dim_instrument), w["MifidInstrumentID"].nunique()),
    audit_row("dim_date rows sum", int(dim_date["published_rows"].sum()), len(fact)),
    audit_row("time minutes unique", bool(minutes["minute_of_day_utc"].is_unique), True),
]

# Frozen-baseline checks: only when reproducing the 11-date extract
if CHECK_FROZEN_BASELINE:
    audit_rows += [
        audit_row("fact rows = frozen baseline", len(fact), frozen_baseline["rows"]),
        audit_row("instrument IDs", len(dim_instrument), frozen_baseline["instrument_ids"]),
        audit_row("observed execution dates", len(dim_date), frozen_baseline["execution_dates"]),
        audit_row("rows with reported notional",
                  int(fact["has_reported_notional"].sum()), frozen_baseline["rows_with_notional"]),
        audit_row("rows missing notional",
                  int((~fact["has_reported_notional"]).sum()), frozen_baseline["rows_missing_notional"]),
        audit_row("CANC rows",
                  int(fact["modification_flag"].eq("CANC").sum()), frozen_baseline["canc_rows"]),
    ]

audit = pd.DataFrame(audit_rows)
audit["actual"] = audit["actual"].astype(str)
audit["expected"] = audit["expected"].astype(str)
print(audit.to_string(index=False))

if not audit["passed"].all():
    raise ValueError("Audit failed - nothing written. Fix the failing check first.")


# -----------------------------------------------------------------------------
# 9E. Write Parquet files and manifest
# -----------------------------------------------------------------------------
# Parquet keeps column types (dates stay dates, numbers stay numbers),
# which is why it is used instead of CSV.
parquet_options = dict(engine="pyarrow", index=False,
                       coerce_timestamps="us", allow_truncated_timestamps=False)

outputs = {
    "fact_eid_published_rows": fact,
    "dim_instrument": dim_instrument,
    "dim_date": dim_date,
    "dim_mechanism": dim_mechanism,
    "dim_time_from": dim_time_from,
    "dim_time_to": dim_time_to,
    "eid_export_audit": audit,
}

for table_name, table in outputs.items():
    table.to_parquet(powerbi_folder / f"{table_name}.parquet", **parquet_options)
    print(f"Wrote {table_name}: {len(table):,} rows")

export_manifest = pd.DataFrame({
    "table": list(outputs),
    "rows": [len(t) for t in outputs.values()],
    "exported_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
})
export_manifest.to_csv(powerbi_folder / "export_manifest.csv", index=False)

print("\nTime dropdown range (UTC):",
      minutes["time_label_utc"].iloc[0], "to", minutes["time_label_utc"].iloc[-1])
print("Top 3 in dropdown:", dim_instrument["instrument_label"].head(3).tolist())
print("Export folder:", powerbi_folder.resolve())


# -----------------------------------------------------------------------------
# 9F. Verify: reload the written files and compare with Python
# -----------------------------------------------------------------------------
# The audit (9D) checks the tables BEFORE writing.
# This step checks the files AFTER writing, which is what Power BI will read.
# run_check comes from Section 8A, so results join the same PASS/FAIL list.
fact_reloaded = pd.read_parquet(powerbi_folder / "fact_eid_published_rows.parquet")

run_check("Parquet fact rows = Python fact rows", len(fact_reloaded) == len(fact),
          f"{len(fact_reloaded):,}")
run_check("Parquet quantity sum = Python quantity_num sum",
          abs(fact_reloaded["reported_quantity"].sum()
              - df_eid_working_combined["quantity_num"].sum()) < 1e-6)
run_check("Parquet instrument IDs = Python instrument IDs",
          fact_reloaded["MifidInstrumentID"].nunique()
          == df_eid_working_combined["MifidInstrumentID"].nunique())
run_check("Parquet timestamps still UTC (min and max unchanged)",
          fact_reloaded["exec_datetime_utc"].min() == fact["exec_datetime_utc"].min()
          and fact_reloaded["exec_datetime_utc"].max() == fact["exec_datetime_utc"].max())

manifest_check = pd.read_csv(powerbi_folder / "export_manifest.csv")
for table_name, table in outputs.items():
    reloaded_rows = len(pd.read_parquet(powerbi_folder / f"{table_name}.parquet"))
    run_check(f"File rows = manifest rows: {table_name}",
              reloaded_rows == int(manifest_check.loc[
                  manifest_check["table"] == table_name, "rows"].iloc[0]))


import sys

print(
    "Python version:",
    f"{sys.version_info.major}."
    f"{sys.version_info.minor}."
    f"{sys.version_info.micro}"
)
print("Python executable:", sys.executable)
