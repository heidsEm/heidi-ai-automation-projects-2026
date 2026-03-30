import base64
import csv
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

# ================= CONFIG =================
ORG = "" #ORG NAME
PROJECT = "" #Project GUID # Project GUID https://dev.azure.com/ITS-EAI/_apis/projects?api-version=7.0%0A
PAT = ""  # Azure DevOps Personal Access Token

API_VERSION = "7.1"
TIMEOUT = 60
EXCEL_FILE = "input.xlsx"
LOG_FILE = "repo_cleanup_log.csv"
DELAY = 0.2
DELETE_VALIDATION = True
MAX_LEASE_RETRIES = 6
DELETE_OLD_BUILDS_DAYS = 180  # Delete builds older than this if blocking CI deletion

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# ================= AUTH =================
AUTH = base64.b64encode(f":{PAT}".encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH}", "Content-Type": "application/json"}

# ================= RELEASE/CD =================
def get_release_definition_id(name):
   url = f"https://vsrm.dev.azure.com/{ORG}/{PROJECT}/_apis/release/definitions?api-version={API_VERSION}"
   r = requests.get(url, headers=HEADERS)
   r.raise_for_status()
   for d in r.json().get("value", []):
       if d["name"] == name:
           return d["id"]
   return None

def delete_release_definition_force(def_id):
   """Force delete Release/CD pipeline including in-progress releases"""
   url = f"https://vsrm.dev.azure.com/{ORG}/{PROJECT}/_apis/release/definitions/{def_id}?forceDelete=true&api-version=7.1"
   r = requests.delete(url, headers=HEADERS)
   return r.status_code == 204

# ================= BUILD/CI/VALIDATION =================
def get_build_definition_id(name):
   url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/definitions?api-version={API_VERSION}"
   r = requests.get(url, headers=HEADERS)
   r.raise_for_status()
   for d in r.json().get("value", []):
       if d["name"] == name:
           return d["id"]
   return None

def get_builds(def_id):
   url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/builds?definitions={def_id}&api-version={API_VERSION}"
   r = requests.get(url, headers=HEADERS)
   if not r.ok:
       return []
   return r.json().get("value", [])

def remove_all_retention_leases(def_id, max_retries=MAX_LEASE_RETRIES):
   """Remove all retention leases for all builds in a pipeline"""
   for attempt in range(max_retries):
       builds = get_builds(def_id)
       leases_found = False
       for b in builds:
           build_id = b["id"]
           leases_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/retention/leases?buildId={build_id}&api-version={API_VERSION}"
           r = requests.get(leases_url, headers=HEADERS)
           if r.ok:
               for lease in r.json().get("value", []):
                   leases_found = True
                   lease_id = lease["leaseId"]
                   delete_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/retention/leases/{lease_id}?api-version={API_VERSION}"
                   requests.delete(delete_url, headers=HEADERS)
                   time.sleep(0.1)
       if not leases_found:
           break
       time.sleep(0.5)
   return not leases_found

