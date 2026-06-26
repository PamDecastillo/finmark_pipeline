
import pandas as pd
import os
import logging
import hashlib

# setup logging so we can see whats happening
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/resilient_pipeline.log"),
        logging.StreamHandler()
    ]
)

log = logging.getLogger(__name__)

# make output folders if they dont exist yet
os.makedirs("data/cleaned", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)


# -------------------------------------------------------
# HELPER: remove junk columns (col_4, col_5 etc)
# -------------------------------------------------------
def remove_junk_columns(df):
    # drop columns named col_something (unnamed columns from export)
    junk_cols = [c for c in df.columns if c.startswith("col_")]
    df = df.drop(columns=junk_cols, errors="ignore")

    # also drop columns that are more than 50% empty
    for col in df.columns:
        null_percent = df[col].isnull().mean()
        if null_percent > 0.5:
            log.info(f"Dropping {col} because it is {null_percent:.0%} empty")
            df = df.drop(columns=[col])

    return df


# -------------------------------------------------------
# HELPER: check if important columns are there
# -------------------------------------------------------
def check_columns(df, needed_cols, file_name):
    missing = []
    for col in needed_cols:
        if col not in df.columns:
            missing.append(col)
            log.warning(f"WARNING: {file_name} is missing column: {col}")

    if len(missing) == 0:
        log.info(f"{file_name} - all required columns found")

    return missing


# -------------------------------------------------------
# HELPER: fix missing columns instead of crashing
# -------------------------------------------------------
def fix_missing_columns(df, missing_cols, file_name):
    # default values we use when a column is missing
    defaults = {
        "amount":            0.0,
        "transaction_amount": 0.0,
        "total_sales":       0.0,
        "users_active":      0,
        "new_customers":     0,
        "sales_growth_rate": 0.0,
        "avg_users":         0,
        "product_id":        "UNKNOWN",
        "event_type":        "unknown",
    }

    for col in missing_cols:
        default_val = defaults.get(col, None)
        df[col] = default_val
        log.info(f"FIXED: added missing column '{col}' with default value: {default_val}")

    return df


# -------------------------------------------------------
# HELPER: check for bad/corrupted values
# -------------------------------------------------------
def fix_bad_values(df, file_name):
    # fix negative numbers (e.g. negative sales doesnt make sense)
    number_cols = df.select_dtypes(include="number").columns
    for col in number_cols:
        negative_rows = (df[col] < 0).sum()
        if negative_rows > 0:
            log.warning(f"WARNING: {file_name} column '{col}' has {negative_rows} negative values - setting to 0")
            df[col] = df[col].clip(lower=0)

    return df


# -------------------------------------------------------
# CLEAN TREND REPORT
# -------------------------------------------------------
def clean_trend_report():
    log.info("--- Starting trend_report cleaning ---")

    # try to load the file, if it fails just skip it
    try:
        df = pd.read_csv("data/raw/trend_report.csv")
        log.info(f"Loaded trend_report: {df.shape[0]} rows, {df.shape[1]} columns")
    except FileNotFoundError:
        log.error("ERROR: trend_report.csv not found - skipping")
        return

    # remove junk columns
    df = remove_junk_columns(df)

    # check if we have the columns we need
    needed = ["week", "avg_users", "sales_growth_rate"]
    missing = check_columns(df, needed, "trend_report")

    # if something is missing add a default column so we dont crash
    if missing:
        df = fix_missing_columns(df, missing, "trend_report")

    # fix any corrupted values
    df = fix_bad_values(df, "trend_report")

    # convert week column to proper date format
    try:
        df["week"] = pd.to_datetime(df["week"] + "-1", format="%Y-W%W-%w", errors="coerce")
    except Exception as e:
        log.warning(f"Could not parse week column: {e}")

    # fill empty numeric cells with the median
    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].fillna(df[col].median())

    # save the cleaned file
    df.to_csv("data/cleaned/trend_report_cleaned.csv", index=False)
    log.info(f"Saved cleaned trend_report: {len(df)} rows")


# -------------------------------------------------------
# CLEAN MARKETING SUMMARY
# -------------------------------------------------------
def clean_marketing_summary():
    log.info("--- Starting marketing_summary cleaning ---")

    try:
        df = pd.read_csv("data/raw/marketing_summary.csv")
        log.info(f"Loaded marketing_summary: {df.shape[0]} rows, {df.shape[1]} columns")
    except FileNotFoundError:
        log.error("ERROR: marketing_summary.csv not found - skipping")
        return

    df = remove_junk_columns(df)

    needed = ["date", "users_active", "total_sales", "new_customers"]
    missing = check_columns(df, needed, "marketing_summary")

    if missing:
        df = fix_missing_columns(df, missing, "marketing_summary")

    df = fix_bad_values(df, "marketing_summary")

    # convert date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # drop rows where we cant figure out the date
    before = len(df)
    df = df.dropna(subset=["date"])
    if before - len(df) > 0:
        log.warning(f"Dropped {before - len(df)} rows with invalid dates")

    # fill empty numeric cells
    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].fillna(df[col].median())

    df.to_csv("data/cleaned/marketing_summary_cleaned.csv", index=False)
    log.info(f"Saved cleaned marketing_summary: {len(df)} rows")


