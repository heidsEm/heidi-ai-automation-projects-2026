from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd
import requests
from tqdm import tqdm

# ================= CONFIG =================
# instructions on how to get an access_token can be found at README.MD 
ACCESS_TOKEN = "access-token-value"
OUTPUT_FILE = "apim_api_traffic.xlsx"

# subscription_id = Subscription ID, resource_group = Resource group, service_name = API Management service the following information are available under Azure APIM instances overview
ENVIRONMENTS = {
   "AZ-ENT-NONPROD": [
       {
           "subscription_id": "subscription_id-value",
           "resource_group": "resource_group-value",
           "service_name": "service_name-value"
       }
   ],
   "AZ-ENT-PROD": [
       {
           "subscription_id": "subscription_id-value",
           "resource_group": "resource_group-value",
           "service_name": "service_name-value"
       }
   ]
}

START_YEAR = 2025
END_YEAR = 2026

API_VERSION = "2024-05-01"

HEADERS = {
   "Authorization": f"Bearer {ACCESS_TOKEN}",
   "Content-Type": "application/json"
}

# ================= FUNCTIONS =================

def month_ranges(start_year, end_year):
   """Generate (start, end) tuples for each month between start_year and end_year"""
   current = datetime(start_year, 1, 1)
   end = datetime(end_year, 12, 31)
   months = []
   while current <= end:
       next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
       months.append((current, next_month - timedelta(seconds=1)))
       current = next_month
   return months

def fetch_apim_traffic(sub_id, rg, service, start_iso, end_iso):
   url = f"https://management.azure.com/subscriptions/{sub_id}/resourceGroups/{rg}/providers/Microsoft.ApiManagement/service/{service}/reports/byApi"
   params = {
       "$filter": f"timestamp ge datetime'{start_iso}' and timestamp le datetime'{end_iso}'",
       "api-version": API_VERSION
   }
   response = requests.get(url, headers=HEADERS, params=params)
   if response.status_code != 200:
       print(f"[!] Failed: {response.status_code} {response.text}")
       return []
   return response.json().get("value", [])

# ================= SCRIPT =================

writer = pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl")
months = month_ranges(START_YEAR, END_YEAR)
month_columns = [m[0].strftime("%b-%y") for m in months]

for env, instances in ENVIRONMENTS.items():
   print(f"\nProcessing Environment: {env}")
   traffic_data = defaultdict(lambda: defaultdict(int))

   for month_start, month_end in months:
       month_col = month_start.strftime("%b-%y")
       print(f"  Fetching {month_col}...")

       for instance in instances:
           sub_id = instance["subscription_id"]
           rg = instance["resource_group"]
           service = instance["service_name"]

           start_iso = month_start.isoformat() + "Z"
           end_iso = month_end.isoformat() + "Z"

           data = fetch_apim_traffic(sub_id, rg, service, start_iso, end_iso)

           for item in tqdm(data, desc=f"{env} {month_col}", unit="API"):
               api_name = item.get("name")
               call_total = item.get("callCountTotal", 0)
               if api_name:
                   traffic_data[api_name][month_col] += call_total

   if not traffic_data:
       print(f"[!] No traffic data found for {env}")
       continue

   df = pd.DataFrame.from_dict(traffic_data, orient="index").fillna(0)
   df.index.name = "API Name"
   df = df.reindex(columns=month_columns, fill_value=0)
   df["Total Traffic"] = df.sum(axis=1)
   df.to_excel(writer, sheet_name=env)

writer.close()
print(f"\n✅ Excel report generated: {OUTPUT_FILE}")