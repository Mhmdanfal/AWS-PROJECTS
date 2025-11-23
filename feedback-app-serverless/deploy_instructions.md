# Deploy Instructions — Serverless Feedback App

In order to create the serverless feedback app these are the precise steps that should be considered

# Prerequisites
Create an AWS Account
Create an IAM user -- use a region which is close to you or a default region but do not change it , Cost for this project is very minimal unless you use it multiple times
Install the AWS CLI from the AWS website make sure it is updated , by writing in the terminal aws-- version
AWS account with Admin privileges (or equivalent permissions to create Lambda, API Gateway, DynamoDB, SNS, S3, IAM).
AWS CLI configured (aws configure) or use AWS Console. 

Python 3.12 + installed for local packaging (optional).

Your repo files in place: lambda/feedback_handler/app.py, lambda/feedback_handler/requirements.txt, and frontend/index.html.

## 2. Create DynamoDB table

Console (recommended):

Go to DynamoDB → Create table

Table name: FeedbackTable (or feedback)

Partition key: id (String)

Provisioned capacity: On-demand (recommended for small projects)

Press Create and wolah

## 3.Create SNS topic & subscription

Console:

Go to SNS → Topics → Create topic → Standard

Name: FeedbackNotifications


3. Create the Lambda function

We’ll create a Python Lambda that:

Reads JSON body (name, email, message)

Validates fields

Stores item in DynamoDB

Publishes SNS email

Step 3.1: Create Lambda

Go to Lambda → Create function

Author from scratch

Name: feedback_handler

Runtime: Python 3.12 (or 3.11 if 3.12 not available)

Architecture: x86_64

Execution role:

Choose “Create a new role with basic Lambda permissions”

Create function.

 # Step 3.2: Add environment variables

In Lambda → your function → Configuration → Environment variables:

Add:

TABLE_NAME = feedback (your DynamoDB table name)

SNS_TOPIC_ARN = arn:aws:sns:ap-south-1:...:feedback-notifications

Save.

# Step 3.3: Give Lambda permissions for DynamoDB + SNS

Go to Configuration → Permissions → Execution role → Open in IAM console

In IAM → this role → Add permissions → Attach policies

Attach these managed policies (for this project it’s fine, later you can tighten):

AmazonDynamoDBFullAccess (or better: AmazonDynamoDBReadWriteAccess)

AmazonSNSFullAccess

Save.

If you want tighter security later, we can write a custom inline policy, but for now just get it working.

# Step 3.4: Write the Lambda code

In Code tab, replace the default code with this:

import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

sns = boto3.client("sns")
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]


def build_response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # for browser
            "Access-Control-Allow-Methods": "OPTIONS,POST",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body_dict),
    }


def lambda_handler(event, context):
    # API Gateway HTTP API/REST API sends body as string
    try:
        body_str = event.get("body", "")
        if isinstance(body_str, str):
            data = json.loads(body_str or "{}")
        else:
            data = body_str or {}
    except json.JSONDecodeError:
        return build_response(400, {"error": "Invalid JSON"})

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return build_response(400, {"error": "name, email, and message are required"})

    item_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    item = {
        "id": item_id,
        "name": name,
        "email": email,
        "message": message,
        "created_at": created_at,
    }

    try:
        # store in DynamoDB
        table.put_item(Item=item)

        # send SNS notification
        sns_message = (
            f"New feedback received:\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Message: {message}\n"
            f"Time: {created_at}\n"
            f"ID: {item_id}"
        )

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="New Feedback Submission",
            Message=sns_message,
        )

        return build_response(200, {"status": "ok", "id": item_id})

    except ClientError as e:
        print(f"Error: {e}")
        return build_response(500, {"error": "Internal server error"})


Click Deploy.

 # Step 3.5: Test Lambda manually

Before dealing with API Gateway, we test Lambda directly.

Click Test.

Create a test event with this JSON:

{
  "body": "{\"name\": \"Test User\", \"email\": \"test@example.com\", \"message\": \"This is a test\"}"
}


Run Test.

Check:

Lambda logs (Monitor → Logs in CloudWatch) – no errors.

DynamoDB table → Explore table items → see if a new item is created.

Your email → you should get an SNS email.

If this part doesn’t work, do not move to Part 2. Fix it first.

PART 2 — API Gateway + S3 Form Frontend

Now that backend is working, you’ll:

Expose Lambda via API Gateway

Create a simple HTML form on S3 static website

Form → calls API via fetch() → user gets response → you get email + DynamoDB entry

# 4. Create API Gateway endpoint

You can use either REST API or HTTP API. I’ll give you REST API steps — slightly more verbose but good learning.

## Step 4.1: Create REST API

Go to API Gateway → APIs → Create API

Choose REST API → Build

API name: feedback-api

