import datetime
import subprocess
import os

# Define log file path
today = datetime.datetime.now().strftime("%Y-%m-%d")
log_file = os.path.join("logs", f"{today}.log")

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Run the screener script and capture output
with open(log_file, "a") as log:
    log.write(f"\n\n===== {datetime.datetime.now()} =====\n")
    subprocess.run(["python", "screenerv2.py"], stdout=log, stderr=log)
