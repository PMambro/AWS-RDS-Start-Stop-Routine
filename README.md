# AWS RDS/Aurora Start-Stop Routine

## Overview
This project provides an automated solution to implement a  **start and stop routine in all Amazon RDS and Aurora instances** in an AWS account using an **AWS Lambda function**, except those explicitly tagged with:

```
OffSchedule = 1
```

This helps reduce costs by stopping unused databases during off-hours while allowing exceptions for instances that should remain down.

---

## Architecture
- **AWS Lambda**: Executes the start/stop logic.
- **Amazon EventBridge (CloudWatch Events)**: Triggers the Lambda function on a schedule (e.g., start at 05:00, stop at 20:00).
- **AWS SDK (boto3)**: Interacts with RDS and Aurora instances, getting the instances status and tags, and executing the scheduler.
- **Tag Filtering**: Skips instances with `OffSchedule = 1`.

---

## Prerequisites
- AWS Account with permissions to manage RDS/Aurora, IAM Policies and Roles, Lambdas and EventBridge.
- Python 3.x runtime for Lambda.

---

## Deployment Steps
1. **Create the IAM Role**:
   In AWS console, create an IAM role with the custom policy in the file [Policy.json](Policy.json) 

2. **Create the Triggers**:
  We will create 2 event buses to use as time triggers for our Lambda:
  - In AWS console, go to **Amazon Event Bridge** > **Buses** > **Rules** > **Create Rule**
  - Desativate the **"Rule creation experience"** to facilitate
  - Step 1: Insert the name and description for your rule, and disable the rule on the selected events (Bottom of the page)
  - Step 2: 

3. **Create the Lambda Function**:
  - Select **"Author from Scratch"**
  - Create a name for your function
  - Runtime: select Pythonwith a 3.x
  - In **"Change default execution role"** select **"Use an existing role"** and choose the role you created o step 1
  - You can create it with all the other options can stay with the default settings
  - Once the function is created, paste the Python script from file [lambda-start-stop-1.1.py](lambda-start-stop-1.1.py) into the tab **"code"** > **lambda_function.py**


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

