# 🌩️ Cloud Data Engineer Challenge

## 🧭 Overview

This project builds an **AWS-based data ingestion and processing architecture** using **S3 → Lambda → RDS (PostgreSQL + PostGIS) → API Gateway**.  
All infrastructure is defined and deployed using **Terraform**, featuring **KMS encryption**, **CloudWatch monitoring**, **automatic RDS backups**, and **on-demand view creation** via Lambda.

---

## ⚠️ Critical Configuration Notes

The **bucket configuration** is a critical part of this project. Two different S3 buckets are required:

1. **Terraform State Bucket** – used to store the Terraform state file (`terraform.tfstate`).  
2. **Data Upload Bucket** – used to upload files that trigger the Lambda function.

### 🪣 Terraform State Bucket
- This bucket is configured in the `backend.hcl` file.  
- If you want to **change the bucket name**:
  - First, **validate that the bucket does not already exist** in your AWS account.  
  - Then, **create the new bucket** following the same steps described in the [Prerequisites](#-prerequisites) section.  
  - Finally, update the `bucket` value in the `backend.hcl` file to match the new name.

### 📂 Data Upload Bucket
- This bucket is where files are uploaded to trigger the Lambda function.  
- If you want to **change the variable name or bucket value**, update it in:
  ```
  bucket_module → variables.tf → default value
  ```
- Before changing it, **make sure that the bucket exists**, as explained in the prerequisites section.  
- Terraform uses this variable to connect the S3 event notification with the Lambda function, so the name must match an existing bucket.

Incorrect configuration of either bucket will prevent Terraform from deploying or the Lambda from being triggered correctly.

---

## 🧰 Prerequisites

### 1️⃣ AWS CLI Installation

The **AWS CLI** is essential for managing credentials and configuring your environment. Follow these steps for installation:

**macOS Installation:**
```bash
brew install awscli
```

**Verify Installation:**
```bash
aws --version
```

**Windows Installation:**  
For Windows users, refer to the official [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

---

### 2️⃣ Terraform Environment Configuration

**Check if the S3 Bucket Exists:**
```bash
aws s3api head-bucket --bucket your_bucket
```

**Create DynamoDB Table for Terraform State Locking:**
```bash
aws dynamodb create-table --table-name terraform-lock-table   --attribute-definitions AttributeName=LockID,AttributeType=S   --key-schema AttributeName=LockID,KeyType=HASH   --billing-mode PAY_PER_REQUEST --region your_region
```

**Create S3 Bucket for Terraform State:**
```bash
aws s3api create-bucket --bucket your_bucket --region your_region   --create-bucket-configuration LocationConstraint=your_region
```

**Apply Bucket Policies:**
```bash
aws s3api put-public-access-block --bucket your_bucket   --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

---

### 3️⃣ Backend Configuration for Terraform State

Update the `backend.hcl` file with your Terraform backend configuration:
```hcl
bucket = "your-bucket"
```
---

## 📦 Triggering the Lambda Function via S3

Once the Terraform infrastructure is deployed, you can **trigger the Lambda function automatically** by uploading files to the configured **S3 bucket**.

Each time a new object is uploaded, the **S3 event notification** will invoke the Lambda to process the data and store it in the PostgreSQL database.

### 📁 Use the `sample_files` Folder

This repository includes a directory named **`sample_files/`**, which contains example files to test the Lambda integration.

#### 🧪 Steps to Trigger the Lambda

1. Identify your S3 bucket name from Terraform outputs or the AWS Console.  
2. Upload a sample file from the `sample_files` directory:
   ```bash
   aws s3 cp sample_files/example_data.csv s3://your_bucket_name/
   ```
3. The **S3 ObjectCreated:Put** event will automatically **invoke the Lambda**.  
4. The Lambda function reads and processes the file, then loads the resulting data into **RDS (PostgreSQL)**.  
5. Check Lambda execution logs in:
   ```
   Amazon CloudWatch → Log groups → /aws/lambda/your_lambda_name
   ```
6. Also the lambda can be triggered loading the files manually using AWS Console directly

#### 📝 Notes

- Only `.csv` files should be uploaded.  
- The schema (columns, types) must match what your Lambda expects.  


---


### ⚙️ 4️⃣ Required Environment Variables

Before running Terraform or executing GitHub Actions pipelines, make sure the following **environment variables** are configured.  
If they are missing, the **pipeline will fail** during deployment or Lambda provisioning.

| Variable | Description |
|-----------|--------------|
| `DB_NAME` | Variable used in the AWS Lambda for PosgreSQL database creation  |
| `DB_PASSWORD` | Password used in RDS module for default database access |
| `AWS_ACCESS_KEY_ID` | AWS access key ID for authentication |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key associated with the account |

**These variables must be configured under the repository’s:**  
👉 `Settings → Secrets and variables → Actions → Repository secrets`  

The GitHub Actions workflow automatically loads these variables at runtime to authenticate and provision AWS resources.

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
- Creates the DB Backup implementing a dynamic snapshot

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
GET /https://lrph5cswsc.execute-api.us-east-2.amazonaws.com/dev/postgresql-api-conn-path?table=crime_incidents
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
GET /https://lrph5cswsc.execute-api.us-east-2.amazonaws.com/dev/postgresql-api-conn-path?table=crime_summary
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

#### `PRECOMMIT.yml`
- Validate locally before committing:
```bash
pre-commit run --all-files --show-diff-on-failure
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