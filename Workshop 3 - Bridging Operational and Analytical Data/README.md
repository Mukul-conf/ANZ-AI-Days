# Confluent Tableflow Workshop [WIP]

This repository contains the necessary labs for the Confluent Tableflow workshop. You'll learn how to automatically materialize streaming Kafka data into analytics-ready Iceberg tables using Confluent Tableflow, without writing any ETL code.

During the workshop, you'll create a Confluent Cloud environment, configure AWS S3 storage, set up Glue Data Catalog integration, and query streaming data using Amazon Athena.

## General Requirements

* **Confluent Cloud Account** - Free tier available with $400 credits
* **AWS Account** - With permissions to create S3 buckets, IAM policies, and IAM roles
* **Git CLI** - To clone this repository

<details>
<summary>Installing Git on MAC</summary>

Install `git` by running:

```bash
brew install git
```

</details>

<details>
<summary>Installing Git on Windows</summary>

Install `git` by running:

```powershell
winget install --id Git.Git -e
```
</details> 

## Workshop Structure

This workshop consists of 3 hands-on labs:

### [Lab 0: Manual Confluent Cloud Setup](./tableflow-labs/lab0.md)
- Create Confluent Cloud account and environment
- Set up a Kafka cluster  
- Create topics with sample e-commerce data
- Explore the Confluent Cloud UI

### [Lab 1: Configure AWS and Enable Tableflow](./tableflow-labs/lab1.md)
- Set up AWS S3 bucket for Iceberg storage
- Configure IAM roles and policies
- Create Provider Integration between Confluent and AWS
- Enable Tableflow on Kafka topics

### [Lab 2: Integrate with AWS Glue Catalog and Query with Athena](./tableflow-labs/lab2.md)
- Configure AWS Glue Data Catalog integration
- Set up Catalog Integration in Confluent Cloud
- Query materialized Iceberg tables using Amazon Athena
- Explore analytics capabilities on streaming data

## Getting Started

1. **Clone the Repository:**
   ```bash
   git clone <repo_url>
   cd anz-tableflow-workshop
   ```

2. **Start with Lab 0:**
   Begin with [Lab 0](tableflow-labs/lab0.md) to set up your Confluent Cloud environment and create sample data.

3. **Follow the Lab Sequence:**
   Complete the labs in order (0 → 1 → 2) as each builds upon the previous one.

## What You'll Learn

- **Confluent Tableflow**: Automatic Kafka-to-Iceberg materialization
- **Cloud Integration**: Secure connection patterns between Confluent Cloud and AWS
- **Data Governance**: Schema Registry and data classification
- **Stream-to-Analytics Pipeline**: Real-time data to SQL analytics without ETL

**Result**: Live data becomes instantly queryable via standard SQL!

## Support

If you encounter issues during the workshop:
- Refer to [Confluent Cloud Documentation](https://docs.confluent.io/cloud/current/overview.html)
- Review [Confluent Tableflow Documentation](https://docs.confluent.io/cloud/current/topics/tableflow/overview.html)

---
