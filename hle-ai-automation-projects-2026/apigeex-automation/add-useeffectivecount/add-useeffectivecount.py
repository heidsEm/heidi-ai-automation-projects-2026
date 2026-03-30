import gc
import os
import random
import shutil
import stat
import string
import time
import xml.etree.ElementTree as ET

import requests
from git import Repo

# ================= CONFIGURATION =================

REPOSITORIES = [
    "repo-name",
]

BASE_BRANCH = "develop"
COMMIT_MESSAGE = "feat(enahancement): add UseEffectiveCount to SpikeArrest policy"

TEMPLATE_FOLDER_NAME = "EAI-API-APIGEEX-APIPROXY-TEMPLATE"

BASE_TEMP_DIR = "C:\\temp"
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

GITHUB_TOKEN = "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"
HEADERS = {
   "Authorization": f"token {GITHUB_TOKEN}",
   "Accept": "application/vnd.github.v3+json"
}

# ================= CLEANUP HELPERS =================

def handle_remove_readonly(func, path, exc):
   os.chmod(path, stat.S_IWRITE)
   func(path)

def cleanup_temp_dir(path, retries=7, delay=2):
   for _ in range(retries):
       try:
           if os.path.exists(path):
               shutil.rmtree(path, onerror=handle_remove_readonly)
           return
       except PermissionError:
           gc.collect()
           time.sleep(delay)

# ================= BRANCH NAME =================

def generate_branch_name():
   suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
   return f"EAM-29-add-useeffectivecount-{suffix}"

# ================= XML HELPERS =================

def read_xml_declaration(file_path):
   """Preserve original XML declaration (including standalone=yes)."""
   with open(file_path, "r", encoding="utf-8") as f:
       first_line = f.readline().strip()
       if first_line.startswith("<?xml"):
           return first_line
   return '<?xml version="1.0" encoding="UTF-8"?>'

def write_pretty_xml(tree, root, file_path, xml_declaration):
   ET.indent(tree, space="  ")
   xml_body = ET.tostring(root, encoding="unicode")
   with open(file_path, "w", encoding="utf-8") as f:
       f.write(xml_declaration + "\n")
       f.write(xml_body)

def update_spike_arrest_policy(policy_path):
   xml_declaration = read_xml_declaration(policy_path)

   tree = ET.parse(policy_path)
   root = tree.getroot()

   if root.tag != "SpikeArrest":
       return False

   if root.find("UseEffectiveCount") is None:
       elem = ET.Element("UseEffectiveCount")
       elem.text = "true"
       root.append(elem)

       write_pretty_xml(tree, root, policy_path, xml_declaration)
       return True

   return False

# ================= DISCOVERY =================

def find_spike_arrest_policies(repo_root):
   policies = []

   for root, _, files in os.walk(repo_root):
       if TEMPLATE_FOLDER_NAME.lower() in root.lower():
           continue

       if os.path.basename(root) == "policies":
           for file in files:
               if file.endswith(".xml"):
                   full_path = os.path.join(root, file)
                   try:
                       if ET.parse(full_path).getroot().tag == "SpikeArrest":
                           policies.append(full_path)
                   except ET.ParseError:
                       pass

   return policies

# ================= MAIN LOGIC =================

def update_repo(full_repo_name):
   owner, repo_name = full_repo_name.split("/")
   clone_url = f"https://{GITHUB_TOKEN}@github.com/{owner}/{repo_name}.git"
   temp_dir = os.path.join(BASE_TEMP_DIR, f"temp_{repo_name}")
   branch_name = generate_branch_name()

   print(f"\n🔄 Processing {full_repo_name}")

   try:
       cleanup_temp_dir(temp_dir)
       repo = Repo.clone_from(clone_url, temp_dir)
       repo.git.checkout("-b", branch_name)

       policy_files = find_spike_arrest_policies(temp_dir)

       changed = False
       for policy_file in policy_files:
           if update_spike_arrest_policy(policy_file):
               changed = True
               print(f"✔ Updated: {policy_file}")

       if not changed:
           print("ℹ No changes required")
           return

       repo.git.add(all=True)
       repo.index.commit(COMMIT_MESSAGE)
       repo.remote(name="origin").push(branch_name)

       pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
       response = requests.post(
           pr_url,
           headers=HEADERS,
           json={"title": COMMIT_MESSAGE, "head": branch_name, "base": BASE_BRANCH}
       )

       if response.status_code == 201:
           print(f"🔗 PR created: {response.json()['html_url']}")
       else:
           print(f"⚠️ PR failed: {response.text}")

   finally:
       try:
           del repo
       except Exception:
           pass
       gc.collect()
       time.sleep(2)
       cleanup_temp_dir(temp_dir)

# ================= EXECUTION =================

for repo in REPOSITORIES:
   update_repo(repo)

print("\n✅ Done processing all repositories.")