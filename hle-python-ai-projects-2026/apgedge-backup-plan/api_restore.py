import json
import logging
import os

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
   "Content-Type": "application/json"
}

BACKUP_ROOT = "Apigee_Backup"
TIMEOUT = 30

# ---------------- LOGGING ----------------
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

# ---------------- SAFE REQUEST ----------------
def safe_post(url, **kwargs):

   r = session.post(
       url,
       headers=HEADERS,
       verify=False,
       timeout=TIMEOUT,
       **kwargs
   )

   r.raise_for_status()

   return r


# ---------------- IMPORT PROXY ----------------
def import_proxy(api, bundle_file):

   logging.info(f"{api} -> importing proxy")

   url = f"{BASE_URL}/apis?action=import&name={api}"

   with open(bundle_file, "rb") as f:

       files = {"file": f}

       r = session.post(
           url,
           headers={"Authorization": f"Bearer {TOKEN}"},
           files=files,
           verify=False
       )

   r.raise_for_status()

   revision = r.json()["revision"]

   logging.info(f"{api} -> imported revision {revision}")

   return revision


# ---------------- DEPLOY PROXY ----------------
def deploy_proxy(api, revision):

   logging.info(f"{api} -> deploying revision {revision}")

   url = f"{BASE_URL}/environments/{ENV}/apis/{api}/revisions/{revision}/deployments"

   safe_post(url)


# ---------------- RESTORE API PRODUCT ----------------
def restore_products(product_folder):

   for file in os.listdir(product_folder):

       file_path = os.path.join(product_folder, file)

       with open(file_path) as f:
           data = json.load(f)

       logging.info(f"Creating API Product {data['name']}")

       try:

           safe_post(f"{BASE_URL}/apiproducts", json=data)

       except Exception as e:

           logging.warning(f"Product may already exist: {data['name']}")


# ---------------- RESTORE KVM ----------------
def restore_kvms(kvm_file):

   with open(kvm_file) as f:

       kvms = json.load(f)

   for kvm_name, entries in kvms.items():

       logging.info(f"Creating KVM {kvm_name}")

       try:

           safe_post(
               f"{BASE_URL}/environments/{ENV}/keyvaluemaps",
               json={"name": kvm_name}
           )

       except:
           logging.warning(f"KVM already exists: {kvm_name}")

       for entry in entries:

           key = entry["name"]
           value = entry["value"]

           entry_url = f"{BASE_URL}/environments/{ENV}/keyvaluemaps/{kvm_name}/entries"

           safe_post(
               entry_url,
               json={"name": key, "value": value}
           )


# ---------------- RESTORE API ----------------
def restore_api(api_folder):

   api = os.path.basename(api_folder)

   logging.info(f"Restoring {api}")

   bundle_folder = os.path.join(api_folder, "bundle")

   for file in os.listdir(bundle_folder):

       bundle_file = os.path.join(bundle_folder, file)

       revision = import_proxy(api, bundle_file)

       deploy_proxy(api, revision)

   product_folder = os.path.join(api_folder, "api_product")

   if os.path.exists(product_folder):

       restore_products(product_folder)

   kvm_folder = os.path.join(api_folder, "kvm")

   if os.path.exists(kvm_folder):

       for file in os.listdir(kvm_folder):

           restore_kvms(os.path.join(kvm_folder, file))


# ---------------- MAIN ----------------
def main():

   for api in os.listdir(BACKUP_ROOT):

       api_path = os.path.join(BACKUP_ROOT, api)

       if os.path.isdir(api_path):

           restore_api(api_path)

   logging.info("Restore completed")


if __name__ == "__main__":
   main()