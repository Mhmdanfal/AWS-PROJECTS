import json
import os
import uuid
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError


def build_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    # ---------------------------
    # 1️⃣ Parse + validate input
    # ---------------------------
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return build_response(400, {"error": "Invalid JSON"})

    name = body.get("name")
    email = body.get("email")
    message = body.get("message")

    if not name or not email or not message:
        return build_response(400, {"error": "Missing required fields"})

    # ---------------------------
    # 2️⃣ ONLY NOW touch AWS
    # ---------------------------
    dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION"))
    table = dynamodb.Table(os.environ["TABLE_NAME"])

    sns = boto3.client("sns", region_name=os.environ.get("AWS_REGION"))
    topic_arn = os.environ["SNS_TOPIC_ARN"]

    item_id = str(uuid.uuid4())

    table.put_item(
        Item={
            "id": item_id,
            "name": name,
            "email": email,
            "message": message,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    sns.publish(
        TopicArn=topic_arn,
        Subject="New Feedback",
        Message=message,
    )

    return build_response(200, {"id": item_id})
