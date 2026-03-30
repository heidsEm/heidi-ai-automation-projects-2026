## Acknowledgement

Parts of this documentation were generated with the assistance of AI tools (Microsoft Copilot and ChatGPT) and reviewed for accuracy before use.

***

# Apigee Edge Backup and Restore Toolkit

This repository provides Python scripts to back up and restore **Apigee Edge APIs** and **platform artifacts**.

It is designed for:

*   Disaster recovery (DR)
*   Environment migration
*   Operational backups

The toolkit separates **API proxy data** from **infrastructure artifacts** to keep backups organized and safe.

***

## Scripts Included

| Script                | Purpose                                                                                     |
| --------------------- | ------------------------------------------------------------------------------------------- |
| `api_backup.py`       | Back up API proxies, API products, and related KVM values                                   |
| `api_restore.py`      | Restore API proxies, deploy them, restore API products and KVM values                       |
| `artifact_backup.py`  | Back up platform artifacts such as target servers, keystores, certificates, and truststores |
| `artifact_restore.py` | Restore platform artifacts such as target servers and certificates                          |

***

## Requirements

*   Python **3.8** or newer
*   Install dependencies:

```bash
pip install requests urllib3
```

***

## Configuration

Each script contains configuration variables that must be updated before running.

### Example Configuration

```python
ORG = "pg-prod"
ENV = "prod"
TOKEN = "YOUR_OAUTH_TOKEN"
```

### Configuration Variables

| Variable | Description                                             |
| -------- | ------------------------------------------------------- |
| `ORG`    | Apigee organization                                     |
| `ENV`    | Environment (`prod`, `test`, `dev`, etc.)               |
| `TOKEN`  | OAuth Bearer token used to access Apigee Management API |

***

## CSV Input File

`api_backup.py` requires a CSV file named:

    apis.csv

### Example

```csv
API Name
Consumer_Profile_V1
Consumer_MIG_V1
SupplyChain_OrderManagement_V1
```

*   The first row is treated as a header and is skipped automatically.

***

## Backup Process

### 1. Backup API Proxies

Run:

```bash
python api_backup.py
```

This will:

*   Download the latest revision of each proxy
*   Export API Product configuration
*   Export KVM values related to the API

#### Output Folder

    Apigee_Backup/

#### Example Structure

    Apigee_Backup/
    ├── Consumer_Profile_V1
    │   ├── bundle
    │   │   └── Consumer_Profile_V1_rev3.zip
    │   ├── api_product
    │   │   └── Consumer_Profile_product.json
    │   └── kvm
    │       └── Consumer_Profile_kvm_values.json

***

### 2. Backup Platform Artifacts

Run:

```bash
python artifact_backup.py
```

This backs up important infrastructure artifacts:

*   Target Servers
*   Keystores
*   Certificates
*   Truststores
*   Virtual Hosts

#### Output Folder

    Apigee_Artifacts_Backup/

#### Example Structure

    Apigee_Artifacts_Backup/
    ├── target_servers
    │   ├── target1.json
    │   └── target2.json
    │
    ├── keystores
    │   └── gateway_keystore
    │       ├── cert1.pem
    │       └── cert2.pem
    │
    └── truststores
    │    └── mtls_store
    │        └── rootCA.pem
    │
    └── virtual_hosts    

***

## Restore Process

> **Note:** Restoring should normally be done in the order below.

### 1. Restore Platform Artifacts

Run:

```bash
python artifact_restore.py
```

This restores:

*   Target servers
*   Keystores
*   Certificates
*   Truststores

These components are often required before deploying APIs.

***

### 2. Restore APIs

Run:

```bash
python api_restore.py
```

This will:

*   Import API proxy bundles
*   Deploy the proxies to the environment
*   Recreate API Products
*   Restore KVM entries

***

## Recommended Disaster Recovery Workflow

Typical production DR workflow:

```bash
# Backup APIs
python api_backup.py

# Backup artifacts
python artifact_backup.py

# Store backups securely (Git / artifact repository / secure storage)

# Restore infrastructure artifacts first
python artifact_restore.py

# Restore API proxies
python api_restore.py
```

***

## Safety Recommendations

Before running restore scripts:

*   Verify the correct Apigee organization and environment
*   Ensure the OAuth token has **admin permissions**
*   Check whether resources already exist
*   Always test restores in **non‑production environments first**

***

## Typical Use Cases

This toolkit can be used for:

*   Disaster recovery
*   Environment cloning
*   Platform migration
*   Backup automation
*   Operational platform management

***

## Project Structure

    apigee-backup-toolkit/
    │
    ├── api_backup.py
    ├── api_restore.py
    │
    ├── artifact_backup.py
    ├── artifact_restore.py
    │
    ├── apis.csv
    └── README.md

***

## Notes

*   These scripts interact with the **Apigee Edge Management API**
*   Large environments with many proxies may take several minutes to back up
*   Parallel processing is used to speed up proxy backups

***
