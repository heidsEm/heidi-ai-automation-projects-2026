import json
import logging
import os

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------- SSL WARNINGS ----------------
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

BACKUP_ROOT = "Apigee_Artifacts_Backup"
TIMEOUT = 30

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------- RETRY SESSION ----------------
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

# ---------------- BACKUP VIRTUAL HOSTS ----------------
def backup_virtual_hosts():
   logging.info("Backing up Virtual Hosts...")
   vh_dir = os.path.join(BACKUP_ROOT, "virtual_hosts")
   os.makedirs(vh_dir, exist_ok=True)

   try:
       vhosts = safe_get(f"{BASE_URL}/environments/{ENV}/virtualhosts").json()
       for vh in vhosts:
           detail = safe_get(f"{BASE_URL}/environments/{ENV}/virtualhosts/{vh}").json()
           with open(os.path.join(vh_dir, f"{vh}.json"), "w") as f:
               json.dump(detail, f, indent=4)
       logging.info(f"Backed up {len(vhosts)} virtual host(s)")
   except Exception as e:
       logging.error(f"Failed to backup Virtual Hosts: {e}")

# ---------------- BACKUP TARGET SERVERS ----------------
def backup_target_servers():
   logging.info("Backing up Target Servers...")
   target_dir = os.path.join(BACKUP_ROOT, "target_servers")
   os.makedirs(target_dir, exist_ok=True)

   try:
       servers = safe_get(f"{BASE_URL}/environments/{ENV}/targetservers").json()
       for server in servers:
           detail = safe_get(f"{BASE_URL}/environments/{ENV}/targetservers/{server}").json()
           with open(os.path.join(target_dir, f"{server}.json"), "w") as f:
               json.dump(detail, f, indent=4)
       logging.info(f"Backed up {len(servers)} target server(s)")
   except Exception as e:
       logging.error(f"Failed to backup Target Servers: {e}")

# ---------------- BACKUP KEYSTORES (Includes Truststores) ----------------
def backup_keystores():
   logging.info("Backing up Keystores and Certificates...")
   ks_dir = os.path.join(BACKUP_ROOT, "keystores")
   os.makedirs(ks_dir, exist_ok=True)

   try:
       keystores = safe_get(f"{BASE_URL}/environments/{ENV}/keystores").json()
       for ks in keystores:
           ks_path = os.path.join(ks_dir, ks)
           os.makedirs(ks_path, exist_ok=True)

           # Keystore Metadata
           ks_meta = safe_get(f"{BASE_URL}/environments/{ENV}/keystores/{ks}").json()
           with open(os.path.join(ks_path, "metadata.json"), "w") as f:
               json.dump(ks_meta, f, indent=4)

           # Aliases
           aliases = safe_get(f"{BASE_URL}/environments/{ENV}/keystores/{ks}/aliases").json()
           for alias_name in aliases:
               try:
                   alias_detail = safe_get(f"{BASE_URL}/environments/{ENV}/keystores/{ks}/aliases/{alias_name}").json()
                   with open(os.path.join(ks_path, f"{alias_name}.json"), "w") as f:
                       json.dump(alias_detail, f, indent=4)
               except Exception as e:
                   logging.warning(f"Could not export alias {alias_name} in {ks}: {e}")
       
       logging.info(f"Backed up {len(keystores)} keystore(s)")
   except Exception as e:
       logging.error(f"Failed to backup Keystores: {e}")

# ---------------- MAIN ----------------
def main():
   os.makedirs(BACKUP_ROOT, exist_ok=True)
   
   backup_virtual_hosts()
   backup_target_servers()
   backup_keystores()
   
   logging.info("--- All Artifacts Backed Up Successfully ---")

if __name__ == "__main__":
   main()