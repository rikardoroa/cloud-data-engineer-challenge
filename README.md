# 🌩️ Cloud Data Engineer Challenge

## 🧭 Overview

This project builds an **AWS-based data ingestion and processing architecture** using **S3 → Lambda → RDS (PostgreSQL + PostGIS) → API Gateway**.  
All infrastructure is defined and deployed using **Terraform**, featuring **KMS encryption**, **CloudWatch monitoring**, **automatic RDS backups**, and **on-demand view creation** via Lambda.

---

## ⚙️ Architecture

### 🔹 Key Components

- **Amazon S3**  
  Receives CSV data files and triggers the **Lambda** on `ObjectCreated:Put`.

- **AWS Lambda**  
  Core processing unit performing:
  - **Data ingestion**: Reads S3 files and validates schemas.  
  - **Transformation**: Converts latitude/longitude into geospatial `geometry(Point)` using `ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)`.  
  - **Database loading**: Inserts rows into PostgreSQL `crime_incidents`.  
  - **Backup automation**: Invokes `boto3.rds.create_db_snapshot` to create **RDS snapshots** after data insertion.  
  - **View creation**: Ensures existence of **`v_crime_summary`**, an analytical view for aggregated crime reporting.

- **Amazon RDS (PostgreSQL + PostGIS)**  
  Runs in a private subnet with **PostGIS extensions** (`CREATE EXTENSION postgis;`).  
  Secrets (hostname, username, password) are securely retrieved from **AWS Secrets Manager**.

- **Amazon API Gateway**  
  REST interface exposing `/postgresql-api-conn-path`, allowing real-time querying of both `crime_incidents` and `v_crime_summary`.

- **Networking (VPC)**  
  Private subnet for Lambda with NAT Gateway for internet access and proper **Security Groups** to reach RDS.

- **CloudWatch & SNS**  
  Logs all Lambda runs, monitors failures, and sends alerts through SNS.

---

## 🧱 Repository Structure

```
aws_resources/
├── bucket_module/           # S3 bucket + KMS encryption
├── lambda_module/           # Lambda, IAM, Docker build, and alerts
│   ├── iam.tf
│   ├── lambda.tf
│   └── resources/python/aws_lambda/
│       ├── lambda_function.py
│       ├── get_connection.py      # Includes RDS snapshot logic
│       ├── get_transformation.py  # Inserts data and creates view v_crime_summary
│       ├── get_response.py
│       ├── get.py
│       └── utils.py
├── api_gateway_module/      # REST API Gateway (AWS_PROXY)
├── network_module/          # VPC, subnets, NAT, SG
├── rds_module/              # PostgreSQL RDS + Secrets Manager
├── providers.tf             # AWS provider definition
├── backend.hcl              # Remote backend (S3 + DynamoDB)
└── .pre-commit-config.yaml  # Pre-commit validation
```

---

## 📡 Data Flow

### 1️⃣ Ingestion from S3

When a CSV is uploaded, S3 triggers the Lambda (`ObjectCreated:Put` event).  
Lambda:
- Reads file from S3.  
- Validates schema using Pandas.  
- Converts coordinates to PostGIS geometry.  
- Inserts into `crime_incidents`.  
- Creates or replaces the summary view.

Example SQL (executed by Lambda):
```sql
CREATE OR REPLACE VIEW v_crime_summary AS
SELECT
    offense,
    district,
    COUNT(*) AS total,
    ST_Collect(geom) AS geom_cluster
FROM crime_incidents
WHERE geom IS NOT NULL
GROUP BY offense, district;
```

---

### 2️⃣ API Gateway Query

**Request:**
```
GET /https://09hlcr7v6d.execute-api.us-east-2.amazonaws.com/dev/postgresql-api-conn-path?table=crime_incidents
```

**Real Response Example:**
```json
[
  {
    "id": 384,
    "ccn": "25141990",
    "report_date": 1758066539000,
    "shift": "EVENING",
    "method": "OTHERS",
    "offense": "ROBBERY",
    "block": "1300 - 1399 BLOCK OF 2ND STREET NE",
    "ward": "6.0",
    "district": "5.0",
    "psa": "501.0",
    "neighborhood_cluster": "Cluster 25",
    "latitude": 38.9078254892,
    "longitude": -77.0035141787,
    "geom": "0101000020E6100000AFA58893394053C06B4B29A033744340"
  }
]
```

