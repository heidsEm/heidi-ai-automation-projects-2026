import gc
import os
import random
import shutil
import stat
import string
import time

import requests
from git import Repo

# === CONFIGURATION ===

REPOSITORIES = [
""
    # Add more repositories here
]


WORKFLOW_FILE = "generate-change-docs.yaml"  # Local file that you have in the same folder
WORKFLOW_FILENAME = "generate-change-docs.yaml"  # The name to use in the repo
COMMIT_MESSAGE = f"feat(workflows):Add {WORKFLOW_FILENAME}"
BASE_BRANCH = "dev"  # Or 'master' depending on your repo

# === TEMP DIRECTORY OUTSIDE ONEDRIVE ===
BASE_TEMP_DIR = "C:\\temp"
if not os.path.exists(BASE_TEMP_DIR):
    os.makedirs(BASE_TEMP_DIR)

# === AUTHENTICATION ===

GITHUB_TOKEN = "token"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# === SAFETY CHECK ===

if not os.path.isfile(WORKFLOW_FILE):
    print(f"❌ Workflow file '{WORKFLOW_FILE}' not found at path: {os.path.abspath(WORKFLOW_FILE)}")
    exit(1)

with open(WORKFLOW_FILE, 'r') as f:
    WORKFLOW_CONTENT = f.read()

# === CLEANUP HELPERS ===

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
    print(f"❌ Failed to remove temp directory after {retries} attempts: {path}")

# === BRANCH NAME GENERATOR ===

def generate_branch_name():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"EAAMP-82-feature-add-generate-docs-yaml-{suffix}"

# === MAIN FUNCTION ===

def update_repo(full_repo_name):
    owner, repo_name = full_repo_name.split('/')
    clone_url = f"https://{GITHUB_TOKEN}@github.com/{owner}/{repo_name}.git"
    temp_dir = os.path.join(BASE_TEMP_DIR, f"temp_{repo_name}")
    workflow_dir = os.path.join(temp_dir, ".github", "workflows")
    workflow_path = os.path.join(workflow_dir, WORKFLOW_FILENAME)

    branch_name = generate_branch_name()
    print(f"\n🔄 Processing {full_repo_name} with branch '{branch_name}'...")

    try:
        if os.path.exists(temp_dir):
            cleanup_temp_dir(temp_dir)

        repo = Repo.clone_from(clone_url, temp_dir)
        repo.git.checkout('-b', branch_name)

        os.makedirs(workflow_dir, exist_ok=True)

        with open(workflow_path, 'w') as wf:
            wf.write(WORKFLOW_CONTENT.strip())

        repo.git.add(all=True)
        repo.index.commit(COMMIT_MESSAGE)
        origin = repo.remote(name='origin')
        origin.push(branch_name)
        print(f"✅ Branch '{branch_name}' pushed to {full_repo_name}")

        pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
        pr_payload = {
            "title": COMMIT_MESSAGE,
            "head": branch_name,
            "base": BASE_BRANCH
        }

        response = requests.post(pr_url, headers=HEADERS, json=pr_payload)
        if response.status_code == 201:
            pr_link = response.json().get("html_url", "")
            print(f"🔗 Pull request created: {pr_link}")
        else:
            print(f"⚠️ Failed to create PR: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Error processing {full_repo_name}: {e}")

    finally:
        try:
            del repo
        except Exception:
            pass
        gc.collect()
        time.sleep(2)
        cleanup_temp_dir(temp_dir)

# === MAIN LOOP ===

for repo in REPOSITORIES:
    update_repo(repo)

print("\n✅ Done processing all repositories.")