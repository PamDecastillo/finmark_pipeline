import os
import logging
import pandas as pd

os.makedirs("data/processed", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline_run.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def transform_marketing(path):
    log.info("=== Transforming: marketing_summary ===")
    df = pd.read_csv(path, parse_dates=["date"])
    df["sales_per_user"] = (df["total_sales"] / df["users_active"]).round(2)
    df = df.sort_values("date")
    df["sales_7d_avg"] = df["total_sales"].rolling(window=7, min_periods=1).mean().round(2)
    df["below_trend"] = df["total_sales"] < df["sales_7d_avg"]
    df.to_csv("data/processed/marketing_kpis.csv", index=False)
    log.info(f"  Saved → data/processed/marketing_kpis.csv ({len(df)} rows)")
    return df


def transform_events(path):
    log.info("=== Transforming: event_logs ===")
    df = pd.read_csv(path, parse_dates=["event_time"])
    df["event_date"] = df["event_time"].dt.date
    funnel = df.groupby(["event_date", "event_type"]).size().unstack(fill_value=0).reset_index()
    funnel.columns.name = None
    for col in ["page_view", "add_to_cart", "checkout"]:
        if col not in funnel.columns:
            funnel[col] = 0
    funnel["conversion_rate"] = (funnel["checkout"] / funnel["page_view"].replace(0, 1)).round(4)
    funnel.to_csv("data/processed/event_funnel_daily.csv", index=False)
    log.info(f"  Saved → data/processed/event_funnel_daily.csv ({len(funnel)} rows)")
    return funnel


def transform_trend(path):
    log.info("=== Transforming: trend_report ===")
    df = pd.read_csv(path, parse_dates=["week"])
    df["growth_flag"] = df["sales_growth_rate"].apply(
        lambda x: "Rising" if x > 0.05 else ("Falling" if x < -0.05 else "Stable")
    )
    df.to_csv("data/processed/trend_report_processed.csv", index=False)
    log.info(f"  Saved → data/processed/trend_report_processed.csv ({len(df)} rows)")
    return df


if __name__ == "__main__":
    transform_marketing("data/cleaned/marketing_summary_cleaned.csv")
    transform_events("data/cleaned/event_logs_cleaned.csv")
    transform_trend("data/cleaned/trend_report_cleaned.csv")
    log.info("✅ Transformation complete")