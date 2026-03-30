import csv
import time

import pandas as pd
import requests

# ================= CONFIG =================
GITHUB_TOKEN = "YOUR_TOKEN"
REPO_OWNER = "REPO_OWNER"
REPO_NAME = "REPO_NAME"
WORKFLOW_FILE = "workflow.yaml"
BRANCH = "dev"

EXCEL_FILE = "gh-mig.xlsx"
LOG_FILE = "workflow_trigger_log.csv"
DELAY_SECONDS = 2
# ==========================================

# Read Excel
df = pd.read_excel(EXCEL_FILE)

# GitHub API endpoint
url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_FILE}/dispatches"

headers = {
   "Accept": "application/vnd.github+json",
   "Authorization": f"Bearer {GITHUB_TOKEN}"
}

# Create log file
with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as log_file:
   writer = csv.writer(log_file)
   writer.writerow(["Repository", "Container Key", "Status", "Message"])

   for index, row in df.iterrows():
       # Column A & B (safe positional access)
       repository = str(row.iloc[0]).strip()
       container_key = str(row.iloc[1]).strip()

       payload = {
           "ref": BRANCH,
           "inputs": {
               "repository": repository,
               "container-key": container_key
           }
       }

       try:
           response = requests.post(url, headers=headers, json=payload)

           if response.status_code == 204:
               status = "SUCCESS"
               message = "Workflow triggered"
               print(f"✅ {repository}")
           else:
               status = "FAILED"
               message = f"{response.status_code} - {response.text}"
               print(f"❌ {repository} ({response.status_code})")

       except Exception as e:
           status = "ERROR"
           message = str(e)
           print(f"❌ {repository} - Exception")

       writer.writerow([repository, container_key, status, message])
       time.sleep(DELAY_SECONDS)

print(f"\n✅ Done. Log saved to {LOG_FILE}")