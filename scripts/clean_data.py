import os
import logging
import hashlib
import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check
from datetime import datetime

os.makedirs("logs", exist_ok=True)
os.makedirs("data/cleaned", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline_run.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def drop_junk_columns(df, null_threshold=0.5):
    junk = [c for c in df.columns if c.startswith("col_")]
    df = df.drop(columns=junk, errors="ignore")
    null_ratio = df.isnull().mean()
    to_drop = null_ratio[null_ratio > null_threshold].index.tolist()
    if to_drop:
        log.warning(f"  Dropping high-null columns: {to_drop}")
        df = df.drop(columns=to_drop)
    return df


def clean_trend_report(path):
    log.info("=== Cleaning: trend_report ===")
    df = pd.read_csv(path)
    log.info(f"  Loaded {df.shape[0]} rows, {df.shape[1]} columns")
    df = drop_junk_columns(df)
    df["week"] = pd.to_datetime(df["week"] + "-1", format="%Y-W%W-%w", errors="coerce")
    df = df.dropna(subset=["week"])
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    df.to_csv("data/cleaned/trend_report_cleaned.csv", index=False)
    log.info(f"  Saved → data/cleaned/trend_report_cleaned.csv ({len(df)} rows)")
    return df


def clean_marketing_summary(path):
    log.info("=== Cleaning: marketing_summary ===")
    df = pd.read_csv(path)
    log.info(f"  Loaded {df.shape[0]} rows, {df.shape[1]} columns")
    df = drop_junk_columns(df)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    if "report_generated" in df.columns:
        df["report_generated"] = pd.to_datetime(df["report_generated"], errors="coerce")
    df = df.dropna(subset=["date"])
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].median())
    df.to_csv("data/cleaned/marketing_summary_cleaned.csv", index=False)
    log.info(f"  Saved → data/cleaned/marketing_summary_cleaned.csv ({len(df)} rows)")
    return df


VALID_EVENT_TYPES = {
    "checkout", "page_view", "wishlist_add", "add_to_cart",
    "login", "search", "profile_update"
}

def clean_event_logs(path):
    log.info("=== Cleaning: event_logs ===")
    df = pd.read_csv(path)
    log.info(f"  Loaded {df.shape[0]} rows, {df.shape[1]} columns")
    df = drop_junk_columns(df)
    df["event_time"] = pd.to_datetime(df["event_time"], format="%Y-%m-%d %H:%M", errors="coerce")
    df = df.dropna(subset=["user_id", "event_type", "event_time"])
    df = df.drop_duplicates(subset=["user_id", "event_type", "event_time"])
    df = df[df["event_type"].isin(VALID_EVENT_TYPES)]
    if "amount" in df.columns:
        df["amount"] = df["amount"].fillna(0.0)
    else:
        df["amount"] = 0.0
    df["user_id_masked"] = df["user_id"].apply(
        lambda uid: "U_" + hashlib.sha256(str(uid).encode()).hexdigest()[:8]
    )
    df.to_csv("data/cleaned/event_logs_cleaned.csv", index=False)
    log.info(f"  Saved → data/cleaned/event_logs_cleaned.csv ({len(df)} rows)")
    return df


if __name__ == "__main__":
    log.info(f"Pipeline started: {datetime.now()}")
    clean_trend_report("data/raw/trend_report.csv")
    clean_marketing_summary("data/raw/marketing_summary.csv")
    clean_event_logs("data/raw/event_logs.csv")
    log.info("✅ Cleaning complete")