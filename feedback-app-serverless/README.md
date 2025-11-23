
# Serverless Feedback App (AWS)

**Stack:** S3 (static website) → API Gateway → Lambda (Python) → DynamoDB → SNS → CloudWatch

## What it does
A static feedback form hosted on S3 that submits user input to API Gateway. The API triggers a Python Lambda which:
- validates input
- generates a UUID id
- stores the item in DynamoDB
- publishes a notification via SNS (email)
- logs execution to CloudWatch

## Architecture (high level)
1. User loads `index.html` from S3.
2. Browser POSTs JSON to `POST /feedback` on API Gateway.
3. API Gateway invokes the Lambda function (proxy integration).
4. Lambda writes item to DynamoDB and publishes an SNS message.
5. CloudWatch captures Lambda logs.

## Why I built it
- Demonstrates end-to-end serverless architecture and event-driven design.
- Shows practical experience with permissions (IAM), CORS, debugging, and deployment.
- Great interview talking point: design tradeoffs, IAM least-privilege, and deploy automation.


