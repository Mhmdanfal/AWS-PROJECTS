# EC2 Auto Start/Stop Scheduler + Daily Billing Reporter

In this project we Automated EC2 lifecycle management & AWS cost visibility using Lambda, EventBridge, SNS, IAM, and Cost Explorer.Which automatically starts The ec2 instances on a certain time and stops on the given time ,
and sends an email through SNS when the instance starts and stops and also generates a billing report each day and sends it via email

## Overview of the Project



This project automates day-to-day EC2 lifecycle management and provides clear visibility into daily AWS costs using a fully serverless architecture. It runs three scheduled tasks every day:

9:00 AM IST — Automatically start EC2 instances

7:00 PM IST — Automatically stop EC2 instances

8:00 PM IST — Generate and email a daily billing report

Only instances explicitly tagged with AutoManaged = true are included in the automation, ensuring complete control and zero accidental impact on other resources.

### AWS Services Used

AWS Lambda — Hosts the automation logic for starting, stopping, and reporting.

Amazon EventBridge — Triggers the Lambda functions on precise daily schedules.

Amazon SNS — Sends email notifications containing cost reports or any automation alerts.

AWS Cost Explorer API — Retrieves daily cost and usage data for reporting.

Amazon EC2 — The compute resources being automatically managed.

AWS IAM — Provides secure, least-privilege access for all Lambda functions.

Amazon CloudWatch Logs — Captures logs for monitoring, debugging, and audits.

IAM Roles and Policies

The project uses clearly separated IAM roles to ensure security and least-privilege access:

EC2 Start/Stop Role: Grants Lambda permission to discover, start, and stop only those EC2 instances tagged with `AutoManaged = true`, preventing unintentional actions on other systems.

Billing Report Role: Provides read-only access to AWS Cost Explorer, allowing the Lambda function to retrieve daily cost data and publish the report to an SNS topic.

Lambda Execution Permissions: Each function includes CloudWatch Logs permissions for log creation, streaming, and diagnostics. This ensures full visibility into the automation without over-permissive access.

This separation of duties keeps the system secure, maintainable, and aligned with AWS best practices.
IAM Roles and Policies

You will create two IAM roles:

1. Role for Start/Stop Lambdas (EC2AutoSchedulerRole)
Required Permissions (JSON)

Create an IAM role with this inline policy:
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "SNS_TOPIC_ARN"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

Replace SNS_TOPIC_ARN with your SNS topic ARN.

2. Role for Billing Lambda (EC2BillingReporterRole)
Required Permissions (JSON)
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ec2:DescribeInstances"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "SNS_TOPIC_ARN"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```
Lambda Functions

# Create 3 Lambda functions in the AWS Console:

Python 3.12
Attach the correct IAM roles
Add tags if needed

Copy/paste the code below

EC2 Start Function (Python)
File: start_lambda.py
```
import boto3
import json

SNS_TOPIC_ARN = "REPLACE_ME"  # SNS ARN

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

def lambda_handler(event, context):

    instances_to_start = []

    # Find AutoManaged=true instances
    reservations = ec2.describe_instances(
        Filters=[{
            'Name': 'tag:AutoManaged',
            'Values': ['true']
        }]
    )['Reservations']

    for r in reservations:
        for instance in r['Instances']:
            state = instance['State']['Name']
            if state in ["stopped", "stopping"]:
                instances_to_start.append(instance['InstanceId'])

    # Start instances
    if instances_to_start:
        ec2.start_instances(InstanceIds=instances_to_start)

    # Send SNS report
    message = f"EC2 Start Report:\nInstances started: {instances_to_start}"
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject="EC2 Start Report", Message=message)

    return {"status": "success", "started": instances_to_start}
```
EC2 Stop Function (Python)

File: stop_lambda.py
```
import boto3
import json

SNS_TOPIC_ARN = "REPLACE_ME"

ec2 = boto3.client('ec2')
sns = boto3.client('sns')

def lambda_handler(event, context):

    instances_to_stop = []

    reservations = ec2.describe_instances(
        Filters=[{
            'Name': 'tag:AutoManaged',
            'Values': ['true']
        }]
    )['Reservations']

    for r in reservations:
        for instance in r['Instances']:
            state = instance['State']['Name']
            if state == "running":
                instances_to_stop.append(instance['InstanceId'])

    if instances_to_stop:
        ec2.stop_instances(InstanceIds=instances_to_stop)

    message = f"EC2 Stop Report:\nInstances stopped: {instances_to_stop}"
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject="EC2 Stop Report", Message=message)

    return {"status": "success", "stopped": instances_to_stop}
```
Daily Billing Report Function (Python)

File: billing_lambda.py
```
import boto3
import datetime
import json

SNS_TOPIC_ARN = "REPLACE_ME"

ce = boto3.client('ce')
ec2 = boto3.client('ec2')
sns = boto3.client('sns')

def lambda_handler(event, context):

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    # Fetch AWS cost data
    cost = ce.get_cost_and_usage(
        TimePeriod={
            'Start': yesterday.strftime('%Y-%m-%d'),
            'End': today.strftime('%Y-%m-%d')
        },
        Metrics=['UnblendedCost'],
        Granularity='DAILY'
    )

    cost_amount = cost['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']

    # List running AutoManaged instances
    reservations = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:AutoManaged', 'Values': ['true']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    running_instances = [i['Instances'][0]['InstanceId'] for i in reservations['Reservations']]

    report = (
        "Daily AWS Billing Report\n"
        f"Date: {yesterday}\n"
        f"Cost: ${cost_amount}\n\n"
        f"Running AutoManaged Instances:\n{running_instances}"
    )

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="Daily AWS Billing Report",
        Message=report
    )

    return {"status": "success", "cost": cost_amount, "running": running_instances}
```
## EventBridge Scheduled Rules

EventBridge requires UTC, so convert IST → UTC.

Task	IST	UTC	Cron
Start: ` EC2	09:00	03:30	cron(30 3 * * ? *)`

Stop EC2:	`19:00	13:30	cron(30 13 * * ? *)`

Billing Report :	`20:00	14:30	cron(30 14 * * ? *)`

## SNS Setup for Daily Reports

Open SNS console → Topics
Create a Standard Topic

Name: EC2-notifications
Create subscription:
Protocol: Email
Endpoint: your email

Confirm the subscription from your inbox

# Screenshots 

<img width="1904" height="808" alt="Screenshot 2025-11-25 140603" src="https://github.com/user-attachments/assets/9cbaa370-0e5e-4188-bf8f-72b0f988098c" />
<img width="1908" height="853" alt="Screenshot 2025-11-25 141616" src="https://github.com/user-attachments/assets/20e5375d-24![EC2 Start](https://github.com/user-attachments/assets/3578204f-b353-4afd-b7c6-7d4a9d924338)
b9-4170-9549-02af9b343c05" />

# Email Screenshots
![EC2 Start](https://github.com/user-attachments/assets/41cd3399-afb7-4207-9bad-3b031168bc90)

![EC2 billing](https://github.com/user-attachments/assets/7bc4620a-c8e1-4a6d-8420-a05ae3ed168a)

Stop](https://github.com/user-attachments/assets/20b3b87a-3886-4177-af3d-c9bf2b9112a7)

 

