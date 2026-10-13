# Euronext Equity & Index Derivatives
## Published Post-Trade Activity, Concentration and Data Quality

A Python and Power BI analysis investigating whether instruments that dominate Euronext post-trade publication counts also dominate reported quantity and notional.

The project examines instrument concentration, reported-notional availability, intraday observations and market-mechanism patterns. Python prepares and validates the data; Power BI provides interactive exploration by instrument, execution date and UTC time window.

> The analytical unit is a published post-trade report row, not a guaranteed unique economic trade. The analysis is descriptive and does not measure liquidity, market power, comparable economic exposure or causal price effects.

## Project at a Glance

| Item | Detail |
|---|---|
| Market | Euronext Equity & Index Derivatives |
| Source | Delayed MiFID II / MiFIR post-trade CSV files |
| Published records | 435,535 |
| Instrument IDs | 6,036 |
| Observed execution dates | 11 |
| Observation period | 16 September–1 October 2026, observed dates only |
| Preparation and analysis | Python and Pandas |
| Reporting | Power BI Desktop |
| Data exchange | Parquet |
| Time convention | UTC |

The observed execution dates are 16, 17, 18, 21, 22, 23, 24, 25, 28 and 30 September, and 1 October 2026. The extract does not contain 29 September; its absence does not establish that no market activity occurred that day.

## Analytical Questions

- Does high publication frequency imply a similarly large contribution to reported quantity or notional?
- How does instrument concentration differ between records, quantity and reported notional?
- Is unavailable notional dispersed across instruments or concentrated in specific IDs and dates?
- Can mechanisms with few publications contribute substantial reported quantity?
- What reported price and quantity observations appear within a selected instrument’s execution window?

## Key Findings

### Publication frequency, quantity and notional tell different stories

Across the complete 11-date extract, `FREX03591036` leads on all three measures, but its shares differ substantially:

| Measure | Instrument total | Extract total | Instrument share |
|---|---:|---:|---:|
| Published records | 356,510 | 435,535 | 81.86% |
| Reported quantity | 464,362 | 1,765,726 | 26.30% |
| Reported notional, EUR | 37,448,213,811.40 | 52,573,070,953.67 | 71.23% |

Publication frequency is therefore not interchangeable with quantity contribution or reported monetary contribution.

The notional percentage describes available reported amounts, not a complete economic total that includes unknown amounts.

### Missing notional is concentrated by instrument and date

- 16,692 records, or 3.83% of the extract, have no numeric reported notional.
- These records belong to 688 instrument IDs.
- All 688 have entirely unavailable numeric notional across their observed rows; no partially unavailable IDs were found.
- Approximately 90.63% of unavailable-notional records occur on 16–17 September.
- Numeric-notional records were verified as EUR-only, with no missing notional currency.

| Execution date | Published records | Records without numeric notional | Unavailable share |
|---|---:|---:|---:|
| 16 Sep 2026 | 50,241 | 9,313 | 18.54% |
| 17 Sep 2026 | 46,910 | 5,815 | 12.40% |
| 18 Sep 2026 | 48,352 | 809 | 1.67% |
| 21 Sep 2026 | 28,779 | 109 | 0.38% |
| 22 Sep 2026 | 33,476 | 100 | 0.30% |
| 23 Sep 2026 | 28,161 | 96 | 0.34% |
| 24 Sep 2026 | 31,118 | 71 | 0.23% |
| 25 Sep 2026 | 32,267 | 87 | 0.27% |
| 28 Sep 2026 | 34,891 | 61 | 0.17% |
| 30 Sep 2026 | 39,752 | 82 | 0.21% |
| 1 Oct 2026 | 61,588 | 149 | 0.24% |

These findings describe the observed reporting pattern; they do not establish why notional is unavailable.

### Selected-day example: 18 September 2026

For `FREX03591036`, full day and all mechanisms:

- 43,438 published records: 89.84% of the day’s 48,352 records.
- 56,010 reported quantity: 27.87% of the day’s 200,988 quantity.
- The Top 3 quantity leaders contribute 96,010, or 47.77% of the daily total.
- Within the selected instrument, one Off Book publication contributes quantity 700, approximately 1.25% of its daily quantity.

| Quantity leader | Reported quantity | Share of daily quantity |
|---|---:|---:|
| `FREX03591036` | 56,010 | 27.87% |
| `FREX03468201` | 25,000 | 12.44% |
| `FREX03474167` | 15,000 | 7.46% |
| All other instruments | 104,978 | 52.23% |

The second leader contributes its quantity through three records, and the third through one record. Sparse publication can therefore coexist with a substantial reported-quantity contribution.

