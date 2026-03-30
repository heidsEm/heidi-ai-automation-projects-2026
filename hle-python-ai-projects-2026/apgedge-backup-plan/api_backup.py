import csv
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------- SUPPRESS SSL WARNINGS ----------------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------- CONFIG ----------------
ORG = "pg-prod"
ENV = "prod"
BASE_URL = f"https://api.enterprise.apigee.com/v1/organizations/{ORG}"
TOKEN = "YOUR_OAUTH_TOKEN"

HEADERS = {
   "Authorization": f"Bearer {TOKEN}",
   "Accept": "application/json"
}

BACKUP_ROOT = "Apigee_Backup"
CSV_FILE = "apis.csv"
THREADS = 5
TIMEOUT = 30

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------- SESSION SETUP ----------------
def create_session():
   session = requests.Session()
   retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
   session.mount("https://", HTTPAdapter(max_retries=retries))
   return session

session = create_session()

def safe_get(url):
   r = session.get(url, headers=HEADERS, verify=False, timeout=TIMEOUT)
   r.raise_for_status()
   return r

# ---------------- KVM FETCH LOGIC (Fixed for 405) ----------------
def get_kvm_data(base_kvm_url, kvm_name):
   """
   Attempts to get KVM data. Handles the 405 by trying alternative endpoints.
   """
   # Try the standard entries endpoint first
   entries_url = f"{base_kvm_url}/{kvm_name}/entries"
   try:
       resp = session.get(entries_url, headers=HEADERS, verify=False, timeout=TIMEOUT)
       if resp.status_code == 200:
           return resp.json()
       
       # If 405, try getting it from the base KVM definition (Non-CPS style)
       if resp.status_code == 405:
           resp = session.get(f"{base_kvm_url}/{kvm_name}", headers=HEADERS, verify=False, timeout=TIMEOUT)
           if resp.status_code == 200:
               return resp.json().get('entry', resp.json()) # Return entries if present
   except Exception as e:
       logging.debug(f"Could not fetch entries for {kvm_name}: {e}")
   return None

# ---------------- EXPORT FUNCTIONS ----------------
def export_env_kvms():
   env_kvm_dir = os.path.join(BACKUP_ROOT, "_ENVIRONMENT_LEVEL", ENV, "kvms")
   os.makedirs(env_kvm_dir, exist_ok=True)
   try:
       url = f"{BASE_URL}/environments/{ENV}/keyvaluemaps"
       kvm_names = safe_get(url).json()
       for name in kvm_names:
           data = get_kvm_data(url, name)
           if data:
               with open(os.path.join(env_kvm_dir, f"{name}.json"), "w") as f:
                   json.dump(data, f, indent=4)
       logging.info(f"Environment KVMs for {ENV} backed up.")
   except Exception as e:
       logging.error(f"Env KVM Export Failed: {e}")

def export_api_kvms(api, api_path):
   kvm_dir = os.path.join(api_path, "kvm")
   url = f"{BASE_URL}/apis/{api}/keyvaluemaps"
   try:
       resp = session.get(url, headers=HEADERS, verify=False, timeout=TIMEOUT)
       if resp.status_code == 200:
           os.makedirs(kvm_dir, exist_ok=True)
           for name in resp.json():
               data = get_kvm_data(url, name)
               if data:
                   with open(os.path.join(kvm_dir, f"{name}.json"), "w") as f:
                       json.dump(data, f, indent=4)
   except Exception:
       pass

def export_api_products(api, api_path):
   product_dir = os.path.join(api_path, "api_product")
   os.makedirs(product_dir, exist_ok=True)
   try:
       # Optimization: In a real prod env, you'd cache this list once in main()
       all_products = safe_get(f"{BASE_URL}/apiproducts").json()
       for p_name in all_products:
           detail = safe_get(f"{BASE_URL}/apiproducts/{p_name}").json()
           if api in detail.get("proxies", []):
               with open(os.path.join(product_dir, f"{p_name}.json"), "w") as f:
                   json.dump(detail, f, indent=4)
   except Exception as e:
       logging.error(f"{api} product export error: {e}")

# ---------------- CORE BACKUP PROCESS ----------------
def backup_api(api):
   api = api.strip()
   if not api: return
   try:
       api_path = os.path.join(BACKUP_ROOT, api)
       meta = safe_get(f"{BASE_URL}/apis/{api}").json()
       revs = meta.get("revision", [])
       if not revs: return
       
       latest = revs[-1]
       bundle_dir = os.path.join(api_path, "bundle")
       os.makedirs(bundle_dir, exist_ok=True)

       # Download ZIP
       r = safe_get(f"{BASE_URL}/apis/{api}/revisions/{latest}?format=bundle")
       with open(os.path.join(bundle_dir, f"{api}_rev{latest}.zip"), "wb") as f:
           f.write(r.content)

       export_api_kvms(api, api_path)
       export_api_products(api, api_path)
       logging.info(f"[SUCCESS] {api}")
   except Exception as e:
       logging.error(f"[FAILED] {api}: {e}")

def main():
   os.makedirs(BACKUP_ROOT, exist_ok=True)
   export_env_kvms()
   
   if not os.path.exists(CSV_FILE):
       logging.error(f"{CSV_FILE} not found")
       return

   with open(CSV_FILE) as f:
       apis = [row[0].strip() for row in csv.reader(f) if row and row[0].strip() != "name"]

   logging.info(f"Starting backup for {len(apis)} proxies...")
   with ThreadPoolExecutor(max_workers=THREADS) as executor:
       executor.map(backup_api, apis)

if __name__ == "__main__":
   main()