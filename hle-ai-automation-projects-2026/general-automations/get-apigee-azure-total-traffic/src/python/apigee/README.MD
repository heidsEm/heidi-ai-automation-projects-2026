
# How to Run the Apigee X Monthly Traffic Extraction Script

This guide explains how to run the Python script that pulls **monthly sum(message_count)** per API Proxy from **Apigee X** and exports it to **Excel**.

---

## ✅ Prerequisites
- **Python** 3.8 or later
- Install required packages:
  ```bash
  pip install pandas requests openpyxl
  ```
- **gcloud CLI** is installed and authenticated to the correct GCP account/project
  ```bash
  gcloud auth login
  gcloud config set project <YOUR_PROJECT_ID>
  ```

---

## 🔐 Get an Access Token (GCP)
Run in **Cloud Shell** or any terminal with gcloud:
```bash
gcloud auth print-access-token
```
Copy the token and paste it into the script:
```python
ACCESS_TOKEN = "<paste-token-here>"
```
> Tip: Tokens expire (typically ~1 hour). If you see 401/403, generate a fresh token.

---

## 🧩 Configure the Script
Open the script and update the following:

### 1) Organization–Environment Map
```python
ORG_ENV_MAP = {
  "gto-eai-apigeex-dev-211f": "apigeex-env-dev",
  "gto-eai-apigeex-qa-stg-a858": "apigeex-env-qa",
  "gto-eai-apigeex-prod-prod-82e2": "apigeex-env-prod"
}
```
- Keys = **Apigee organization** (often same as the GCP project id)
- Values = **Apigee environment** names

### 2) Input CSV of API Proxies
Set the file name:
```python
CSV_FILE = "api_list.csv"
```
The CSV must contain a column of API proxy names. Supported header:
- `api_name` (preferred), or if missing, the **first column** will be used.

**Example `api_list.csv`:**
```csv
api_name
OrdersAPI
PaymentsAPI
InventoryAPI
```

### 3) Report Year & Output File
```python
YEAR = 2025
OUTPUT_FILE = "apgx_api_traffic.xlsx"
```

---

## ▶️ Run the Script
1. Save the script as `apigee_traffic_report.py`.
2. Place `api_list.csv` in the **same folder**.
3. Run:
```bash
python apigee_traffic_report.py
```

---

## 📦 What You Get
- An Excel workbook: `apgx_api_traffic.xlsx`
- One **sheet per environment** (e.g., `apigeex-env-dev`, `apigeex-env-qa`, `apigeex-env-prod`)
- Columns:
  - `API Name`
  - `<Month> Traffic` for **Jan–Dec** of `YEAR`
  - `Total Annual Traffic`
  - Final row: `GRAND TOTAL` (per-month and annual totals)

---

## 🧪 How It Works (Quick Overview)
- Builds month time windows via `get_time_range(year, month)` in the format `MM/DD/YYYY HH:MM~MM/DD/YYYY HH:MM` required by the **Stats API**.
- Calls:
  ```
  GET https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/stats/apiproxy
  params: select=sum(message_count), timeRange=..., limit=1000
  ```
- Maps returned metric values to your target API list and writes to Excel.

---

## 🛠️ Troubleshooting
- **401/403 Unauthorized**
  - Token expired → run `gcloud auth print-access-token` again.
  - Ensure your user/service account has **Apigee Viewer** (or higher) and the project has **Apigee X enabled**.
- **Empty/zero values**
  - Verify API proxy names in `api_list.csv` match **Apigee proxy names** exactly (case-sensitive).
  - Check that traffic exists for the given `YEAR` and environment.
- **HTTP errors printed in console**
  - The script prints the raw error body. Confirm org/env are correct and your account has access.
- **Excel file open/locked**
  - Close the Excel file before re-running. The writer uses `openpyxl`.

---

