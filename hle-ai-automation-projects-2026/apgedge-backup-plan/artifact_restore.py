import json
import logging
import os

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------- CONFIG ----------------
ORG = "pg-prod"
ENV = "prod"

BASE_URL = f"https://api.enterprise.apigee.com/v1/organizations/{ORG}"

TOKEN = "YOUR_OAUTH_TOKEN"

HEADERS = {
   "Authorization": f"Bearer {TOKEN}",
   "Content-Type": "application/json"
}

BACKUP_ROOT = "Apigee_Artifacts_Backup"

TIMEOUT = 30

logging.basicConfig(
   level=logging.INFO,
   format="%(asctime)s [%(levelname)s] %(message)s"
)

# ---------------- RETRY SESSION ----------------
def create_session():

   session = requests.Session()

   retries = Retry(
       total=5,
       backoff_factor=1,
       status_forcelist=[500,502,503,504]
   )

   adapter = HTTPAdapter(max_retries=retries)

   session.mount("https://", adapter)

   return session

session = create_session()

# ---------------- SAFE POST ----------------
def safe_post(url, **kwargs):

   r = session.post(
       url,
       headers=HEADERS,
       verify=False,
       timeout=TIMEOUT,
       **kwargs
   )

   if r.status_code not in [200,201]:

       logging.warning(f"{url} -> {r.text}")

   return r


# ---------------- RESTORE TARGET SERVERS ----------------
def restore_target_servers():

   path = os.path.join(BACKUP_ROOT, "target_servers")

   if not os.path.exists(path):
       return

   logging.info("Restoring Target Servers")

   for file in os.listdir(path):

       with open(os.path.join(path, file)) as f:

           data = json.load(f)

       safe_post(
           f"{BASE_URL}/environments/{ENV}/targetservers",
           json=data
       )


# ---------------- RESTORE KEYSTORES ----------------
def restore_keystores():

   ks_root = os.path.join(BACKUP_ROOT, "keystores")

   if not os.path.exists(ks_root):
       return

   logging.info("Restoring Keystores")

   for ks in os.listdir(ks_root):

       safe_post(
           f"{BASE_URL}/environments/{ENV}/keystores",
           json={"name": ks}
       )


# ---------------- RESTORE CERTIFICATES ----------------
def restore_certificates():

   ks_root = os.path.join(BACKUP_ROOT, "keystores")

   for ks in os.listdir(ks_root):

       ks_path = os.path.join(ks_root, ks)

       for cert_file in os.listdir(ks_path):

           cert_path = os.path.join(ks_path, cert_file)

           alias = cert_file.replace(".pem","")

           with open(cert_path) as f:
               cert_data = f.read()

           logging.info(f"Uploading certificate {alias}")

           safe_post(
               f"{BASE_URL}/environments/{ENV}/keystores/{ks}/aliases",
               json={
                   "alias": alias,
                   "cert": cert_data
               }
           )


# ---------------- MAIN ----------------
def main():

   restore_target_servers()
   restore_keystores()
   restore_certificates()

   logging.info("Artifact restore completed")


if __name__ == "__main__":
   main()