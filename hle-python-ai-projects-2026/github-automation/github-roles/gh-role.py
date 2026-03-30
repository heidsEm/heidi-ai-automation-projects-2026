import csv
import gc
import os
import random
import shutil
import stat
import string
import time

import requests
from git import Repo
from tqdm import tqdm

# ================= CONFIG =================

GITHUB_TOKEN = "YOUR_TOKEN"
ORG_NAME = "org-name"

REPO_CSV_FILE = "repos.csv"

BASE_BRANCHES = ["develop", "qa", "main"]

TEAMS_WITH_WRITE = [
   "github-non-engineers",
   "github-devops",
   "github-non-operations",
   "github-engineers",
   "github-operations",
   "api-owners"
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_CODEOWNERS_FILE = os.path.join(SCRIPT_DIR, "CODEOWNERS.txt")

BASE_TEMP_DIR = os.path.join(SCRIPT_DIR, "temp")

CODEOWNERS_PATH = ".github/CODEOWNERS"

LOG_FILE = "repo_governance_log.csv"

HEADERS = {
   "Authorization": f"token {GITHUB_TOKEN}",
   "Accept": "application/vnd.github+json"
}

DELAY_SECONDS = 1

# ================= VALIDATE LOCAL FILE =================

if not os.path.isfile(LOCAL_CODEOWNERS_FILE):
   raise FileNotFoundError(f"❌ CODEOWNERS template not found: {LOCAL_CODEOWNERS_FILE}")

with open(LOCAL_CODEOWNERS_FILE, "r", encoding="utf-8") as f:
   CODEOWNERS_CONTENT = f.read().strip() + "\n"

# ================= HELPERS =================

def random_suffix(length=4):
   return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def cleanup_temp_dir(path, retries=5, delay=2):
   """
   Recursively remove a directory in Windows safely,
   clearing read-only files and retrying if necessary.
   """
   for attempt in range(retries):
       if not os.path.exists(path):
           return
       try:
           # Clear read-only flags recursively
           for root, dirs, files in os.walk(path, topdown=False):
               for name in files:
                   filepath = os.path.join(root, name)
                   try:
                       os.chmod(filepath, stat.S_IWRITE)
                   except Exception:
                       pass
               for name in dirs:
                   dirpath = os.path.join(root, name)
                   try:
                       os.chmod(dirpath, stat.S_IWRITE)
                   except Exception:
                       pass
           # Remove directory
           shutil.rmtree(path)
           return
       except Exception:
           gc.collect()
           time.sleep(delay)
   print(f"⚠️ Failed to remove temp directory after {retries} attempts: {path}")

def set_default_branch(repo_name):
   url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}"
   payload = {"default_branch": "develop"}
   r = requests.patch(url, headers=HEADERS, json=payload)
   return r.status_code == 200

def enable_auto_delete(repo_name):
   url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}"
   payload = {"delete_branch_on_merge": True}
   r = requests.patch(url, headers=HEADERS, json=payload)
   return r.status_code == 200

def grant_team_access(repo_name, team_slug):
   url = f"https://api.github.com/orgs/{ORG_NAME}/teams/{team_slug}/repos/{ORG_NAME}/{repo_name}"
   payload = {"permission": "push"}
   r = requests.put(url, headers=HEADERS, json=payload)
   return r.status_code in (201, 204)

# ================= READ CSV =================

repositories = []
with open(REPO_CSV_FILE, newline="", encoding="utf-8") as f:
   reader = csv.DictReader(f)
   for row in reader:
       repositories.append(row["repository_name"].strip())

# ================= PROCESS =================

with open(LOG_FILE, "w", newline="", encoding="utf-8") as log_file:
   writer = csv.writer(log_file)
   writer.writerow(["Repository", "Status", "Message"])

   for repo_name in tqdm(repositories, desc="Processing Repositories"):

       temp_dir = os.path.join(BASE_TEMP_DIR, f"temp_{repo_name}")

       try:
           # --------------------------
           # Repo Settings
           # --------------------------
           set_default_branch(repo_name)
           enable_auto_delete(repo_name)

           for team in TEAMS_WITH_WRITE:
               grant_team_access(repo_name, team)

           # --------------------------
           # Clone Repo
           # --------------------------
           cleanup_temp_dir(temp_dir)
           clone_url = f"https://{GITHUB_TOKEN}@github.com/{ORG_NAME}/{repo_name}.git"
           repo = Repo.clone_from(clone_url, temp_dir)

           # --------------------------
           # Process Branches
           # --------------------------
           for base_branch in BASE_BRANCHES:

               suffix = random_suffix()
               branch_name = f"hle/update-codeowners-and-repo-role-settings-{suffix}"
               pr_title = f"feat:update-codeowners-and-repo-role-settings-{base_branch}-{suffix}"

               repo.git.checkout(base_branch)
               repo.git.checkout('-b', branch_name)

               codeowners_file = os.path.join(temp_dir, CODEOWNERS_PATH)
               os.makedirs(os.path.dirname(codeowners_file), exist_ok=True)

               with open(codeowners_file, "w", encoding="utf-8") as f:
                   f.write(CODEOWNERS_CONTENT)

               repo.git.add(CODEOWNERS_PATH)
               repo.index.commit("feat: update CODEOWNERS governance")
               repo.remote().push(branch_name)

               # --------------------------
               # Create Pull Request
               # --------------------------
               pr_url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/pulls"
               payload = {
                   "title": pr_title,
                   "head": branch_name,
                   "base": base_branch
               }
               response = requests.post(pr_url, headers=HEADERS, json=payload)

               if response.status_code == 201:
                   pr_link = response.json()["html_url"]
                   message = f"PR Created: {pr_link}"
               else:
                   message = f"PR Failed: {response.text}"

               writer.writerow([repo_name, "SUCCESS", message])

           time.sleep(DELAY_SECONDS)

       except Exception as e:
           writer.writerow([repo_name, "ERROR", str(e)])

       finally:
           try:
               del repo
           except:
               pass
           gc.collect()
           cleanup_temp_dir(temp_dir)

print(f"\n✅ Completed. Log saved to {LOG_FILE}")