## Dashboard Features

- Instrument, execution-date and UTC From/To selectors.
- KPI cards for reported quantity, reported notional, published records and mean reported price.
- An intraday reported-price and quantity panel.
- Selected-instrument Quantity and Notional Availability tabs.
- Dynamic Top 3 concentration tabs for records, quantity and reported notional.
- A publication-level observations table and selected-window record count.
- A market-mechanism matrix comparing quantity and record shares.
- A takeaway panel distinguishing selected-day observations from whole-extract context.

The dashboard uses a mock-up as a visual style reference, not as a source of numerical results.

## Explore the Power BI Dashboard

1. Download `Equity_Index_Derivatives Dashboard.pbix`.
2. Open it in Power BI Desktop.
3. Select an instrument and execution date.
4. Choose a UTC time window, or leave the endpoints on All.
5. Use the panel tabs to change the displayed metric.

The PBIX contains an imported data snapshot. Separate Parquet files are not required to explore that snapshot.

In Power BI Desktop edit mode, use Ctrl+click to activate bookmark navigator buttons.

GitHub hosts the file for download; it does not display the PBIX as an interactive dashboard in the browser.

### Refreshing the report

To refresh rather than simply explore the saved snapshot:

1. Download all seven Parquet files.
2. Keep them together in a local directory.
3. Open the PBIX in Power BI Desktop.
4. In Power Query, update the queries’ source paths to the local Parquet files.
5. Apply the changes and refresh.

The report’s original connections reference the author’s local filesystem. Uploading the files to GitHub does not automatically update those connections.

## Files Included

The files currently sit together in this project folder.

| File | Purpose |
|---|---|
| `README.md` | Project overview, findings, methodology and usage |
| `Equity_Index_Derivative_Analysis.py` | Python preparation, analysis, validation and export workflow |
| `Equity_Index_Derivatives Dashboard.pbix` | Power BI report with its imported data snapshot |
| Dashboard PNG files | Static dashboard previews |
| `fact_eid_published_rows.parquet` | One row per published post-trade report |
| `dim_instrument.parquet` | Instrument selector and descriptive metadata |
| `dim_date.parquet` | Observed execution dates |
| `dim_mechanism.parquet` | Market-mechanism codes and labels |
| `dim_time_from.parquet` | UTC start-minute selector |
| `dim_time_to.parquet` | UTC end-minute selector |
| `eid_export_audit.parquet` | Export audit results |
| `export_manifest.csv` | Exported table names, row counts and export timestamp |

Original daily source CSVs are not included.

## Workflow

```text
Manually downloaded Euronext CSVs
                |
                v
Validate source column names and order
                |
                v
Combine accepted files into an unchanged raw dataframe
                |
                v
Prepare a separate working dataframe
                |
                v
Analyse concentration, availability and mechanisms
                |
                v
Reconcile analytical totals
                |
                v
Build and audit the reporting model
                |
                v
Write Parquet files and export manifest
                |
                v
Load into Power BI and calculate interactive DAX measures
                |
                v
Check selected dashboard results against Python
```

The repeatable pipeline begins after manual source acquisition. It does not automatically download data from Euronext.

## Python Analysis

The script develops the analysis in nine sections:

| Section | Main purpose |
|---|---|
| Setup | Folder configuration, source-reading settings and analytical objectives |
| Import | Validate the expected 27-column schema and combine accepted CSVs |
| Preparation | Preserve raw fields and create UTC and numeric analytical fields |
| Record concentration | Instrument counts, daily rankings, CR1 and CR3 |
| Notional coverage | Availability by instrument/date and reported sums |
| Market mechanisms | Compare publication counts and reported quantity by mechanism |
| Quantity analysis | Compare quantity rankings with record-count rankings |
| Checks and figures | Reconciliation, exploratory charts and reference slices |
| Power BI export | Reporting tables, audit, Parquet writing and read-back verification |

Rejected files are reported explicitly. If some files pass and others fail, accepted files can still be consolidated; review the validation output before treating the run as a complete ingestion.

Numeric conversion distinguishes source missingness from nonblank values that fail parsing. “No numeric notional” therefore does not automatically mean an original blank.

## Power BI Model

Three single-direction dimension-to-fact relationships connect:

- `dim_instrument` to `fact_eid_published_rows`.
- `dim_date` to `fact_eid_published_rows`.
- `dim_mechanism` to `fact_eid_published_rows`.

The From and To tables remain disconnected. DAX measures read their selections and apply the execution-minute interval.

A disconnected donut-category table supplies instrument IDs and the categories `All other instruments` and `Notional N/A`. Measures determine which categories receive values.

