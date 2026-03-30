import calendar
from datetime import datetime, timedelta

import pandas as pd
import requests

# ================ CONFIG ================
# You can get this by running the command in GCP Cloud Shell: gcloud auth print-access-token
ACCESS_TOKEN = "access_token"
# The Org name is usually the same as your GCP Project ID
ORG_ENV_MAP = {
   "gto-eai-apigeex-dev-211f": "apigeex-env-dev",
   "gto-eai-apigeex-qa-stg-a858": "apigeex-env-qa",
   "gto-eai-apigeex-prod-prod-82e2": "apigeex-env-prod"
}

CSV_FILE = "api_list.csv"
YEAR = 2025
OUTPUT_FILE = "apgx_api_traffic.xlsx"
# ========================================

def get_time_range(year, month):
   """Formats the time range as MM/DD/YYYY HH:MM~MM/DD/YYYY HH:MM for Stats API."""
   start = datetime(year, month, 1)
   if month == 12:
       end = datetime(year, 12, 31, 23, 59)
   else:
       end = datetime(year, month + 1, 1) - timedelta(minutes=1)
   return f"{start.strftime('%m/%d/%Y %H:%M')}~{end.strftime('%m/%d/%Y %H:%M')}"

def fetch_traffic_sum(org, env, time_range):
   """Calls the Apigee Stats API to get sum of message_count."""
   url = f"https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/stats/apiproxy"
   
   headers = {
       "Authorization": f"Bearer {ACCESS_TOKEN}",
       "Accept": "application/json"
   }
   
   # Filter removed to avoid syntax errors; limit added for completeness
   params = {
       "select": "sum(message_count)", 
       "timeRange": time_range,
       "limit": 1000 
   }

   try:
       response = requests.get(url, headers=headers, params=params)
       if response.status_code != 200:
           print(f"\n[!] Error {response.status_code} on {env}: {response.text}")
           return {}

       data = response.json()
       traffic_map = {}

       for env_stats in data.get("environments", []):
           for dimension in env_stats.get("dimensions", []):
               proxy_name = dimension.get("name")
               metrics = dimension.get("metrics", [])
               if metrics:
                   metric_values = metrics[0].get("values", [])
                   if metric_values:
                       raw_val = metric_values[0]
                       # Handle both string values and dictionary-wrapped values
                       val_str = raw_val.get("value", "0") if isinstance(raw_val, dict) else str(raw_val)
                       traffic_map[proxy_name] = int(float(val_str))
       return traffic_map
   except Exception as e:
       print(f"\n[!] Python Exception: {e}")
       return {}

def main():
   print(f"--- Starting Apigee X Traffic Extraction for {YEAR} ---")
   
   try:
       api_df_input = pd.read_csv(CSV_FILE)
       col_name = "api_name" if "api_name" in api_df_input.columns else api_df_input.columns[0]
       target_apis = sorted(api_df_input[col_name].unique().tolist())
   except Exception as e:
       print(f"Error reading CSV: {e}")
       return

   with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
       for org, env in ORG_ENV_MAP.items():
           print(f"\nProcessing Environment: {env}")
           
           # 1. Prepare base DataFrame
           df = pd.DataFrame({"API Name": target_apis})
           
           # 2. Fetch Monthly Data
           month_cols = []
           for month in range(1, 13):
               month_name = calendar.month_name[month]
               col_title = f"{month_name} Traffic"
               month_cols.append(col_title)
               
               tr = get_time_range(YEAR, month)
               print(f"  > Fetching {month_name}...", end="\r")
               
               monthly_stats = fetch_traffic_sum(org, env, tr)
               df[col_title] = df["API Name"].map(lambda x: monthly_stats.get(x, 0))

           # 3. Add Horizontal Totals (Annual per API)
           df["Total Annual Traffic"] = df[month_cols].sum(axis=1)

           # 4. Add Vertical Totals (Grand Total per Month)
           # Create a summary row dictionary
           totals_row = {"API Name": "GRAND TOTAL"}
           for col in month_cols + ["Total Annual Traffic"]:
               totals_row[col] = df[col].sum()
           
           # Append totals row using pd.concat
           df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True)

           # 5. Save Sheet
           df.to_excel(writer, sheet_name=env[:31], index=False)

   print(f"\n\nReport successfully generated: {OUTPUT_FILE}")

if __name__ == "__main__":
   main()