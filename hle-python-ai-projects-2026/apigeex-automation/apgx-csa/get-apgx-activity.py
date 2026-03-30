import time

import pandas as pd
import requests
from tqdm import tqdm

# ================= CONFIG =================
ACCESS_TOKEN = "ya29.a0ATkoCc5TiP0ybtpc03LbWiqEc4p4iuzF_bNsEy2ZwuwEkWIDUhVHxBsxv9-i9Fgwz5aihfHvxAabpHBZ63kM0cQuWAK_o4jY0jkZVqqAnhm_symt7Zf5zclQt6PPEmmK1nI4xwYYtPFofGURNueIQNCuMYsOPaXd87dwAc7AMhDJIWZtiiMN9Jt18aG0d104m46I2NTpj99FtGHFScIvm_x7Faxe_KojIm2I6KQZTMltm6M4cRATcSZMvl15vyQa2PaxGRYbp5RUI_4niNcJhqpEwCAbR8G2JHUAjrsFMIKcMoEQHx6CY1G5hPjD4ka_nAWiC8ZJqymw-5jbWwF_wiiC28O5ICRMW1O6QQaCgYKAXYSARUSFQHGX2MiCzJhYsdWQnfE0uhdwUJcWw0365"
PROJECT_ID = "gto-eai-apigeex-dev-211f"   # << define the specific project here
INPUT_FILE = "emails.xlsx"
EMAIL_COLUMN = "Email"
OUTPUT_FILE = "first_log_project.xlsx"
# ==========================================

LOGGING_API = "https://logging.googleapis.com/v2/entries:list"


def get_first_log(email):
   """Return the earliest log for the email in the specified project."""
   headers = {
       "Authorization": f"Bearer {ACCESS_TOKEN}",
       "Content-Type": "application/json"
   }

   filter_query = f'protoPayload.authenticationInfo.principalEmail="{email}"'

   body = {
       "resourceNames": [f"projects/{PROJECT_ID}"],
       "filter": filter_query,
       "orderBy": "timestamp asc",  # oldest first
       "pageSize": 1  # only need first log
   }

   # handle retries just in case
   for _ in range(3):
       resp = requests.post(LOGGING_API, headers=headers, json=body)
       if resp.status_code == 200:
           break
       print(f"Retrying for {email} due to error: {resp.text}")
       time.sleep(1)
   else:
       print(f"❌ Failed to get logs for {email}")
       return None

   data = resp.json()
   entries = data.get("entries", [])

   if not entries:
       return None

   entry = entries[0]
   payload = entry.get("protoPayload", {})

   return {
       "Email": email,
       "Project": PROJECT_ID,
       "First Log Timestamp": entry.get("timestamp"),
       "Service": payload.get("serviceName"),
       "Method": payload.get("methodName"),
       "Resource": payload.get("resourceName"),
       "Log Name": entry.get("logName"),
   }


def main():
   print(f"📂 Loading emails from {INPUT_FILE}...")
   df = pd.read_excel(INPUT_FILE)
   emails = df[EMAIL_COLUMN].dropna().unique()

   results = []

   for email in tqdm(emails, desc="Processing emails"):
       log = get_first_log(email)
       if log:
           results.append(log)
           print(f"✅ {email} → {log['First Log Timestamp']}")
       else:
           results.append({
               "Email": email,
               "Project": PROJECT_ID,
               "First Log Timestamp": "No logs found"
           })
           print(f"⚠️ {email} → No logs found")

   pd.DataFrame(results).to_excel(OUTPUT_FILE, index=False)
   print(f"\n🎉 Done! Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
   main()