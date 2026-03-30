## Steps to Generate Azure Access Token (OAuth 2.0)

### 1. Register an Application & Get Credentials
1. In the Azure Portal, go to:
   **Microsoft Entra ID → App registrations → New registration**
2. After creating the app, take note of:
   - **Application (client) ID**
   - **Directory (tenant) ID**

!!! note 
    If registering an Application is restricted, kindly reach out to P&G Platform Managers to obtain the Applications needed
    Consumer - AZ-APIM-NA-GLB-CS-Prod-01
    Enterprise/Internal - AZ-SVN-GLB-EAI-Enterprise-Build-01
    External - Azure-DevOps-PG-GLB-EAI-01-2021

---

### 2. Create a Client Secret
1. Open your registered app.
2. Navigate to:
   **Certificates & secrets → Client secrets → New client secret**
3. Copy the generated **client secret value** (you won’t see it again).

!!! note 
    If creation of client secret is restricted, kindly reach out to P&G Platform Managers to obtain the client secret value

---

### 3. Request an Access Token (POST Request)
You can use **Postman**, **curl**, or any HTTP client.

**Token Endpoint:**
```

<https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token>

```

!!! note 
    For Azure API Management the tenant_id is `3596192b-fdf5-4e2c-a6fa-acb706c963d8`


#### Request Body (as `x-www-form-urlencoded`):
```

grant_type=client_credentials
client_id={client_id_value}
client_secret={client_secret_value}
scope=https://management.core.windows.net/

```

!!! note
   Replace the scope with your API’s required scope if needed.

---

### 4. Use the Access Token <access_token>
The API response will contain:
- **access_token**
- **expires_in**
- **token_type**

Use the token in API calls as:

```

Authorization: Bearer {access-token-value}

```


# How to Run the APIM Traffic Extraction Python Script

This guide explains how to run the Python script that extracts monthly API traffic data from Azure API Management (APIM) and exports it into an Excel file.

---

## 📌 Prerequisites
Before running the script, ensure you have the following installed:

### **1. Python 3.8 or later**
Check your version:
```bash
python --version
```

### **2. Required Python Packages**
Install dependencies using:
```bash
pip install pandas requests tqdm openpyxl
```

### **3. Azure Access Token**
You must generate an Azure AD access token with permission to query APIM analytics.

---

## 📌 Script Configuration
Before running the script, update the following sections.

### **1. OUTPUT_FILE**
This is where the Excel report will be saved.
```python
OUTPUT_FILE = "apim_api_traffic.xlsx"
```
!!! note 
    Rename accordingly based on the Azure instances e.g Consumer `apim_api_traffic-con.xlsx`

### **2. ENVIRONMENTS**
Update subscription ID, resource group, and APIM service name:
```python
ENVIRONMENTS = {
    "AZ-ENT-NONPROD": [
        {
            "subscription_id": "<your-subscription-id>",
            "resource_group": "<your-resource-group>",
            "service_name": "<your-apim-service-name>"
        }
    ],
    "AZ-ENT-PROD": [ ... ]
}
```

   ![az-instance](/azr-total-traffic/assets/img/az-instance-sample.png)

### **3. Date Range**
Set the years you want to extract:
```python
START_YEAR = 2025
END_YEAR = 2026
```

---

## 📌 How to Run the Script
1. Save the Python script as `apim_traffic_report.py`.
2. Open a terminal in the folder containing the script.
3. Run:
```bash
python apim_traffic_report.py
```

---

## 📌 Output
After execution, the script will generate an Excel file: 
```
apim_api_traffic-ent.xlsx
```
The file contains:
- One sheet per environment (e.g., NONPROD, PROD)
- Monthly traffic per API
- A “Total Traffic” column

---

!!! note 
    - If APIM has no analytics data for a given month, the script will show a warning.
    - Make sure your access token is not expired.