### Timestamp fields

| Field | Role |
|---|---|
| `exec_datetime_utc` | Intraday datetime plotting |
| `exec_date` | Execution-date filtering |
| `exec_minute_of_day_utc` | Integer time-window comparisons |
| `exec_time_text_utc` | Readable execution time with microseconds |

Exact timestamp text is preserved for inspection, but the implemented time selectors operate at minute boundaries.

## Calculation Logic

### Window-aware statistics

`Rows In Time Window` counts published rows between the selected From and To minutes. Quantity, notional and price measures follow the same window pattern.

- Minute bounds are inclusive.
- From 13:50 to To 13:59 represents `[13:50, 14:00)` UTC.
- An invalid From > To interval returns blank.
- With no single selected endpoint, measures use the endpoint fallback.
- Disconnected time selectors only affect calculations that explicitly read them.

### Selected-instrument shares

- Record share = selected published rows / all published rows in the same context.
- Quantity share = selected reported quantity / all-ID reported quantity in the same context.
- Reported-notional share = selected available amount / all-ID available amounts in the same context.

The all-ID denominator removes the instrument-dimension filter while preserving execution date, time window and applicable mechanism context.

### Notional availability is not a monetary share

The selected Notional Availability ring uses published rows as its unit:

- Selected-instrument rows with numeric notional.
- Other-instrument rows with numeric notional.
- All rows without numeric notional.

The cards beneath the ring show monetary reported amounts.

For 17 September 2026, `FREX03591036`, full day and all mechanisms:

| Ring category | Share of published rows |
|---|---:|
| Selected instrument with numeric notional | 46.21% |
| Other instruments with numeric notional | 41.39% |
| Notional unavailable | 12.40% |

The accompanying amounts are approximately EUR 2.64bn selected and EUR 2.70bn other. The selected monetary share is separately 49.50%.

These are different, valid statistics with different units and denominators.

### Top 3 concentration

Each concentration tab ranks instruments independently by its own metric.

The calculation removes the selected-instrument filter, evaluates the metric for each ID, retains positive nonblank totals and selects up to three leaders. Metric ties are broken by instrument ID.

The donut shows three actual IDs plus the remainder. The card shows the combined Top 3 share.

Fewer than four slices can be valid if fewer than three instruments qualify or the remainder is zero.

### Mechanism shares

Mechanism denominators remove the mechanism-dimension filter while preserving the selected instrument, date and window.

| Code | Label |
|---|---|
| 1 | Central Limit Order Book |
| 4 | Off Book |
| 5 | Periodic Auction |
| 8 | Hybrid System |

Codes 1, 4 and 5 follow the documented FIX MMT reference. Code 8 follows the Euronext Optiq MDG MMT field reference; it must not be confused with the separate EMM code system.

### Price statistics

Mean reported price is an equal-weight arithmetic mean of numeric price observations within the selected scope. It is not VWAP or an official closing price.

Reported highs and lows are extremes among the included publication rows, not automatically official session highs and lows.

## Validation

Python reference checks cover:

- Raw rows against accepted source-file rows.
- Working rows against raw rows.
- Instrument and daily counts against population totals.
- Notional availability counts against published rows.
- Quantity sums and selected-instrument shares.
- Exported rows against the reporting model and manifest.
- Selected dashboard values under matching date, time and mechanism contexts.

A benchmark for `FREX03591036` on 18 September 2026 returned 1,233 rows for the interval `[13:50, 14:00)` UTC.

The latest whole-extract checks reported:

- No unavailable quantity.
- No negative quantity or notional.
- EUR-only currency among numeric-notional rows.
- No missing currency among those rows.
- Reconciled instrument-row, daily-unavailability and affected-ID totals.

The manifest dated 11 October 2026 records:

| Exported table | Rows |
|---|---:|
| `fact_eid_published_rows` | 435,535 |
| `dim_instrument` | 6,036 |
| `dim_date` | 11 |
| `dim_mechanism` | 4 |
| `dim_time_from` | 840 |
| `dim_time_to` | 840 |
| `eid_export_audit` | 15 |

The manifest records export metadata; it does not alone prove that every verification passed.

## Run the Python Workflow

### Reported working environment

| Component | Version |
|---|---|
| Operating system | Windows 11 |
| Python | 3.14.5 |
| IDE | PyCharm 2026.1.5 |
| Pandas | 3.0.5 |
| Matplotlib | 3.11.2 |
| PyArrow | 25.0.1 |

These are the author’s reported working versions. Installation has not been independently tested on a clean machine.