Endpoint type: Regional (default)

Create.

## Step 4.2: Create resource + POST method

In your new API, in Resources:

Click on / root → Actions → Create Resource

Resource name: feedback

Resource path: /feedback

Create Resource.

Click on /feedback → Actions → Create Method

Choose POST → tick checkmark.

For Integration type:

Integration type: Lambda Function

Check “Use Lambda Proxy integration”

Region: ap-south-1

Lambda Function: feedback_handler

Save → it will ask to give API Gateway permission to invoke Lambda → allow it.

## Step 4.3: Enable CORS for /feedback

Select /feedback resource.

Actions → Enable CORS

Allow:

POST

OPTIONS

Click “Enable CORS and replace existing CORS headers”.

Confirm the dialogs.

This allows your HTML page hosted on S3 to call the API.

## Step 4.4: Deploy the API

Actions → Deploy API

New stage: prod

Deploy.

You’ll get an Invoke URL like:

https://abc123.execute-api.ap-south-1.amazonaws.com/prod

Your full endpoint will be:

https://abc123.execute-api.ap-south-1.amazonaws.com/prod/feedback

Test it using Postman or curl (or VSCode REST client), or even the API Gateway console test:

Method: POST

URL: that full endpoint

Body (raw JSON):

{
  "name": "API Test",
  "email": "api@test.com",
  "message": "Testing via API Gateway"
}


If this works, you should again see DynamoDB entry + SNS email.

# 5. Create S3 static site with HTML form

Now we make a simple HTML form that calls the API.

## Step 5.1: Create S3 bucket for website

Go to S3 → Create bucket

Bucket name: feedback-form-anfal-123 (must be globally unique)

Region: ap-south-1

Uncheck “Block all public access” (because we want a public website).

Confirm the warning.

Create bucket.

Then:

Open bucket → Properties → Static website hosting

Enable → Host a static website.

Index document: index.html

Save.

Copy the Website endpoint URL (not the S3 URL). Something like:
http://feedback-form-anfal-123.s3-website-ap-south-1.amazonaws.com

## Step 5.2: Set bucket policy for public read

Go to Permissions → Bucket policy and paste something like:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::feedback-form-anfal-123/*"
    }
  ]
}


Change feedback-form-anfal-123 to your bucket name.

Save.

## Step 5.3: Create index.html with form + JS

Create a file called index.html on your local machine with this content:

<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Feedback Form</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; }
    label { display: block; margin-top: 12px; }
    input, textarea { width: 100%; padding: 8px; margin-top: 4px; }
    button { margin-top: 16px; padding: 10px 15px; cursor: pointer; }
    .msg { margin-top: 15px; }
  </style>
</head>
<body>
  <h1>Feedback</h1>
  <form id="feedbackForm">
    <label>Name
      <input type="text" name="name" required>
    </label>
    <label>Email
      <input type="email" name="email" required>
    </label>
    <label>Message
      <textarea name="message" rows="4" required></textarea>
    </label>
    <button type="submit">Submit</button>
  </form>
  <div class="msg" id="msg"></div>

  <script>
    const apiUrl = "https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/prod/feedback";

    const form = document.getElementById("feedbackForm");
    const msgDiv = document.getElementById("msg");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      msgDiv.textContent = "Submitting...";

      const formData = new FormData(form);
      const payload = {
        name: formData.get("name"),
        email: formData.get("email"),
        message: formData.get("message"),
      };

      try {
        const res = await fetch(apiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (!res.ok) {
          msgDiv.textContent = "Error: " + (data.error || "Unknown error");
        } else {
          msgDiv.textContent = "Thank you! Your feedback ID: " + data.id;
          form.reset();
        }
      } catch (err) {
        console.error(err);
        msgDiv.textContent = "Network error. Try again later.";
      }
    });
  </script>
</body>
</html>


IMPORTANT: Replace https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/prod/feedback with your actual API Gateway endpoint.

Upload index.html to your S3 bucket:

Go to bucket → Upload → add index.html → Upload.

Now open your S3 website endpoint in the browser and test the form.

You should see:

Success message on the page

New item in DynamoDB

Email from SNS

6. CloudWatch logs (for debugging & “showing off”)

For interviews and for your own sanity:

Lambda logs: CloudWatch → Logs → Log groups → /aws/lambda/feedback_handler

API Gateway logs: you can enable CloudWatch logs from Stages → prod → Logs/Tracing

This is where you see errors if something fails.

Open the topic → Create subscription:

Protocol: Email

Endpoint: your-email@example.com

Confirm the subscription from your inbox.
You’ll get a confirmation email → CONFIRM IT, otherwise SNS won’t send anything.

Copy the Topic ARN (looks like arn:aws:sns:ap-south-1:123456789012:feedback-notifications).
