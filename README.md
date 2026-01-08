# AWS RDS/Aurora Start-Stop Routine

## Overview
This project provides an automated solution to implement a  **start and stop routine in all Amazon RDS and Aurora instances** in an AWS account using an **AWS Lambda function**, except those explicitly tagged with:

```
ALWAYSDOWN = yes
```

This helps reduce costs by stopping unused databases during off-hours while allowing exceptions for instances that should remain down.

---

## Architecture
- **AWS Lambda**: Executes the start/stop logic.
- **Amazon EventBridge (CloudWatch Events)**: Triggers the Lambda function on a schedule (e.g., start at 05:00, stop at 20:00).
- **AWS SDK (boto3)**: Interacts with RDS and Aurora instances, getting the instances status and tags, and executing the scheduler.
- **Tag Filtering**: Skips instances with `ALWAYSDOWN = yes`.

---

## Prerequisites
- AWS Account with permissions to manage RDS/Aurora, IAM Policies and Roles, Lambdas and EventBridge.
- Python 3.x runtime for Lambda.

---

## Deployment Steps
1. **Create the IAM Role**:
   In AWS console, create a IAM role with the custom policy in the file [Policy.json](Policy.json)
   

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create Lambda Function**:
   - Runtime: Python 3.x
   - Upload the code from `lambda_function.py`.

4. **Set Environment Variables** (optional):
   - `REGION`: AWS region to target.
   - `START_TIME` / `STOP_TIME`: For reference in logs.

5. **Configure EventBridge Rules**:
   - Create two rules:
     - **Start Rule**: Cron expression for start time.
     - **Stop Rule**: Cron expression for stop time.

---

## Configuration Details
- **Tag Filtering**:
  - Instances with `ALWAYSDOWN = yes` will be skipped.
- **Supported Engines**:
  - Amazon RDS (MySQL, PostgreSQL, etc.)
  - Amazon Aurora

---

## Usage Instructions
- To **start all instances**:
  - Lambda will call `rds.start_db_instance()` for each eligible instance.
- To **stop all instances**:
  - Lambda will call `rds.stop_db_instance()` for each eligible instance.

Logs are available in **CloudWatch Logs** for troubleshooting.

---

## Best Practices
- Test in a **non-production environment** first.
- Use **resource tagging** consistently.
- Implement **error handling** and **retry logic** in Lambda.
- Consider **notifications** (SNS) for success/failure alerts.

---

## License
MIT License

