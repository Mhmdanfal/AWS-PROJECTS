# EventBridge rules — schedules & examples


This file documents the EventBridge rules used in this project and shows practical CLI and SAM examples so you can reproduce them reliably.


> IMPORTANT: EventBridge rules accept cron expressions in UTC. Convert your local timezone (IST) to UTC when creating rules. The cron expressions below are already converted from IST → UTC.


---


## Rules (summary)


1. **Start Lambda** — runs every day at **09:00 IST**
- UTC cron: `cron(30 3 * * ? *)` (03:30 UTC)
- Rule name suggestion: `ec2-auto-start-daily`


2. **Stop Lambda** — runs every day at **19:00 IST**
- UTC cron: `cron(30 13 * * ? *)` (13:30 UTC)
- Rule name suggestion: `ec2-auto-stop-daily`


3. **Billing Lambda** — runs every day at **20:00 IST**
- UTC cron: `cron(30 14 * * ? *)` (14:30 UTC)
- Rule name suggestion: `ec2-daily-billing-report`


---


## Create rule — AWS CLI examples


Replace `REGION`, `ACCOUNT_ID`, and `LAMBDA_ARN` placeholders.


### Create rule (Start Lambda)


```bash
aws events put-rule \
--name ec2-auto-start-daily \
--schedule-expression "cron(30 3 * * ? *)" \
--description "Start AutoManaged EC2 in