`pathlib`, `datetime` and `sys` are included with Python. The separate `pathlib2` package is not required by the supplied script.

### Install dependencies

```bash
python -m pip install pandas==3.0.5 matplotlib==3.11.2 pyarrow==25.0.1
```

### Local execution layout

The repository’s uploaded file layout is separate from the directory structure used by the Python pipeline:

```text
<PROJECT_ROOT>/
├── data/
│   ├── raw/
│   └── powerbi/
└── output/
    ├── tables/
    └── figures/
```

Set the existing `project_folder` assignment in the script to the directory you want to use.

The author’s working configuration is:

```python
project_folder = Path(r"C:\Users\sudha\Desktop\Python Projects")

raw_data_folder = project_folder / "data" / "raw"
tables_folder = project_folder / "output" / "tables"
figures_folder = project_folder / "output" / "figures"
```

Change the project-root path for your own machine. The script itself can be stored in a separate directory.

### Execution

1. Obtain compatible Equity & Index Derivatives source CSVs.
2. Place them in `<PROJECT_ROOT>/data/raw/`.
3. Configure `project_folder`.
4. Run:

```bash
python Equity_Index_Derivative_Analysis.py
```

5. Review validation and reconciliation messages.
6. If execution waits while Matplotlib chart windows are open, close them to continue.
7. Inspect the generated outputs and export checks.

The Power BI exports are written to `<PROJECT_ROOT>/data/powerbi/`.

### Updating the extract

Add compatible daily CSVs to the raw-data folder and rerun the pipeline.

Structural export checks run each time. Optional frozen-baseline checks are controlled by `CHECK_FROZEN_BASELINE`, set to `False` in the supplied script. Enable them only when reproducing the original baseline.

New files change population counts and results. Repeat currency, sign, availability and reconciliation checks after updates.

Reproducing the exact historical figures requires the original source-file collection. The current download page should not be assumed to provide a complete historical archive.

## Methodology and Interpretation Limits

- Publication rows are not guaranteed unique trades.
- Cancellation reports and repeated trade identifiers are retained.
- Missing reported notional remains unavailable, not zero.
- Notional is not universally reconstructed as price multiplied by quantity.
- Quantities across different derivative contracts are descriptive, not common exposure.
- Execution and publication timestamps are distinct.
- Currency compatibility is checked for the loaded extract, not assumed for future files.
- Mechanism codes describe reported categories, not causes.
- Shared timestamps can lead to visual aggregation; the intraday chart should not automatically be treated as one point per publication.
- Static takeaway statements require an explicit date or whole-extract scope.
- A share rounded to 0.00% can still represent actual records.
- Percentage measures store ratios; percentage formatting changes their display.
- Row keys identify exported publication rows and are not persistent economic-trade identifiers.
- Negative values in future files require review before using proportional donuts.
- Some no-selection and empty-window states require explicit handling.

## Development Lessons

The implementation exposed several useful analytical and reporting lessons:

- A disconnected legend requires slice-aware measures; repeating one ratio across categories can produce a misleading 50/50 donut.
- A visual using an ordinary count can ignore disconnected time selectors.
- Removing too many filters can change the intended population or assign every ranked ID the same total.
- A displayed decimal can be a formatting issue rather than a calculation error.
- Unavailable-row counts cannot be mixed with euro amounts in one monetary donut.
- Bookmark groups control available buttons; selected-visual scope controls which objects a bookmark restores.
- Summing reported prices is not an informative substitute for a mean or reported range.

These corrections informed the final model, denominator definitions and dashboard design.

## Data Source and Usage

Source: [Euronext Trades files](https://marketdata.euronext.com/data-reporting-service/trades-file).

The repository includes derived Parquet tables and a PBIX containing imported data. Original source CSVs are not included.

Consult the applicable Euronext terms before reusing or redistributing the source or derived data. Availability for download does not imply unrestricted redistribution rights.

Sharing a populated PBIX also shares its imported data. Omitting separate source files does not remove that consideration.

Any licence applied to this project’s code does not grant additional rights over Euronext data.

## Current Scope

This is a local Python-to-Power-BI workflow with an imported reporting snapshot.

- Power BI Service refresh of local files is not configured.
- A custom dashboard export button was explored but not implemented.
- Screenshots are static previews; interactive exploration requires Power BI Desktop.
- Some label, scope and edge-case refinements remain areas for improvement.

## Purpose

This project demonstrates analyst-led data preparation, transparent missing-data treatment, denominator-aware calculations, independent validation and interactive reporting.

Its central conclusion is that publication frequency, reported quantity and reported notional offer complementary—not interchangeable—views of the same post-trade extract.
