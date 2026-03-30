import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from openpyxl import Workbook

# ========= CONFIGURATION =========
REPOSITORIES = [
"procter-gamble/EAI-APIM-Con-Consumer-DigitalCommerce-PampersClub-FavouriteButtonService-V1",
"procter-gamble/EAI-APIM-Con-Consumer-DigitalCommerce-PampersClub-IncentiveDistributionAPI-V1",
"procter-gamble/EAI-APIM-Con-Consumer-DigitalCommerce-PampersClub-PregnancyWeightGainAPI-V1",
"procter-gamble/EAI-APIM-Con-Consumer-DigitalCommerce-PampersClub-px-autopublish-nonprod-V1", 
   # Add more repos here...
]

MAX_WORKERS = 20  # Faster parallel processing
RETRY_LIMIT = 3   # Auto-retry for GitHub throttling

LEGACY_CLONE_PATTERN = re.compile(r"-DEV-|-NON-PROD-|-PROD-", re.IGNORECASE)

# ========= AUTH =========
GITHUB_TOKEN = ""  # Your PAT
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# ========= HELPERS =========

def request_with_retry(url):
   """Auto-retry GitHub API calls (403, 502, network errors)."""
   for attempt in range(RETRY_LIMIT):
       try:
           resp = requests.get(url, headers=HEADERS)
           if resp.status_code in (200, 404):
               return resp
           print(f"⚠️ Retry {attempt+1} for {url} (status {resp.status_code})")
           time.sleep(1 + attempt)
       except:
           print(f"⚠️ Network error retry {attempt+1}: {url}")
           time.sleep(1 + attempt)
   return None


def get_default_branch(owner, repo):
   url = f"https://api.github.com/repos/{owner}/{repo}"
   resp = request_with_retry(url)
   if not resp or resp.status_code != 200:
       return None
   return resp.json().get("default_branch", "main")


def get_repo_tree(owner, repo, branch):
   """Fetch full tree once (massive speed improvement)."""
   url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
   resp = request_with_retry(url)
   if not resp or resp.status_code != 200:
       print(f"❌ Cannot fetch tree for {repo}")
       return []
   return resp.json().get("tree", [])


def find_file(tree, filename):
   for item in tree:
       if item["type"] == "blob" and item["path"].endswith(filename):
           return item["path"]
   return None


def fetch_file(owner, repo, path, branch):
   url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
   resp = request_with_retry(url)
   return resp.text if (resp and resp.status_code == 200) else None


def check_main_tf(main_tf):
   lines = main_tf.splitlines()
   def any_uncommented(start, end):
       return any(
           i < len(lines) and not lines[i].strip().startswith("#")
           for i in range(start, end)
       )
   swagger = any_uncommented(25, 31) and not any_uncommented(41, 136)
   ops = not any_uncommented(25, 31) and any_uncommented(41, 136)
   return swagger, ops


def detect_v2(owner, repo, branch):
   tree = get_repo_tree(owner, repo, branch)

   parameters_path = find_file(tree, "parameters.json")
   main_tf_path = find_file(tree, "main.tf")

   if not parameters_path or not main_tf_path:
       return None

   parameters = fetch_file(owner, repo, parameters_path, branch)
   main_tf = fetch_file(owner, repo, main_tf_path, branch)

   if not parameters or not main_tf:
       return None

   # V2 Clone
   if "NonProdEnvClones" in parameters:
       return "V2 with Clone"

   swagger, operations = check_main_tf(main_tf)

   if "openapi-spec" in parameters and swagger:
       return "V2 with Swagger"

   if "operations" in parameters and operations:
       return "V2 with Operations"

   return "V2"


def classify(repo_fullname):
   owner, repo = repo_fullname.split("/")
   repo_name = repo

   # Legacy Clone detection
   if LEGACY_CLONE_PATTERN.search(repo_name):
       return repo_name, "Legacy API Clone"

   # Detect default branch
   branch = get_default_branch(owner, repo)
   if not branch:
       return repo_name, "Branch Detection Failed"

   # Detect V2 type
   v2 = detect_v2(owner, repo, branch)
   if v2:
       return repo_name, v2

   return repo_name, "Legacy API"


# ========= EXCEL GENERATOR =========

def save_to_excel(results, file="api_classification.xlsx"):
   wb = Workbook()
   ws = wb.active
   ws.title = "API Classification"
   ws.append(["Repository", "Classification"])

   for repo, cls in results.items():
       ws.append([repo, cls])

   wb.save(file)
   print(f"\n✅ Excel created: {file}")


# ========= MAIN =========

def main():
   results = {}

   print("\n🚀 Processing repositories in parallel…\n")

   with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
       futures = {executor.submit(classify, repo): repo for repo in REPOSITORIES}

       for future in as_completed(futures):
           repo_name, cls = future.result()
           results[repo_name] = cls
           print(f"{repo_name}: {cls}")

   save_to_excel(results)


if __name__ == "__main__":
   main()