# -------------------------------------------------------
# CLEAN EVENT LOGS
# -------------------------------------------------------

# list of event types we accept
VALID_EVENTS = [
    "checkout",
    "page_view",
    "wishlist_add",
    "add_to_cart",
    "login",
    "search",
    "profile_update"
]

def clean_event_logs():
    log.info("--- Starting event_logs cleaning ---")

    try:
        df = pd.read_csv("data/raw/event_logs.csv")
        log.info(f"Loaded event_logs: {df.shape[0]} rows, {df.shape[1]} columns")
    except FileNotFoundError:
        log.error("ERROR: event_logs.csv not found - skipping")
        return

    df = remove_junk_columns(df)

    # check for required columns including amount (the problem column from the scenario)
    needed = ["user_id", "event_type", "event_time", "product_id", "amount"]
    missing = check_columns(df, needed, "event_logs")

    # if amount column is missing we add it with 0 instead of crashing
    if missing:
        df = fix_missing_columns(df, missing, "event_logs")

    df = fix_bad_values(df, "event_logs")

    # convert event_time to datetime
    df["event_time"] = pd.to_datetime(df["event_time"], errors="coerce")

    # drop rows missing critical info
    before = len(df)
    df = df.dropna(subset=["user_id", "event_type", "event_time"])
    log.info(f"Dropped {before - len(df)} rows with missing key fields")

    # remove duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["user_id", "event_type", "event_time"])
    log.info(f"Removed {before - len(df)} duplicate rows")

    # remove unknown event types
    before = len(df)
    df = df[df["event_type"].isin(VALID_EVENTS)]
    log.info(f"Removed {before - len(df)} rows with unknown event types")

    # fill empty amounts with 0
    df["amount"] = df["amount"].fillna(0.0)

    # hide user IDs for privacy using hashing
    df["user_id_masked"] = df["user_id"].apply(
        lambda x: "U_" + hashlib.sha256(str(x).encode()).hexdigest()[:8]
    )

    df.to_csv("data/cleaned/event_logs_cleaned.csv", index=False)
    log.info(f"Saved cleaned event_logs: {len(df)} rows")


# -------------------------------------------------------
# TRANSFORM - add KPIs and metrics
# -------------------------------------------------------
def transform_data():
    log.info("--- Starting transformations ---")

    # marketing KPIs
    try:
        df = pd.read_csv("data/cleaned/marketing_summary_cleaned.csv", parse_dates=["date"])
        df = df.sort_values("date")

        # sales per user
        df["sales_per_user"] = (df["total_sales"] / df["users_active"].replace(0, 1)).round(2)

        # 7 day rolling average
        df["sales_7d_avg"] = df["total_sales"].rolling(window=7, min_periods=1).mean().round(2)

        # flag days where sales dropped below average
        df["below_trend"] = df["total_sales"] < df["sales_7d_avg"]

        df.to_csv("data/processed/marketing_kpis.csv", index=False)
        log.info(f"Saved marketing_kpis: {len(df)} rows")

    except Exception as e:
        log.error(f"ERROR in marketing transform: {e}")

    # event funnel
    try:
        df = pd.read_csv("data/cleaned/event_logs_cleaned.csv", parse_dates=["event_time"])
        df["event_date"] = df["event_time"].dt.date

        funnel = df.groupby(["event_date", "event_type"]).size().unstack(fill_value=0).reset_index()
        funnel.columns.name = None

        # make sure these columns exist even if no data
        if "page_view" not in funnel.columns:
            funnel["page_view"] = 0
        if "checkout" not in funnel.columns:
            funnel["checkout"] = 0

        funnel["conversion_rate"] = (
            funnel["checkout"] / funnel["page_view"].replace(0, 1)
        ).round(4)

        funnel.to_csv("data/processed/event_funnel_daily.csv", index=False)
        log.info(f"Saved event_funnel_daily: {len(funnel)} rows")

    except Exception as e:
        log.error(f"ERROR in event funnel transform: {e}")

    # trend growth flags
    try:
        df = pd.read_csv("data/cleaned/trend_report_cleaned.csv", parse_dates=["week"])

        def get_growth_flag(rate):
            if rate > 0.05:
                return "Rising"
            elif rate < -0.05:
                return "Falling"
            else:
                return "Stable"

        df["growth_flag"] = df["sales_growth_rate"].apply(get_growth_flag)

        df.to_csv("data/processed/trend_report_processed.csv", index=False)
        log.info(f"Saved trend_report_processed: {len(df)} rows")

    except Exception as e:
        log.error(f"ERROR in trend transform: {e}")


# -------------------------------------------------------
# RUN EVERYTHING
# -------------------------------------------------------
if __name__ == "__main__":
    log.info("========================================")
    log.info("  FinMark Pipeline - Milestone 2 Draft 2")
    log.info("  Group 5 A3101")
    log.info("========================================")

    clean_trend_report()
    clean_marketing_summary()
    clean_event_logs()
    transform_data()

    log.info("========================================")
    log.info("  Pipeline done! Check data/cleaned/")
    log.info("  and data/processed/ for output files")
    log.info("========================================")