def delete_old_builds(def_id, older_than_days=DELETE_OLD_BUILDS_DAYS):
   """Delete old builds to unblock pipeline deletion"""
   cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
   builds = get_builds(def_id)
   for b in builds:
       finish_time_str = b.get("finishTime")
       if finish_time_str:
           try:
               finish_time = datetime.strptime(finish_time_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
           except Exception:
               finish_time = datetime.strptime(finish_time_str.split(".")[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
           if finish_time < cutoff_date:
               build_id = b["id"]
               delete_build_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/builds/{build_id}?api-version={API_VERSION}"
               requests.delete(delete_build_url, headers=HEADERS)
               time.sleep(0.1)

def delete_build_definition(def_id):
   """
   Delete a CI/Validation pipeline including:
   1. All builds
   2. All retention leases (by leaseId)
   3. Clears retainedByRelease flag
   4. Deletes the pipeline definition
   """
   try:
       # Get all builds for this definition
       builds = get_builds(def_id)
       for b in builds:
           build_id = b["id"]

           # --- Step 1: Delete all retention leases by leaseId ---
           leases_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/retention/leases?buildId={build_id}&api-version={API_VERSION}"
           r = requests.get(leases_url, headers=HEADERS)
           if r.ok:
               lease_ids = [str(lease["leaseId"]) for lease in r.json().get("value", [])]
               if lease_ids:
                   delete_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/retention/leases?ids={','.join(lease_ids)}&api-version={API_VERSION}"
                   requests.delete(delete_url, headers=HEADERS)
                   time.sleep(0.1)

           # --- Step 2: Clear retainedByRelease flag ---
           patch_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/builds/{build_id}?api-version={API_VERSION}"
           requests.patch(patch_url, headers=HEADERS, json={"retainedByRelease": False})
           time.sleep(0.1)

           # --- Step 3: Delete the build itself ---
           delete_build_url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/builds/{build_id}?api-version={API_VERSION}"
           requests.delete(delete_build_url, headers=HEADERS)
           time.sleep(0.1)

       # --- Step 4: Delete the pipeline definition ---
       url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/definitions/{def_id}?api-version={API_VERSION}"
       r = requests.delete(url, headers=HEADERS)
       return r.status_code == 204

   except Exception as e:
       print(f"❌ Failed to delete CI/Validation: {e}")
       return False

# ================= GET ALL EXISTING PIPELINES =================
def get_all_release_definitions():
   url = f"https://vsrm.dev.azure.com/{ORG}/{PROJECT}/_apis/release/definitions?api-version={API_VERSION}"
   r = requests.get(url, headers=HEADERS)
   r.raise_for_status()
   return {d["name"]: d["id"] for d in r.json().get("value", [])}

def get_all_build_definitions():
   url = f"https://dev.azure.com/{ORG}/{PROJECT}/_apis/build/definitions?api-version={API_VERSION}"
   r = requests.get(url, headers=HEADERS)
   r.raise_for_status()
   return {d["name"]: d["id"] for d in r.json().get("value", [])}

# ================= NON-STANDARD PIPELINE LISTING =================
def list_non_standard_pipelines(df_known):
   """List all non-standard pipelines into Excel before deletion"""
   known_pipelines = set(df_known["pipeline_name"].str.strip())
   records = []

   # Releases
   for name, def_id in get_all_release_definitions().items():
       if not any(name.startswith(k) for k in known_pipelines) and name.endswith("-CD"):
           records.append(["Release", name, def_id])

   # Builds/CI/Validation
   for name, def_id in get_all_build_definitions().items():
       if not any(name.startswith(k) for k in known_pipelines) and (name.endswith("-CI") or name.endswith("-build-validation-pipeline")):
           type_name = "CI" if name.endswith("-CI") else "Validation"
           records.append([type_name, name, def_id])

   df_out = pd.DataFrame(records, columns=["Type", "Pipeline Name", "Definition ID"])
   df_out.to_excel("non_standard_pipelines.xlsx", index=False)
   print(f"✅ Non-standard pipelines saved to non_standard_pipelines.xlsx")
   return df_out

# ================= MAIN =================
def main():
   df = pd.read_excel(EXCEL_FILE, dtype=str)
   known_pipelines = set(row["pipeline_name"].strip() for _, row in df.iterrows())

   # List non-standard pipelines first
   list_non_standard_pipelines(df)

   with open(LOG_FILE, "w", newline="", encoding="utf-8") as log:
       writer = csv.writer(log)
       writer.writerow(["Pipeline", "Release Status", "CI Status", "Validation Status"])

       # ---- Known pipelines ----
       for _, row in df.iterrows():
           pipeline_name = row["pipeline_name"].strip()
           release_name = f"{pipeline_name}-CD"
           ci_name = f"{pipeline_name}-CI"
           validation_name = f"{pipeline_name}-build-validation-pipeline"

           print(f"\n🔎 Processing: {pipeline_name}")

           # Release/CD
           rid = get_release_definition_id(release_name)
           if rid:
               ok = delete_release_definition_force(rid)
               release_status = "True" if ok else "False"
           else:
               release_status = "Deleted"
           print(f"Release status: {release_status}")

           # CI
           bid_ci = get_build_definition_id(ci_name)
           if bid_ci:
               ok_ci = delete_build_definition(bid_ci)
               ci_status = "True" if ok_ci else "False"
           else:
               ci_status = "Deleted"
           print(f"CI status: {ci_status}")

           # Validation
           if DELETE_VALIDATION:
               bid_val = get_build_definition_id(validation_name)
               if bid_val:
                   ok_val = delete_build_definition(bid_val)
                   val_status = "True" if ok_val else "False"
               else:
                   val_status = "Deleted"
           else:
               val_status = "N/A"
           print(f"Validation status: {val_status}")

           writer.writerow([pipeline_name, release_status, ci_status, val_status])
           time.sleep(DELAY)

       # ---- Non-standard pipelines deletion (optional) ----
       all_rels = get_all_release_definitions()
       all_builds = get_all_build_definitions()

       for name, def_id in all_rels.items():
           if not any(name.startswith(k) for k in known_pipelines) and name.endswith("CD"):
               print(f"\n⚠️ Deleting Non-standard Release: {name}")
               ok = delete_release_definition_force(def_id)
               status = "True" if ok else "False"
               writer.writerow([name, status, "", ""])
               time.sleep(DELAY)

       for name, def_id in all_builds.items():
           if not any(name.startswith(k) for k in known_pipelines) and (name.endswith("CI") or name.endswith("build-validation-pipeline")):
               print(f"\n⚠️ Deleting Non-standard Build: {name}")
               ok = delete_build_definition(def_id)
               ci_status = "True" if ok and name.endswith("CI") else ""
               val_status = "True" if ok and name.endswith("build-validation-pipeline") else ""
               if ci_status == "" and name.endswith("CI"):
                   ci_status = "Deleted"
               if val_status == "" and name.endswith("build-validation-pipeline"):
                   val_status = "Deleted"
               writer.writerow([name, "", ci_status, val_status])
               time.sleep(DELAY)

   # ---- Summary ----
   result_df = pd.read_csv(LOG_FILE)
   total_true = (result_df == "True").sum().sum()
   total_false = (result_df == "False").sum().sum()
   total_deleted = (result_df == "Deleted").sum().sum()
   print(f"\n✅ Cleanup completed. Log saved to {LOG_FILE}")
   print(f"Summary: True={total_true}, False={total_false}, Deleted={total_deleted}")

if __name__ == "__main__":
   main()