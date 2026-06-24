import subprocess
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

STEPS = [
    ("Step 1 - Data Cleaning",       "scripts/clean_data.py"),
    ("Step 2 - Data Transformation",  "scripts/transform_data.py"),
]

def run_step(label, script):
    log.info(f"\n{'='*50}\n  Running: {label}\n{'='*50}")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        log.error(f"❌ {label} FAILED")
        sys.exit(1)
    log.info(f"✅ {label} COMPLETE")

if __name__ == "__main__":
    log.info(f"🚀 Pipeline starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    for label, script in STEPS:
        run_step(label, script)
    log.info("🎉 Pipeline complete! Check data/cleaned/ and data/processed/")