**Querying the view:**
```
GET /https://09hlcr7v6d.execute-api.us-east-2.amazonaws.com/dev/postgresql-api-conn-path?table=crime_summary
```
**Real Response Example:**
```json
[
  {
    "offense": "ASSAULT W/DANGEROUS WEAPON",
    "district": "3.0",
    "total": 2,
    "geom_cluster": "0104000020E610000002000000010100000057AD2053944053C053F46BA32D74434001010000004FDE4198AD4053C0584EB940ED754340"
  }
]
```

## 🧾 Example Lambda Event Payload (S3 Trigger)

```json
{
  "Records": [
    {
      "eventVersion": "2.1",
      "eventSource": "aws:s3",
      "awsRegion": "us-east-2",
      "eventTime": "2025-10-03T16:09:50.130Z",
      "eventName": "ObjectCreated:Put",
      "userIdentity": {"principalId": "ACF3QWLPS3VUX"},
      "requestParameters": {"sourceIPAddress": "191.95.19.221"},
      "responseElements": {
        "x-amz-request-id": "RGCMFQ73Z5425D4Y",
        "x-amz-id-2": "dV1TSmaGWQzgc4ezL1QaIx00s13H9VFUFHXTcplY1O8VqFaSw7Aj/FfYe3E+N6AoYGiMEW1J1ywKo/42G1DaJTCIh5mMnEIZGJ6pd+7SHu4="
      },
      "s3": {
        "s3SchemaVersion": "1.0",
        "configurationId": "tf-s3-lambda-20251003152624031900000001",
        "bucket": {
          "name": "mv-pr-dt",
          "arn": "arn:aws:s3:::mv-pr-dt"
        },
        "object": {
          "key": "Crime_Incidents_part_1.csv",
          "size": 1571,
          "eTag": "55f777571307999c7d0fee2abe75b5fc",
          "sequencer": "0068DFF54E183036C3"
        }
      }
    }
  ]
}
```

---

## 🚀 Deployment & Automation

### 🧩 Terraform Commands

```bash
terraform init -backend-config=backend.hcl
terraform fmt -recursive
terraform validate
terraform plan
terraform apply -auto-approve
terraform destroy -auto-approve
```

---

### 🤖 GitHub Actions CI/CD

Located in `.github/workflows/`:

#### `AWS_CREATION_PIPELINE.yml`
- Runs on push to `nanlabs_challenge`.
- Executes Terraform validation and deployment.

#### `AWS_DESTROY_PIPELINES.yml`
- Manual cleanup workflow for teardown.

#### Pre-commit Hooks
Validate locally before committing:
```bash
pre-commit run --all-files
```
Includes:
- `terraform_fmt`
- `terraform_validate`
- `terraform_tflint`
- `terraform_docs`

---

## 🔐 Security & Monitoring

| Component | Description |
|------------|--------------|
| **KMS** | Encrypts all S3 bucket objects |
| **Secrets Manager** | Stores DB credentials securely |
| **CloudWatch Logs** | Tracks Lambda execution logs |
| **SNS Notifications** | Sends alerts for failures |
| **CloudWatch Alarms** | Monitors Lambda error metrics |

---

## 🧠 Best Practices Implemented

- Modular Terraform architecture  
- Automated **RDS backup** on ingestion  
- Idempotent **view creation** for analytics  
- Pre-commit & CI/CD enforcement  
- Full observability with CloudWatch and SNS  

---

## 🛠️ Troubleshooting

| Issue | Possible Cause | Fix |
|--------|----------------|-----|
| Lambda not triggered | S3 event config issue | Check `aws_s3_bucket_notification` |
| DB connection error | Invalid Secrets Manager entry | Validate `postgresql_conn` |
| Snapshot not found | Missing IAM permission | Verify `RDSBackupAccess` policy |
| View missing | Lambda timeout or DB lock | Check CloudWatch logs |

---

## ✅ Current Status

| Module | Status | Description |
|---------|---------|-------------|
| **RDS** | ✅ | PostgreSQL + PostGIS operational |
| **Lambda** | ✅ | Ingestion, backup & view creation |
| **S3 Trigger** | ✅ | PUT event connected |
| **API Gateway** | ✅ | Query interface live |
| **CI/CD** | ✅ | Automated workflows |
| **Monitoring** | ✅ | CloudWatch & SNS active |
