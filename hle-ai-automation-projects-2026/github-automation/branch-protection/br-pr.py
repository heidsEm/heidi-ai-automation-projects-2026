import csv
import os
import time

import pandas as pd
import requests

# ================= CONFIG =================
GITHUB_TOKEN = "YOUR_TOKEN"
REPO_OWNER = "repo-owner"
BRANCH = "develop"

EXCEL_FILE = "apgx-repo.xlsx"
LOG_FILE = "branch_protection_log.csv"
DELAY_SECONDS = 1
# ==========================================

if not GITHUB_TOKEN:
   raise ValueError("❌ GITHUB_TOKEN environment variable not set")

headers = {
   "Accept": "application/vnd.github+json",
   "Authorization": f"Bearer {GITHUB_TOKEN}",
   "X-GitHub-Api-Version": "2022-11-28"
}

df = pd.read_excel(EXCEL_FILE)

with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as log_file:
   writer = csv.writer(log_file)
   writer.writerow(["Repository", "Status", "Message"])

   for _, row in df.iterrows():
       repo_name = str(row.iloc[0]).strip()

       url = f"https://api.github.com/repos/{REPO_OWNER}/{repo_name}/branches/{BRANCH}/protection/allow_deletions"

       try:
           # Disable branch deletion only
           response = requests.delete(url, headers=headers)

           if response.status_code in (204, 200):
               status = "SUCCESS"
               message = "Branch deletion disabled"
               print(f"✅ {repo_name}")
           else:
               status = "FAILED"
               message = f"{response.status_code} - {response.text}"
               print(f"❌ {repo_name} ({response.status_code})")

       except Exception as e:
           status = "ERROR"
           message = str(e)
           print(f"❌ {repo_name} - Exception")

       writer.writerow([repo_name, status, message])
       time.sleep(DELAY_SECONDS)

print(f"\n✅ Done. Log saved to {LOG_FILE}")